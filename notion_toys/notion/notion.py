import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from functools import cache
from logging import Logger  # type hint
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .utils import (
    API_URL,
    DB_FILMARKS_KEY,
    DB_PROGRESS_KEY,
    FILMARKS_ID,
    FILMARKS_URL,
    HEADERS,
)


@cache
def _db_process_id(year: int) -> str:
    """映画進捗DBの該当年のページをNotionから取ってきてIDを返す"""

    prop_title = PropTitle(name="年", text=str(year))
    prop_year = PropDate(name="年初", date=date(year, 1, 1))

    # ページが存在するならそのIDを返す
    r = requests.post(
        urljoin(API_URL, f"databases/{DB_PROGRESS_KEY}/query"),
        headers=HEADERS,
        data=json.dumps(prop_year.to_filter("equals")),
    )
    if r.status_code == 200 and r.json()["results"] != []:
        return r.json()["results"][0]["id"].replace("-", "")

    # ページが存在しないなら作成してそのIDを返す
    r = requests.post(
        urljoin(API_URL, "pages"),
        headers=HEADERS,
        data=json.dumps(
            {
                "parent": {"database_id": DB_PROGRESS_KEY},
                "properties": {
                    **prop_title.payload,
                    **prop_year.payload,
                },
            }
        ),
    )
    r.raise_for_status()

    return r.json()["id"].replace("-", "")


@dataclass(frozen=True)
class Prop:
    name: str

    def to_payload(self):
        raise NotImplementedError


@dataclass(frozen=True)
class PropNumber(Prop):
    num: int | float

    def to_payload(self) -> dict:
        return {self.name: {"number": self.num}}


@dataclass(frozen=True)
class PropRichText(Prop):
    text: str

    def to_payload(self) -> dict:
        return {self.name: {"rich_text": [{"text": {"content": self.text}}]}}


@dataclass(frozen=True)
class PropTitle(PropRichText):
    key: str = "title"

    def to_payload(self) -> dict:
        return {self.name: {self.key: [{"text": {"content": self.text}}]}}


@dataclass(frozen=True)
class PropUrl(Prop):
    url: str

    def to_payload(self) -> dict:
        return {self.name: {"url": self.url}}

    def to_external_payload(self) -> dict:
        return {"external": {"url": self.url}}


@dataclass(frozen=True)
class PropDate(Prop):
    date: date | None

    def to_payload(self) -> dict:
        if not date:
            return {}
        return {self.name: {"date": {"start": self.date.isoformat()}}}

    def to_filter(self, condition: str) -> dict:
        if condition in (
            "equals",
            "before",
            "after",
            "on_or_before",
            "on_or_after",
        ):
            value = self.date.isoformat()

        elif condition in (
            "is_empty",
            "is_not_empty",
        ):
            value = True

        elif condition in (
            "past_week",
            "past_month",
            "past_year",
            "this_week",
            "next_week",
            "next_month",
            "next_year",
        ):
            value = {}

        else:
            raise ValueError

        return {"filter": {"property": self.name, "date": {condition: value}}}


@dataclass(frozen=True)
class PropMultiselect(Prop):
    items: tuple[str] = field(default_factory=tuple)

    def to_payload(self) -> dict:
        return {self.name: {"multi_select": [{"name": name} for name in self.items]}}


@dataclass(frozen=True)
class PropRelation(Prop):
    related_db_id: str

    def to_payload(self) -> dict:
        return {
            self.name: {
                "relation": [{"id": self.related_db_id}],
                "has_more": False,
            }
        }


@dataclass(frozen=True)
class MovieReviewPage:
    title: PropTitle
    score: PropNumber
    review: PropRichText
    movie_url: PropUrl
    img_url: PropUrl
    watch_date: PropDate
    release_year: PropNumber
    countries: PropMultiselect = field(hash=False)
    genres: PropMultiselect = field(hash=False)
    directors: PropMultiselect = field(hash=False)
    writers: PropMultiselect = field(hash=False)
    casts: PropMultiselect = field(hash=False)
    icon_url: PropUrl
    relation: PropRelation
    db_id: str

    def init(
        title: str,
        score: float,
        review: str,
        movie_url: str,
        img_url: str,
        watch_date: date,
        release_year: int,
        countries: tuple[str],
        genres: tuple[str],
        directors: tuple[str],
        writers: tuple[str],
        casts: tuple[str],
        db_id: str = DB_FILMARKS_KEY,
        related_db_id: str | None = None,
    ) -> dict:
        prop = {}
        prop["title"] = PropTitle(name="タイトル", text=title)
        prop["score"] = PropNumber(name="スコア", num=score)
        prop["review"] = PropRichText(name="感想", text=review)
        prop["movie_url"] = PropUrl(name="filmarks", url=movie_url)
        prop["img_url"] = PropUrl(name="画像", url=img_url)
        prop["watch_date"] = PropDate(name="鑑賞日", date=watch_date)
        prop["release_year"] = PropNumber(name="上映年", num=release_year)
        prop["countries"] = PropMultiselect(name="制作国", items=countries)
        prop["genres"] = PropMultiselect(name="ジャンル", items=genres)
        prop["directors"] = PropMultiselect(name="監督", items=directors)
        prop["writers"] = PropMultiselect(name="脚本", items=writers)
        prop["casts"] = PropMultiselect(name="出演者", items=casts)
        prop["db_id"] = db_id

        try:
            color = {0: "lightgray", 1: "lightgray", 2: "brown", 3: "yellow", 4: "orange", 5: "red"}[round(score)]
        except KeyError:
            color = "gray"
        prop["icon_url"] = PropUrl(name="アイコン", url=f"https://www.notion.so/icons/movie_{color}.svg")

        if related_db_id is None:
            related_db_id = _db_process_id(prop["watch_date"].date.year)
        prop["relation"] = PropRelation(name="集計", related_db_id=related_db_id)

        return prop

    def to_payload(self) -> dict:
        return {
            "parent": {"database_id": self.db_id},
            "icon": self.icon_url.to_external_payload(),
            "cover": self.img_url.to_external_payload(),
            "properties": {
                **self.title.to_payload(),
                **self.score.to_payload(),
                **self.review.to_payload(),
                **self.watch_date.to_payload(),
                **self.release_year.to_payload(),
                **self.countries.to_payload(),
                **self.genres.to_payload(),
                **self.directors.to_payload(),
                **self.writers.to_payload(),
                **self.casts.to_payload(),
                **self.movie_url.to_payload(),
                **self.img_url.to_payload(),
                **self.relation.to_payload(),
            },
        }


@dataclass
class NotionDB:
    id: str
    children: set = field(default_factory=set)

    def add(self, child: object):
        if not isinstance(child, MovieReviewPage):
            raise ValueError

        self.children.add(child)

    def has(self, page: object) -> bool:
        if not isinstance(page, MovieReviewPage):
            raise ValueError

        return page in self.children


@dataclass
class WebPage:
    url: str
    parser: str = "html.parser"


@dataclass
class FilmarksPage(WebPage):
    title: str = ""
    score: float = 0.0
    review: str = ""
    img_url: str = ""
    watch_date: date | None = None
    release_year: int | None = None
    countries: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    directors: list[str] = field(default_factory=list)
    writers: list[str] = field(default_factory=list)
    casts: list[str] = field(default_factory=list)

    def __post_init__(self):
        r = requests.get(self.url)
        r.raise_for_status()
        self.soup = BeautifulSoup(r.text, self.parser)
        self.parsed = False

    def parse(self) -> MovieReviewPage:
        if not self.parsed:
            # 映画のデータ
            detail = self.soup.find("div", class_="p-content-detail__body")
            other_info = list(detail.find("div", class_="p-content-detail__other-info").children)
            people_list_others = list(
                detail.find("div", class_="p-content-detail__people-list-others__wrapper").children
            )

            self.title = detail.find("h2", class_="p-content-detail__title").find("span").text
            self.img_url = detail.find("img")["src"]
            try:
                self.release_year = datetime.strptime(other_info[0].text, "上映日：%Y年%m月%d日").year
                self.countries = [country.text for country in other_info[2].find_all("a")]
            except ValueError:
                # https://filmarks.com/movies/55537 のように上映日情報がない映画もある
                self.release_year = int(detail.find("h2", class_="p-content-detail__title").find("a").text[:-1])
                self.countries = [country.text for country in other_info[1].find_all("a")]
            self.genres = [genre.text for genre in detail.find("div", class_="p-content-detail__genre").find_all("a")]
            self.directors = [person.text for person in people_list_others[0].find_all("a")]
            try:
                self.writers = [person.text for person in people_list_others[1].find_all("a")]
            except IndexError:
                # https://filmarks.com/movies/80435 のように脚本情報がない映画もある
                pass
            try:
                self.casts = [
                    cast.text for cast in detail.find("div", id="js-content-detail-people-cast").find_all("a")
                ]
            except AttributeError:
                # https://filmarks.com/movies/86613 のように出演者情報がない映画もある
                pass

            # レビューのデータ
            card_review = self.soup.find("div", class_="p-mark")

            ## 鑑賞日
            self.watch_date = datetime.strptime(card_review.find("time")["datetime"], "%Y-%m-%d %H:%M").date()
            ## スコア
            self.score = float(card_review.find("div", class_="c-rating__score").text)
            ## 感想
            self.review = card_review.find("div", class_="p-mark__review").text

            self.parsed = True

        return MovieReviewPage(
            **MovieReviewPage.init(
                title=self.title,
                score=self.score,
                review=self.review,
                movie_url=self.url,
                img_url=self.img_url,
                watch_date=self.watch_date,
                release_year=self.release_year,
                countries=self.countries,
                genres=self.genres,
                directors=self.directors,
                writers=self.writers,
                casts=self.casts,
            )
        )


def run(logger: Logger):
    # ------------------------------------------------------------------------------------------------------------
    # すでに記録してあるページをキャッシュする
    # ------------------------------------------------------------------------------------------------------------
    logger.info("Notionの映画ページをキャッシュします")
    db = NotionDB(id=DB_FILMARKS_KEY)

    pages = []
    payload = {"page_size": 100}  # Max
    while True:
        r = requests.post(
            urljoin(API_URL, f"databases/{DB_FILMARKS_KEY}/query"), headers=HEADERS, data=json.dumps(payload)
        )
        pages += r.json()["results"]

        if r.status_code != 200:
            break

        if r.json()["has_more"]:
            payload["start_cursor"] = r.json()["next_cursor"]
            continue

        break

    logger.debug(f"Notionの映画ページを{len(pages)}ページキャッシュしました")

    for page in pages:
        prop = {}
        prop["title"] = page["properties"]["タイトル"]["title"][0]["text"]["content"]
        prop["score"] = page["properties"]["スコア"]["number"]
        prop["review"] = page["properties"]["感想"]["rich_text"][0]["text"]["content"]
        prop["movie_url"] = page["properties"]["filmarks"]["url"]
        prop["img_url"] = page["properties"]["画像"]["url"]
        prop["watch_date"] = date.fromisoformat(page["properties"]["鑑賞日"]["date"]["start"])
        prop["release_year"] = page["properties"]["上映年"]["number"]
        prop["countries"] = [item["name"] for item in page["properties"]["制作国"]["multi_select"]]
        prop["genres"] = [item["name"] for item in page["properties"]["ジャンル"]["multi_select"]]
        prop["directors"] = [item["name"] for item in page["properties"]["監督"]["multi_select"]]
        prop["writers"] = [item["name"] for item in page["properties"]["脚本"]["multi_select"]]
        prop["casts"] = [item["name"] for item in page["properties"]["出演者"]["multi_select"]]
        prop["related_db_id"] = page["properties"]["集計"]["relation"][0]["id"].replace("-", "")
        prop["db_id"] = page["parent"]["database_id"].replace("-", "")

        prop = MovieReviewPage.init(**prop)
        db.add(MovieReviewPage(**prop))

    # ------------------------------------------------------------------------------------------------------------
    # ページ数
    # ------------------------------------------------------------------------------------------------------------
    logger.info("Filmarksのレビューがマイページ何ページ分かスクレイピングします")
    num_pages = 1
    res = requests.get(urljoin(FILMARKS_URL, f"/users/{FILMARKS_ID}"))
    soup = BeautifulSoup(res.text, "html.parser")
    pagination_last = soup.find("a", class_="c-pagination__last")["href"]
    result = re.match(f"/users/{FILMARKS_ID}\?page=(\d+)", pagination_last)
    if result:
        num_pages = int(result.group(1))
        logger.debug(f"Filmarksのレビューはマイページ{num_pages}ページ分です")

    # ------------------------------------------------------------------------------------------------------------
    # 全レビューを読み取る
    # ------------------------------------------------------------------------------------------------------------
    logger.info("Filmarksの全レビューをスクレイピングしてNotionページを作成します")
    for num in range(1, num_pages + 1):
        # ユーザーページnum番目
        r = requests.get(urljoin(FILMARKS_URL, f"/users/{FILMARKS_ID}?page={num}"))
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        for card_title in soup.find_all("h3", class_="c-content-card__title"):
            movie_path_query = card_title.find("a")["href"]
            fpage = FilmarksPage(url=urljoin(FILMARKS_URL, movie_path_query))

            try:
                page = fpage.parse()
                if db.has(page):
                    logger.debug(f"「{page.title.text}」は同期済みです")
                    continue
                logger.info(f"「{page.title.text}」をNotionに同期します")
                r = requests.post(urljoin(API_URL, "pages"), headers=HEADERS, data=json.dumps(page.to_payload()))
                r.raise_for_status()
                logger.info(f"「{page.title.text}」のNotionページを作成しました (id: {r.json()['id']})")

            except Exception as e:
                logger.error(e)
                continue

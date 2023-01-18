import json
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import cache
from urllib.parse import urljoin

import requests

from .utils import API_URL, DB_FILMARKS_KEY, DB_PROGRESS_KEY, HEADERS


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
class NotionMoviePage:
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

    @classmethod
    def init(
        cls,
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
        related_db_id: str | None = None,
        db_id: str = DB_FILMARKS_KEY,
    ):
        try:
            star_num = Decimal(str(score)).quantize(Decimal("0"), rounding=ROUND_HALF_UP)  # 正確に四捨五入
            color = {0: "lightgray", 1: "lightgray", 2: "brown", 3: "yellow", 4: "orange", 5: "red"}[star_num]
        except KeyError:
            color = "gray"

        if related_db_id is None:
            related_db_id = _db_process_id(watch_date.year)

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
        prop["icon_url"] = PropUrl(name="アイコン", url=f"https://www.notion.so/icons/movie_{color}.svg")
        prop["relation"] = PropRelation(name="集計", related_db_id=related_db_id)
        prop["db_id"] = db_id

        return cls(**prop)

    @classmethod
    def from_paylaod(cls, db_id: str, prop: dict):
        return cls.init(
            title=prop["タイトル"]["title"][0]["text"]["content"],
            score=prop["スコア"]["number"],
            review=prop["感想"]["rich_text"][0]["text"]["content"],
            movie_url=prop["filmarks"]["url"],
            img_url=prop["画像"]["url"],
            watch_date=date.fromisoformat(prop["鑑賞日"]["date"]["start"]),
            release_year=prop["上映年"]["number"],
            countries=tuple([item["name"] for item in prop["制作国"]["multi_select"]]),
            genres=tuple([item["name"] for item in prop["ジャンル"]["multi_select"]]),
            directors=tuple([item["name"] for item in prop["監督"]["multi_select"]]),
            writers=tuple([item["name"] for item in prop["脚本"]["multi_select"]]),
            casts=tuple([item["name"] for item in prop["出演者"]["multi_select"]]),
            related_db_id=prop["集計"]["relation"][0]["id"].replace("-", ""),
            db_id=db_id.replace("-", ""),
        )

    def _to_payload(self) -> dict:
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

    def create(self) -> str:
        url = urljoin(API_URL, "pages")
        r = requests.post(url, headers=HEADERS, data=json.dumps(self._to_payload()))
        r.raise_for_status()
        return r.json()["id"].replace("-", "")


@dataclass
class NotionDB:
    id: str
    children: set = field(default_factory=set)

    def add(self, child: object):
        if not isinstance(child, NotionMoviePage):
            raise ValueError

        self.children.add(child)

    def has(self, page: object) -> bool:
        if not isinstance(page, NotionMoviePage):
            raise ValueError

        return page in self.children

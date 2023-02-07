import re
from dataclasses import dataclass, field
from datetime import date, datetime
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

from .utils import FILMARKS_ID, FILMARKS_URL


@dataclass
class WebPage:
    url: str
    parser: str = "html.parser"
    soup: BeautifulSoup = field(init=False)

    def __post_init__(self) -> None:
        self.scrape()

    def scrape(self) -> None:
        r = requests.get(self.url)
        r.raise_for_status()
        self.soup = BeautifulSoup(r.text, self.parser)


@dataclass
class FilmarksMyPage(WebPage):
    url: str = urljoin(FILMARKS_URL, f"/users/{FILMARKS_ID}")
    num_pages: int = 1
    card_linked_urls: list = field(default_factory=list)

    def go_to(self, query: dict) -> None:
        self.url = urljoin(self.url, f"?{urlencode(query)}")
        self.scrape()

    def parse_num_pages(self) -> None:
        if not self.soup:
            self.scrape()

        pattern = re.compile(f"/users/{FILMARKS_ID}\?page=(\d+)")
        target = self.soup.find("a", class_="c-pagination__last")["href"]
        result = pattern.match(target)
        if result:
            self.num_pages = int(result.group(1))

    def parse_cards(self) -> None:
        if self.soup:
            self.scrape()

        card_title_divs = self.soup.find_all("h3", class_="c-content-card__title")
        for div in card_title_divs:
            self.card_linked_urls.append(urljoin(self.url, div.a["href"]))


@dataclass
class FilmarksMoviePage(WebPage):
    title: str = ""
    score: float = 0.0
    review: str = ""
    img_url: str = ""
    watch_date: date | None = None
    release_year: int | None = None
    countries: tuple[str] = field(default_factory=tuple)
    genres: tuple[str] = field(default_factory=tuple)
    directors: tuple[str] = field(default_factory=tuple)
    writers: tuple[str] = field(default_factory=tuple)
    casts: tuple[str] = field(default_factory=tuple)
    parsed: bool = False

    def parse(self) -> dict:
        if not self.soup:
            self.scrape()

        if not self.parsed:
            self._parse_movie_info()
            self._parse_review()

            self.parsed = True

        return {
            "title": self.title,
            "score": self.score,
            "review": self.review,
            "movie_url": self.url,
            "img_url": self.img_url,
            "watch_date": self.watch_date,
            "release_year": self.release_year,
            "countries": self.countries,
            "genres": self.genres,
            "directors": self.directors,
            "writers": self.writers,
            "casts": self.casts,
        }

    def _parse_movie_info(self) -> None:
        detail = self.soup.find("div", class_="p-content-detail__body")
        detail_other_info = detail.find("div", class_="p-content-detail__other-info")
        detail_people_list_others = tuple(
            detail.find("div", class_="p-content-detail__people-list-others__wrapper").children
        )

        # タイトル
        self.title = detail.find("h2", class_="p-content-detail__title").find("span").text
        # ポスターURL
        self.img_url = detail.find("img")["src"]
        # 制作年
        self.release_year = int(detail.find("h2", class_="p-content-detail__title").find("a").text[:-1])
        # 制作国
        self.countries = tuple([country.text for country in detail_other_info.find_all("a")])
        # ジャンル
        try:
            self.genres = tuple(
                [genre.text for genre in detail.find("div", class_="p-content-detail__genre").find_all("a")]
            )
        except AttributeError:
            # https://filmarks.com/movies/24302 のようにジャンル情報がない映画もある
            pass
        # 監督
        self.directors = tuple([person.text for person in detail_people_list_others[0].find_all("a")])
        # 脚本
        try:
            self.writers = tuple([person.text for person in detail_people_list_others[1].find_all("a")])
        except IndexError:
            # https://filmarks.com/movies/80435 のように脚本情報がない映画もある
            pass
        # 出演者
        try:
            self.casts = tuple(
                [cast.text for cast in detail.find("div", id="js-content-detail-people-cast").find_all("a")]
            )
        except AttributeError:
            # https://filmarks.com/movies/86613 のように出演者情報がない映画もある
            pass

    def _parse_review(self) -> None:
        card_review = self.soup.find("div", class_="p-mark")

        # 鑑賞日
        self.watch_date = datetime.strptime(card_review.find("time")["datetime"], "%Y-%m-%d %H:%M").date()
        # スコア
        self.score = float(card_review.find("div", class_="c-rating__score").text)
        # 感想
        review_div = card_review.find("div", class_="p-mark__review")
        if review_div.a and "続きを読む" in review_div.a.text:
            # レビュー内容が長すぎて「続きを読む」に丸めこまれている場合
            review_page = WebPage(url=urljoin(self.url, review_div.a["href"]))
            review_div = review_page.soup.find("div", class_="p-mark__review")
        for br in review_div.select("br"):
            br.replace_with("\n")
        self.review = review_div.text

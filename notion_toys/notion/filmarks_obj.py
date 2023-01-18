from dataclasses import dataclass, field
from datetime import date, datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass
class WebPage:
    url: str
    parser: str = "html.parser"

    def scrape(self) -> BeautifulSoup:
        r = requests.get(self.url)
        r.raise_for_status()
        return BeautifulSoup(r.text, self.parser)


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

    def __post_init__(self):
        r = requests.get(self.url)
        r.raise_for_status()
        self.soup = BeautifulSoup(r.text, self.parser)
        self.parsed = False

    def parse(self) -> dict:
        if not self.parsed:
            # 映画のデータ
            detail = self.soup.find("div", class_="p-content-detail__body")
            other_info = detail.find("div", class_="p-content-detail__other-info")
            people_list_others = tuple(
                detail.find("div", class_="p-content-detail__people-list-others__wrapper").children
            )

            self.title = detail.find("h2", class_="p-content-detail__title").find("span").text
            self.img_url = detail.find("img")["src"]
            self.release_year = int(detail.find("h2", class_="p-content-detail__title").find("a").text[:-1])
            self.countries = tuple([country.text for country in other_info.find_all("a")])
            self.genres = tuple(
                [genre.text for genre in detail.find("div", class_="p-content-detail__genre").find_all("a")]
            )
            self.directors = tuple([person.text for person in people_list_others[0].find_all("a")])
            try:
                self.writers = tuple([person.text for person in people_list_others[1].find_all("a")])
            except IndexError:
                # https://filmarks.com/movies/80435 のように脚本情報がない映画もある
                pass
            try:
                self.casts = tuple(
                    [cast.text for cast in detail.find("div", id="js-content-detail-people-cast").find_all("a")]
                )
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
            review_div = card_review.find("div", class_="p-mark__review")
            if review_div.a:
                # レビュー内容が長すぎて「続きを読む」に丸めこまれている場合
                review_page = WebPage(url=urljoin(self.url, review_div.a["href"]))
                review_div = review_page.scrape().find("div", class_="p-mark__review")
            for br in review_div.select("br"):
                br.replace_with("\n")
            self.review = review_div.text

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

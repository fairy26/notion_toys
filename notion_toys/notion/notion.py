import json
import re
from logging import Logger  # type hint
from urllib.parse import urljoin

import requests

from .filmarks_obj import FilmarksMoviePage, WebPage
from .notion_obj import NotionDB, NotionMoviePage
from .utils import (
    API_URL,
    DB_FILMARKS_KEY,
    FILMARKS_ID,
    FILMARKS_URL,
    HEADERS,
    NOTION_URL,
)


def run(logger: Logger):

    # Notionデータベースの情報を取ってくる
    db = NotionDB(id=DB_FILMARKS_KEY)

    movie_page_objs = []
    payload = {"page_size": 100}  # Max
    while True:
        r = requests.post(
            urljoin(API_URL, f"databases/{DB_FILMARKS_KEY}/query"), headers=HEADERS, data=json.dumps(payload)
        )
        r.raise_for_status()

        data = r.json()
        movie_page_objs += data["results"]
        if data["has_more"]:
            payload["start_cursor"] = data["next_cursor"]
            continue

        break

    for obj in movie_page_objs:
        db.add(
            NotionMoviePage.from_paylaod(
                id=obj["id"],
                db_id=obj["parent"]["database_id"],
                prop=obj["properties"],
            )
        )

    logger.debug(f"Notion読取完了 - {len(db.children)}ページ")

    # Filmarksのスクレイピング
    filmarks_mypage = WebPage(url=urljoin(FILMARKS_URL, f"/users/{FILMARKS_ID}"))
    soup = filmarks_mypage.scrape()

    # レビューがマイページ何ページにわたるかスクレイピング
    num_pages = 1
    result = re.match(
        pattern=f"/users/{FILMARKS_ID}\?page=(\d+)",
        string=soup.find("a", class_="c-pagination__last")["href"],
    )
    if result:
        num_pages = int(result.group(1))

    # 全レビューをNotionに
    for num in range(1, num_pages + 1):
        filmarks_mypage.url = urljoin(FILMARKS_URL, f"/users/{FILMARKS_ID}?page={num}")
        soup = filmarks_mypage.scrape()

        for card_title in soup.find_all("h3", class_="c-content-card__title"):
            fpage = FilmarksMoviePage(url=urljoin(FILMARKS_URL, card_title.find("a")["href"]))
            npage = NotionMoviePage.init(**fpage.parse())

            if not db.has(npage):
                try:  # レビューの新規作成
                    id = npage.create()
                    logger.info(f"同期成功 -「{npage.title.text}」を追加({urljoin(NOTION_URL, id)})")
                except Exception as e:
                    logger.error(f"同期失敗 - 「{npage.title.text}」の追加でエラーが起きました\n{e}\n{npage}")
                finally:
                    continue

            old_page = db.get_page(npage)

            if old_page is not None and npage != old_page:
                try:  # レビューの更新
                    id = old_page.update(npage)
                    logger.info(f"同期成功 -「{npage.title.text}」を更新({urljoin(NOTION_URL, id)})")
                except Exception as e:
                    logger.error(f"同期失敗 - 「{npage.title.text}」の更新でエラーが起きました\n{e}\n{npage}")
                finally:
                    continue

            logger.debug(f"変更なし -「{npage.title.text}」")

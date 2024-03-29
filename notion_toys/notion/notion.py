from logging import Logger  # type hint
from urllib.parse import urljoin

from .filmarks_obj import FilmarksMoviePage, FilmarksMyPage
from .notion_obj import NotionDB, NotionMoviePage
from .utils import DB_FILMARKS_KEY, NOTION_URL


def run(logger: Logger, parse_all: bool = False):
    # Notionデータベースの情報を取ってくる
    db = NotionDB(id=DB_FILMARKS_KEY)
    try:
        db.load_pages()
    except Exception as e:
        logger.error(f"Notionの読取失敗 - {e}")
        return
    logger.debug(f"Notion読取完了 - {len(db.children)}ページ")

    # Filmarksのスクレイピング
    try:
        f_mypage = FilmarksMyPage()
    except Exception as e:
        logger.error(f"Filmarksのマイページ読取失敗 - {e}")
        return
    if parse_all:
        f_mypage.parse_num_pages()

    # レビューをNotionに
    for num in range(1, f_mypage.num_pages + 1):
        f_mypage.go_to({"page": num})
        f_mypage.parse_cards()

    for url in f_mypage.card_linked_urls:
        try:
            fpage = FilmarksMoviePage(url=url)
        except Exception as e:
            logger.error(f"Filmarksの映画ページ({url})読取失敗 - {e}")
            continue
        npage = NotionMoviePage.init(**fpage.parse())

        if not db.has(npage):
            try:  # レビューの新規作成
                npage = db.add(npage.create())
                logger.info(f"同期成功 -「{npage.title.text}」を追加({urljoin(NOTION_URL, npage.id)})")
            except Exception as e:
                logger.error(f"同期失敗 - 「{npage.title.text}」の追加でエラーが起きました\n{e}\n{npage}")
            finally:
                continue

        old_page = db.get_page(npage)

        if old_page is not None and npage != old_page:
            try:  # レビューの更新
                npage = db.add(old_page.update(npage))
                logger.info(f"同期成功 -「{npage.title.text}」を更新({urljoin(NOTION_URL, npage.id)})")
            except Exception as e:
                logger.error(f"同期失敗 - 「{npage.title.text}」の更新でエラーが起きました\n{e}\n{npage}")
            finally:
                continue

        logger.debug(f"変更なし -「{npage.title.text}」")

    # Notionのページをキャッシュしておく
    if db.updated:
        db.serialize()

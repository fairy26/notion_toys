from datetime import datetime, timedelta
from importlib import resources

import yaml

_COFIGFILE = "notion_config.yaml"

with resources.files("docs").joinpath(_COFIGFILE).open() as f:
    conf = yaml.safe_load(f)

DB_PROGRESS_KEY = conf["notion"]["database"]["id"]["movie_progress"]
DB_FILMARKS_KEY = conf["notion"]["database"]["id"]["movie_filmarks"]

API_URL = conf["notion"]["api"]["url"]
HEADERS = {
    "Authorization": f"Bearer {conf['notion']['api']['integration']['token']['movie']}",
    "Notion-Version": conf["notion"]["api"]["version"],
    "Content-Type": "application/json",
}

NOTION_URL = conf["notion"]["url"]

FILMARKS_URL = conf["filmarks"]["url"]
FILMARKS_ID = conf["filmarks"]["id"]

_SERIALIZED_NOTION_PAGES_FILENAME = "notion_pages.pkl"
SERIALIZED_NOTION_PAGES_PATH = resources.files("notion_toys.data") / _SERIALIZED_NOTION_PAGES_FILENAME


def use_serialized_data(last_modified_limit_weeks: int = 1) -> bool:
    """Notionの映画DBの子ページをシリアライズされたpickleファイルから読み込むか

    Args:
        last_modified_limit_weeks (int, optional): シリアライズファイルが最新(n週間以内)かを判定する閾値. Defaults to 1.

    Returns:
        bool: if False; NotionAPIを叩いて読み込む
    """
    if not SERIALIZED_NOTION_PAGES_PATH.exists():
        return False
    # いつシリアライズされたか: pickleファイルがいつ更新されたか
    _last_modified_dt = datetime.fromtimestamp(SERIALIZED_NOTION_PAGES_PATH.stat().st_mtime)

    # データは最新か: シリアライズされたのは`last_modified_limit_weeks`週間以内か
    _last_modified_limit = datetime.now() - timedelta(weeks=last_modified_limit_weeks)

    return _last_modified_dt > _last_modified_limit

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

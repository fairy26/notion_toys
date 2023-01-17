from importlib import resources

import yaml

COFIGFILE = "notion_config.yaml"

with resources.path("docs", COFIGFILE) as notion_config:
    with open(notion_config, encoding="utf-8") as f:
        conf = yaml.safe_load(f)

DB_PROGRESS_KEY = conf["database"]["id"]["movie_progress"]
DB_FILMARKS_KEY = conf["database"]["id"]["movie_filmarks"]

API_URL = conf["api"]["url"]
HEADERS = {
    "Authorization": f"Bearer {conf['api']['integration']['token']['movie']}",
    "Notion-Version": conf["api"]["version"],
    "Content-Type": "application/json",
}

FILMARKS_URL = conf["filmarks"]["url"]
FILMARKS_ID = conf["filmarks"]["id"]

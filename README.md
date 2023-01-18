# TODO

-   [ ] レビューの更新機能を追加する
-   [ ] 映画以外の記録ページの機能を追加する

# 実行方法

モジュールで実行する

```bash
$ python -m notion_toys --filmarks
```

-   args
    -   `-f`, `--filmarks`: Filmarks をスクレイピングして Notion に同期する
    -   `-q`, `--quiet`: ログの出力を ERROR のみにする

VSCode の場合, `launch.json` を構成しているのでデバッグモードでも実行可能

##　初期設定

### Notion 上での設定

1.  integration を追加する

    [My integrations](https://www.notion.so/my-integrations) で新しい integration を追加する

    -   Name 以外デフォルトで OK
    -   Secrets/Internal Integration Token をメモする

2.  Notion の映画ページを作成し、配下のデータベースに作成した integration を追加する

    ページや DB のプロパティは[こちら](https://fairy26.notion.site/4f379a2ff814400288d4f6f01ca8fc11)を参考に（複製しても OK）

    ページ構成は以下の通り

        *   映画ページ
            *   目次・情報
            *   進捗
                *   映画進捗 DB
            *   一覧
                *   映画一覧 DB

    このうち（「映画ページ」）「映画進捗 DB」「映画一覧 DB」のそれぞれに integration を追加する

    -   (DB は右の Open as full page) > 右上の ... > Add connections > integration を選択

3.  データベースの ID をメモする

    DB を Open as full page した URL (`https://www.notion.so/{YOUR_NOTION_DOMAIN}/{DB_ID}?v={DB_VIEW_ID}`) の `DB_ID` の部分

### ドキュメントの追加

1.  `docs/notion_config.yaml`に以下の形式で記述する

    ```yaml
    notion:
        url: https://www.notion.so/

        api:
            url: https://api.notion.com/v1/
            version: '2022-06-28'
            integration:
                token:
                    movie: INTEGRATION_TOKEN
    database:
        id:
            movie_progress: DB_ID
            movie_filmarks: DB_ID

    filmarks:
        url: https://filmarks.com
        id: FILMARKS_ID
    ```

# メモ

-   `docs/samples/filmarks_scraping.ipynb` は初期に挙動を調査したノートブック

    流れは踏襲しつつも実際のコードとは大きく違うので注意

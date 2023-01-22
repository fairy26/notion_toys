# TODO

-   [ ] Filmarks の clip に対応する
-   [ ] 映画以外の記録ページの機能を追加する
-   [ ] 視聴可能な媒体のスクレイピング、記録機能を追加する

# 実行方法

パッケージ管理に Poetry を使っているので適宜インストールする - [Poetry Introduction](https://python-poetry.org/docs/)

```bash
$ git clone https://github.com/fairy26/notion_toys.git
$ cd notion_toys
$ poetry install --no-dev
```

実行時はモジュールで

```bash
$ poetry run python -m notion_toys --filmarks
```

-   args
    -   `-f`, `--filmarks`: Filmarks をスクレイピングして Notion に同期する
    -   `-a`, `--all`: 対象を Filmarks マイページの全ページにする（デフォルト: マイページの 1 ページ目のみ）
    -   `-q`, `--quiet`: ログの出力を ERROR 以上にする
    -   `-v`, `--verbose`: ログの出力を DEBUG 以上にする
    -   `--debug`: ログの出力をコンソールのみにする

VSCode の場合, `launch.json` を構成しているのでデバッグモードでも実行可能

## 初期設定

### Notion 上での設定

1.  integration を追加する

    [My integrations](https://www.notion.so/my-integrations) で新しい integration を追加する

    -   Name 以外デフォルトで OK
    -   Secrets > Internal Integration Token をメモする

2.  Notion の映画ページを作成し、配下のデータベースに作成した integration を追加する

    ページや DB のプロパティは[こちら](https://fairy26.notion.site/4f379a2ff814400288d4f6f01ca8fc11)を参考に（複製しても OK）

    ページ構成は以下の通り

        *   目次・情報
        *   進捗
            *   映画進捗 DB
        *   一覧
            *   映画一覧 DB

    このうち「映画進捗 DB」「映画一覧 DB」のそれぞれに integration を追加する

    -   DB 右の Open as full page > 右上の ... > Add connections > integration を選択

3.  データベースの ID をメモする

    DB を Open as full page した URL

    `https://www.notion.so/{YOUR_NOTION_DOMAIN}/{DB_ID}?v={DB_VIEW_ID}`

    の `DB_ID` の部分

### ドキュメントの追加

1.  メモしたシークレットキーらを `docs/notion_config.yaml` に記述する

    形式は以下の通り

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

# 注意事項

-   Filmarks のスクレイピングは[規約](https://filmarks.com/term)上問題ないと判断しているが、利用は自己責任で
-   アプリで登録したレビューのうち視聴方法や鑑賞日などの項目は Web で確認できないため自動登録不可

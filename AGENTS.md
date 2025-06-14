# AGENTS Instructions

このリポジトリでテストやビルドを実行するための環境構築手順を記載します。

## 開発環境のセットアップ
1. Python 3.12 を使用してください。pyenv などでインストールしておきます。
2. Poetry をインストールします。

```bash
pip install poetry
```

3. 依存パッケージをインストールします。

```bash
poetry install
```

4. DynamoDB Local を起動します。Docker が利用できる場合は以下のコマンドを実行してください。

```bash
docker-compose up -d
```

Docker が利用できない場合は、Java を利用してホスト上で DynamoDB Local を起動することも可能です。
以下のコマンドを順に実行してください。

```bash
curl -O https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
tar xzf dynamodb_local_latest.tar.gz
cd dynamodb_local
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
```

起動後は `http://localhost:8000` がエンドポイントとなります。

5. テストを実行して動作確認します。

```bash
poetry run pytest -v
```

以上の手順でローカル環境を準備できます。

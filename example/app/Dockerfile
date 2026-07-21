# ビルドコンテキストはリポジトリルート (example/docker-compose.yml 参照)
FROM python:3.12-slim

WORKDIR /opt/ddb_single

# ローカルの ddb_single をインストール (PyPI 版ではなく手元のコードを使う)
COPY pyproject.toml readme.md ./
COPY ddb_single ./ddb_single
RUN pip install --no-cache-dir .

WORKDIR /app
COPY example/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY example/app .

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

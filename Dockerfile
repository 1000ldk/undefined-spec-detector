# Dockerfile for Undefined Spec Detector

FROM python:3.11-slim

WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存パッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY README.md .
COPY setup.py .
COPY src/ ./src/
COPY web/ ./web/
COPY templates/ ./templates/
COPY examples/ ./examples/

# パッケージをインストール
RUN pip install -e .

# ポートを公開
EXPOSE 8000

# Webサーバーを起動
CMD ["uvicorn", "usd.web_api:app", "--host", "0.0.0.0", "--port", "8000"]


# 1. 使用官方輕量級 Python 映像檔
FROM python:3.11-slim

# 2. 設定工作目錄
WORKDIR /app

# 3. 先複製 requirements.txt 以利用 Docker layer cache
COPY requirements.txt .

# 4. 安裝依賴套件 (不使用快取以減小體積)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 複製剩餘的原始碼 (會排除 .dockerignore 表列檔案)
COPY . .

# 6. 設定環境變數 (Cloud Run 預設監聽 8080)
ENV PORT 8080

# 7. 啟動服務 (使用 uvicorn 執行 main.py 中的 app)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
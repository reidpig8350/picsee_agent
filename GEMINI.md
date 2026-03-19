我想要在GCP上面部署一個PicSee縮網址的助理。我希望是一個無伺服器的解決方案，我的同事可以透過URL呼叫這個助理並且對談。

希望同事能透過 URL 直接與其「對談」（Chat-like interface），使用 Cloud Run 部署一個輕量級的 Web 應用
1. 前端 (HTML/JS)：負責維護一個 list 變數來存對話。
2. 後端 (Cloud Run)：只當一個「純函數」，接收歷史紀錄、處理、回傳結果。


PICSEE_AGENT/
├── main.py            # FastAPI/Flask 主程式（包含網頁與 API 路由）
├── templates/         # 存放 HTML 檔案
│   └── index.html     # 對話介面
├── static/            # (選配) 存放 CSS 或 JS 檔案
├── Dockerfile         # 打包這整個資料夾
└── requirements.txt   # 依賴套件
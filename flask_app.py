# 這是 WSGI 檔案，負責啟動您的應用程式

import sys
# 將您的應用程式目錄加入系統路徑，以確保能找到 antigravity_webapp_1
# (這一步通常是 PythonAnywhere 自動處理的，但保險起見保留)
path = '/home/TIT65mate/mysite'
if path not in sys.path:
    sys.path.append(path)

# 💡 核心變更：從您的應用程式檔案中匯入 'app' 實例
# 您的程式碼已經被您重新命名為 antigravity_webapp_1.py
from antigravity_webapp_1 import app as application

# 注意：PythonAnywhere 要求應用實例變數必須命名為 'application'


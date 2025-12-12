# -*- coding: utf-8 -*-
import pandas as pd
import os
import subprocess
import datetime
import json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- 設定 (V3 基礎，包含內外部路徑判斷) ---

# 💡 判斷執行環境並設定 REPO_PATH
if os.getenv('IS_EXTERNAL_WEBAPP') == 'true':
    # 外部網頁環境 (PythonAnywhere)
    REPO_PATH = os.path.expanduser("~/mysite")
    print("Running in EXTERNAL WebApp mode. REPO_PATH:", REPO_PATH)
else:
    # 本機環境
    REPO_PATH = r"P:/tit65mate/mysite"
    print("Running in LOCAL mode. REPO_PATH:", REPO_PATH)

DATA_FILENAME = "lineinput.csv"
COMMIT_MESSAGE_PREFIX = "更新排程資料"
DAYS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
NAMES = ["陳貫裕", "吳伯聰", "簡尚祿", "周文樹", "徐滄興", "蕭金泉"]
# --- 設定結束 ---

# --- HTML Template (V4 功能整合: 日期、樣式、清除按鈕) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>互動排程表格 (Web App) - V4 Final</title>
    <style>
        /* 新增：用於日期的仿宋體樣式 */
        @font-face {
            font-family: 'FangSong';
            src: local('FangSong'), local('仿宋體');
        }
        .date-header {
            font-family: 'FangSong', sans-serif; /* 條件2：仿宋體 */
            font-size: 28px;
            font-weight: normal;
            color: black;
            margin-bottom: 5px;
        }

        /* Basic table styles */
        table {
            border-collapse: collapse;
            width: 100%;
            text-align: center;
            margin-bottom: 1em;
        }
        th, td {
            border: 1px solid #000;
            padding: 0;
            font-size: 16px;
            height: 35px;
        }
        body {
            font-family: sans-serif;
            margin: 20px;
        }
        th {
            background-color: #f2f2f2;
            padding: 10px;
        }
        .day-header {
            background-color: #f9f9f9;
            font-weight: bold;
            padding: 10px;
        }

        /* Styles for clickable cells */
        td.selectable {
            cursor: pointer;
            background-color: #ffffff;
            min-width: 50px;
            line-height: 35px;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            font-weight: bold;
            font-size: 18px;
        }
        td.selectable:hover {
            background-color: #eef;
        }
        td.selectable.is-o { color: green; }
        td.selectable.is-x { color: red; }
        td.selectable.is-blank { color: transparent; }

        /* Button Container and General Button Styles */
        .button-container {
            display: flex;
            justify-content: space-between; /* 將兩個按鈕分開 */
            margin-top: 15px;
            width: 100%;
        }
        button {
            padding: 10px 15px;
            font-size: 16px;
            cursor: pointer;
            border: none;
            border-radius: 4px;
            min-width: 150px;
        }

        /* 提交按鈕樣式 */
        #submitBtn {
            background-color: #4CAF50;
            color: white;
        }
        #submitBtn:hover { background-color: #45a049; }

        /* 條件1: 全部清除按鍵樣式 */
        #clearAllBtn {
            background-color: #FF0000; /* 鮮紅色 */
            color: white; /* 文字顏色不變 */
            font-weight: bold;
        }
        #clearAllBtn:hover { background-color: #CC0000; }

        #status-message {
            margin-top: 20px;
            padding: 10px;
            border-radius: 4px;
            display: none;
        }
        .success { background-color: #dff0d8; color: #3c763d; border: 1px solid #d6e9c6; }
        .error { background-color: #f2dede; color: #a94442; border: 1px solid #ebccd1; }
    </style>
</head>
<body>
    <div class="date-header">{{ current_date }}</div>

    <h1>互動排程表格 (Web App) - V4 Final</h1>
    <p>請直接點擊下方表格中的格子，即可輪流切換 "O" (綠色)、"X" (紅色) 或空白。</p>

    <div id="status-message"></div>

    <form id="scheduleForm">
        <table>
            <thead>
                <tr>
                    <th></th>
                    {% for name in names %}
                    <th>{{ name }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for day in days %}
                <tr>
                    <td class='day-header'>{{ day }}</td>
                    {% for name in names %}
                        {% set val = current_data.get(day, {}).get(   name, "") %}
                        {% if val == "O" %}
                            {% set cls = "selectable is-o" %}
                            {% set txt = "O" %}
                        {% elif val == "X" %}
                            {% set cls = "selectable is-x" %}
                            {% set txt = "X" %}
                        {% else %}
                            {% set cls = "selectable is-blank" %}
                            {% set txt = "&nbsp;"|safe %}
                        {% endif %}
                    <td class="{{ cls }}" data-day="{{ day }}" data-name="{{ name }}">{{ txt }}</td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="button-container">
            <button type="button" id="submitBtn" onclick="submitData()">提交資料並更新 GitHub</button>
            <button type="button" id="clearAllBtn" onclick="clearAllData()">全部清除</button>
        </div>
    </form>

    <script>
        // --- Click Handling ---
        document.querySelectorAll('td.selectable').forEach(cell => {
            cell.addEventListener('click', () => {
                const currentValue = cell.textContent.trim();
                if (currentValue === 'O') {
                    cell.textContent = 'X';
                    cell.className = 'selectable is-x';
                } else if (currentValue === 'X') {
                    cell.textContent = '\u00A0';
                    cell.className = 'selectable is-blank';
                } else {
                    cell.textContent = 'O';
                    cell.className = 'selectable is-o';
                }
            });
        });

        // --- 條件1: 新增 "全部清除" 邏輯 ---
        function clearAllData() {
            const cells = document.querySelectorAll('td.selectable');
            cells.forEach(cell => {
                const currentValue = cell.textContent.trim();
                // 檢查是否有 O 或 X 才進行清除動作
                if (currentValue === 'O' || currentValue === 'X') {
                    cell.textContent = '\u00A0'; // 設定為空白字元
                    cell.className = 'selectable is-blank'; // 設定為空白樣式
                }
            });

            // 顯示一個清除成功的訊息
            const statusDiv = document.getElementById('status-message');
            statusDiv.style.display = 'block';
            statusDiv.className = 'success';
            statusDiv.textContent = '✅ 已清除所有 O 和 X，請點擊「提交資料」以保存變更。';

            // 延遲後隱藏訊息
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }

        // --- Submit Data ---
        async function submitData() {
            const btn = document.getElementById('submitBtn');
            const statusDiv = document.getElementById('status-message');

            btn.disabled = true;
            btn.textContent = "處理中...";
            statusDiv.style.display = 'none';

            const data = {};
            const daysOrder = {{ days | tojson }};
            const namesOrder = {{ names | tojson }};

            daysOrder.forEach(day => {
                data[day] = {};
                namesOrder.forEach(name => {
                    data[day][name] = "";
                });
            });

            document.querySelectorAll('td.selectable').forEach(cell => {
                const day = cell.dataset.day;
                const name = cell.dataset.name;
                let value = cell.textContent.trim();
                if (value === '\u00A0' || value === '') {
                   value = "";
                }
                if (data[day] && data[day].hasOwnProperty(name)) {
                    data[day][name] = value;
                }
            });

            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                const result = await response.json();

                statusDiv.style.display = 'block';
                if (result.success) {
                    statusDiv.className = 'success';
                    statusDiv.textContent = '✅ ' + result.message;
                } else {
                    statusDiv.className = 'error';
                    statusDiv.textContent = '❌ ' + result.message;
                }
            } catch (error) {
                statusDiv.style.display = 'block';
                statusDiv.className = 'error';
                statusDiv.textContent = '❌ 發生網路錯誤: ' + error;
            } finally {
                btn.disabled = false;
                btn.textContent = "提交資料並更新 GitHub";
            }
        }
    </script>
</body>
</html>
"""

# --- Helper Functions (V3 穩定 Git 邏輯) ---

def load_data_from_csv(path, days, names):
    """讀取 CSV 資料"""
    if not os.path.exists(path):
        return {}
    try:
        df = pd.read_csv(path, index_col=0, encoding="utf-8-sig")
        df = df.reindex(index=days, columns=names).fillna("")
        return df.to_dict(orient="index")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return {}

def save_data_to_csv(data, path, days, names):
    """將資料存回 CSV"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df = pd.DataFrame.from_dict(data, orient="index")
        df = df.reindex(index=days, columns=names)
        df.fillna("", inplace=True)
        df.to_csv(path, encoding="utf-8-sig")
        return True, "資料已儲存至 CSV"
    except Exception as e:
        return False, f"儲存 CSV 失敗: {e}"

def git_run(args):
    """使用 os.chdir 執行 Git 指令 (V3 穩定版)"""
    if not os.path.isdir(REPO_PATH):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr=f"找不到儲存庫路徑 '{REPO_PATH}'", encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(REPO_PATH) # 強制切換到 Git 儲存庫目錄
        r = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        return r
    except Exception as e:
        return subprocess.CompletedProcess(args, 1, stdout="",
               stderr=f"Git 執行錯誤: {e}", encoding="utf-8")
    finally:
        os.chdir(original_cwd)

def git_pull():
    """執行 Git pull --rebase"""
    r = git_run(["pull", "--rebase"])
    # 檢查 returncode 是否為 0，或訊息中包含 "already up to date"
    if r.returncode != 0 and "already up to date" not in r.stdout.lower() and "無變更" not in r.stdout:
        return False, f"Git pull 失敗: {r.stderr.strip()}"
    return True, "資料已同步"

def git_push(filename, prefix):
    """執行 Git add, commit, push"""
    git_run(["add", filename])
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"{prefix} ({timestamp})"

    # Commit
    r = git_run(["commit", "-m", msg])
    if "nothing to commit" in r.stdout.lower() or "無變更需提交" in r.stdout:
        return True, "沒有偵測到檔案變更，無需提交"

    if r.returncode != 0:
        return False, f"Git commit 失敗: {r.stderr.strip()}"

    # Push
    p = git_run(["push"])
    if p.returncode != 0:
        return False, f"Git push 失敗: {p.stderr.strip()}"

    return True, "變更已成功推送至 GitHub"

# --- Flask Routes (V4: 整合日期顯示) ---

@app.route('/')
def index():
    # 條件2: 獲取當前年月份
    current_date_str = datetime.datetime.now().strftime("%Y 年 %m 月份")

    # 1. 先從 GitHub 拉取最新資料
    pull_success, pull_msg = git_pull()
    if not pull_success:
        print(f"Index Load: Git Pull Warning: {pull_msg}")

    # 2. 載入最新的 CSV 資料
    full_data_path = os.path.join(REPO_PATH, DATA_FILENAME)
    current_data = load_data_from_csv(full_data_path, DAYS, NAMES)

    return render_template_string(HTML_TEMPLATE,
                                  days=DAYS,
                                  names=NAMES,
                                  current_data=current_data,
                                  current_date=current_date_str) # 傳遞日期

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    full_data_path = os.path.join(REPO_PATH, DATA_FILENAME)

    # 0. 提交前再次拉取最新版本，避免衝突
    pull_success, pull_msg = git_pull()
    if not pull_success:
         print(f"Submit Warning: Git Pull failed before save: {pull_msg}")

    # 1. Save CSV
    save_ok, save_msg = save_data_to_csv(data, full_data_path, DAYS, NAMES)
    if not save_ok:
        return jsonify({"success": False, "message": save_msg})

    # 2. Push to GitHub
    push_ok, push_msg = git_push(DATA_FILENAME, COMMIT_MESSAGE_PREFIX)
    if not push_ok:
        return jsonify({"success": False, "message": push_msg})

    return jsonify({"success": True, "message": "更新成功！" + push_msg})

if __name__ == '__main__':
    # 只有在本機執行時才自動開啟瀏覽器，且不使用 reloader
    if os.getenv('IS_EXTERNAL_WEBAPP') != 'true':
        import webbrowser
        webbrowser.open("http://127.0.0.1:5000")
        app.run(debug=True, port=5000, use_reloader=False)
    else:
        # 外部伺服器 (如 PythonAnywhere) 忽略此區塊
        app.run(debug=False)
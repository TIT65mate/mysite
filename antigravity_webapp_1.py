# -*- coding: utf-8 -*-
import pandas as pd
import os
import subprocess
import datetime
import json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- 設定 ---
REPO_PATH = os.path.expanduser("~/mysite")
DATA_FILENAME = "lineinput.csv"
COMMIT_MESSAGE_PREFIX = "更新排程資料"
DAYS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
NAMES =["陳貫裕", "吳伯聰", "簡尚祿", "周文樹", "徐滄興", "蕭金泉"]
# --- 設定結束 ---

# --- HTML Template (保持不變) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>互動排程表格 (Web App)</title>
    <style>
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

        /* Button Styles */
        button {
            padding: 10px 15px; font-size: 16px; cursor: pointer;
            background-color: #4CAF50; color: white; border: none;
            border-radius: 4px; margin-top: 15px;
        }
        button:hover { background-color: #45a049; }
        button:disabled { background-color: #cccccc; cursor: not-allowed; }
        
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
    <h1>互動排程表格 (Web App)</h1>
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

        <button type="button" id="submitBtn" onclick="submitData()">提交資料並更新 GitHub</button>
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

        // --- Submit Data ---
        async function submitData() {
            const btn = document.getElementById('submitBtn');
            const statusDiv = document.getElementById('status-message');
            
            btn.disabled = true;
            btn.textContent = "處理中...";
            statusDiv.style.display = 'none';

            const data = {};
            // 從 Jinja2 傳入的變數，確保順序正確
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

# --- Helper Functions (新增/修改部分) ---

def load_data_from_csv(filepath, days_order, names_order):
    """Reads the CSV file and returns a dictionary matching the schedule structure."""
    if not os.path.exists(filepath):
        return {}
    try:
        df = pd.read_csv(filepath, index_col=0, encoding='utf-8-sig')
        # Ensure we only get the expected rows and columns, filling missing with empty string
        df = df.reindex(index=days_order, columns=names_order).fillna("")
        return df.to_dict(orient='index')
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return {}

def save_data_to_csv(data_dict, filepath, days_order, names_order):
    if not data_dict:
        return False, "沒有資料可儲存"
    try:
        # Ensure the directory exists before writing
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df = pd.DataFrame.from_dict(data_dict, orient='index')
        df = df.reindex(index=days_order, columns=names_order)
        df.fillna("", inplace=True)
        df.to_csv(filepath, encoding='utf-8-sig')
        return True, "資料已成功儲存至 CSV"
    except Exception as e:
        return False, f"儲存 CSV 失敗: {e}"

def git_pull_only(repo_path):
    """【新增】專門執行 Git pull 以同步 GitHub 上的最新資料"""
    if not os.path.isdir(repo_path):
        return False, f"找不到儲存庫路徑 '{repo_path}'"
    original_cwd = os.getcwd()
    try:
        os.chdir(repo_path)
        # Pull latest changes (rebase)
        # 使用 check=False, errors='replace' 來處理可能的非零返回碼和編碼問題
        pull_result = subprocess.run(["git", "pull", "--rebase"], capture_output=True, text=True, check=False, encoding='utf-8', errors='replace')
        
        # 檢查是否 pull 失敗 (除非只是說已經是最新版本)
        if pull_result.returncode != 0:
            stdout_lower = pull_result.stdout.lower()
            if "already up to date" in stdout_lower or "無變更" in stdout_lower or "已經是最新" in stdout_lower:
                return True, "已是最新版本"
            
            # 如果失敗，記錄錯誤訊息
            error_msg = pull_result.stderr.strip() or pull_result.stdout.strip()
            return False, f"Git pull 失敗: {error_msg}"
        
        return True, "資料已成功同步"
    except Exception as e:
        return False, f"Git pull 執行錯誤: {e}"
    finally:
        os.chdir(original_cwd)


def push_to_github(repo_path, filename, commit_message):
    """修改：在 push 前，先確保 pull 過最新版本，避免衝突"""
    if not os.path.isdir(repo_path):
        return False, f"找不到儲存庫路徑 '{repo_path}'"
    original_cwd = os.getcwd()
    try:
        os.chdir(repo_path)
        
        # 1. Add the file
        subprocess.run(["git", "add", filename], capture_output=True, text=True, check=False, encoding='utf-8', errors='replace')
        
        # 2. Commit with timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_commit_message = f"{commit_message} ({timestamp})"
        commit_result = subprocess.run(["git", "commit", "-m", full_commit_message], capture_output=True, text=True, check=False, encoding='utf-8', errors='replace')
        
        commit_succeeded = False
        if commit_result.returncode == 0:
            commit_succeeded = True
        elif "nothing to commit" in commit_result.stdout or "無變更需提交" in commit_result.stdout:
            return True, "沒有偵測到檔案變更，無需提交"
        else:
            return False, f"Git commit 失敗: {commit_result.stderr.strip()}"
        
        # 3. Push the commit
        if commit_succeeded:
            push_result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, check=False, encoding='utf-8', errors='replace')
            if push_result.returncode != 0:
                return False, f"Git push 失敗: {push_result.stderr.strip()}"
            return True, "變更已成功推送至 GitHub"
        return True, "提交未成功或無變更"
    except Exception as e:
        return False, f"Git 操作錯誤: {e}"
    finally:
        os.chdir(original_cwd)

# --- Flask Routes ---

@app.route('/')
def index():
    # 【核心改動】在顯示網頁前，先從 GitHub 拉取最新資料
    pull_success, pull_msg = git_pull_only(REPO_PATH)
    
    full_data_path = os.path.join(REPO_PATH, DATA_FILENAME)
    current_data = load_data_from_csv(full_data_path, DAYS, NAMES)
    
    # 您可以選擇將 pull 結果加入日誌或狀態，但在此處主要是為了同步資料
    print(f"Index Load: Git Pull Status: {pull_success}, Message: {pull_msg}")
    
    return render_template_string(HTML_TEMPLATE, days=DAYS, names=NAMES, current_data=current_data)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    full_data_path = os.path.join(REPO_PATH, DATA_FILENAME)
    
    # 0. 提交前再次拉取最新版本，避免儲存和提交時發生衝突
    pull_success, pull_msg = git_pull_only(REPO_PATH)
    if not pull_success:
         # 建議仍然繼續，因為資料已經被修改，但可提供警告
         print(f"Submit Warning: Git Pull failed before save: {pull_msg}")

    # 1. Save CSV
    success, msg = save_data_to_csv(data, full_data_path, DAYS, NAMES)
    if not success:
        return jsonify({"success": False, "message": msg})
    
    # 2. Push to GitHub
    success, msg = push_to_github(REPO_PATH, DATA_FILENAME, COMMIT_MESSAGE_PREFIX)
    if not success:
        return jsonify({"success": False, "message": msg})
        
    return jsonify({"success": True, "message": "更新成功！" + msg})

if __name__ == '__main__':
    # Automatically open browser
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
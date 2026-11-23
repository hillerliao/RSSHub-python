import warnings
# Suppress pkg_resources deprecation warning from Flask 2.0.2
warnings.filterwarnings("ignore", category=UserWarning, module="flask.cli")

import os
import socket

# 用量治理（2026-11-23）：给未显式带 timeout 的网络请求兜底，单次
# connect/read 最多等 8 秒，避免慢上游把函数拖满超时上限、白烧
# Function Duration（GB-Hrs）。与 utils.fetch_with_deadline 的 5 秒
# 截止互补：那条管总时长，这条管单次读写。
socket.setdefaulttimeout(8)

from dotenv import load_dotenv

# On Vercel the environment comes from project settings, so only read .env locally
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.environ.get('VERCEL') and os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from rsshub import create_app

# Use development config for local development
config_name = os.getenv('FLASK_CONFIG', 'development' if os.getenv('FLASK_ENV') == 'development' else 'production')
app = create_app(config_name) 

# Standard WSGI application for Vercel
application = app

# For local development
if __name__ == '__main__':
    app.run(debug=False, port=5000)  
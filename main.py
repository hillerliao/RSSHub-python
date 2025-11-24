import warnings
# Suppress pkg_resources deprecation warning from Flask 2.0.2
warnings.filterwarnings("ignore", category=UserWarning, module="flask.cli")

import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
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
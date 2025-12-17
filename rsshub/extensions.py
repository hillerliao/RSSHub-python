from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_caching import Cache
import os


bootstrap = Bootstrap()
moment = Moment()

# 仅在开发环境中导入和初始化 debugtoolbar
debugtoolbar = None
if os.environ.get('FLASK_ENV') == 'development':
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        debugtoolbar = DebugToolbarExtension()
    except ImportError:
        pass  # 开发环境缺失时忽略，避免阻断启动

cache = Cache(config={
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 3600  # cache half hour
})
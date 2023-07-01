from flask_bootstrap import Bootstrap
from flask_debugtoolbar import DebugToolbarExtension
from flask_moment import Moment
from flask_caching import Cache


bootstrap = Bootstrap()
debugtoolbar = DebugToolbarExtension()
moment = Moment()

cache = Cache(config={
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 3600  # cache half hour
})
import os
import sys


basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class BaseConfig:
    SITE_NAME = 'RSSHub'
    GITHUB_USERNAME = 'alphardex'
    EMAIL = '2582347430@qq.com'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'f43hrt53et53'
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class DevelopmentConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    TESTING = True


class ProductionConfig(BaseConfig):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

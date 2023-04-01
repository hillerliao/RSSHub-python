import os
from datetime import datetime
import click
from flask import Flask, render_template
from flask.cli import with_appcontext
from rsshub.config import config
from rsshub.extensions import *
from rsshub.blueprints.main import bp as main_bp
from rsshub.utils import XMLResponse
from rsshub.extensions import cache


def create_app(config_name=None):
    if config_name is None:
        # config_name = os.getenv('FLASK_CONFIG', 'development')
        config_name = os.getenv('FLASK_CONFIG', 'production')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.response_class = XMLResponse
    cache.init_app(app)

    # Add analytics
    from flask_analytics import Analytics
    from rsshub.google_analytics import ga_account

    Analytics(app)
    app.config['ANALYTICS']['GOOGLE_UNIVERSAL_ANALYTICS']['ACCOUNT'] = ga_account
    app.config['ANALYTICS']['ENABLED'] = True

    register_blueprints(app)
    register_extensions(app)
    register_errors(app)
    register_context_processors(app)
    register_cli(app)

    return app


def register_extensions(app):
    bootstrap.init_app(app)
    debugtoolbar.init_app(app)
    moment.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)


def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


def register_context_processors(app):
    @app.context_processor
    def inject_date_now():
        now = datetime.utcnow()
        return {'now': now}


def register_cli(app):
    @app.cli.command()
    @with_appcontext
    def ptshell():
        """Use ptpython as shell."""
        try:
            from ptpython.repl import embed
            if not app.config['TESTING']:
                embed(app.make_shell_context())
        except ImportError:
            click.echo('ptpython not installed! Use the default shell instead.')

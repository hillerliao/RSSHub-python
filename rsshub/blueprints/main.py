from flask import Blueprint, render_template, request

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('main/index.html')


@bp.route('/feeds')
def feeds():
    return render_template('main/feeds.html')


@bp.app_template_global()
def filter_content(ctx):
    include_title = request.args.get('include_title')
    include_description = request.args.get('include_description')
    exclude_title = request.args.get('exclude_title')
    exclude_description = request.args.get('exclude_description')
    limit = request.args.get('limit', type=int)
    items = ctx['items'].copy()
    items = [item for item in items if include_title in item['title']] if include_title else items
    items = [item for item in items if include_description in item['description']] if include_description else items
    items = [item for item in items if exclude_title not in item['title']] if exclude_title else items
    items = [item for item in items if exclude_description not in item['description']] if exclude_description else items
    items = items[:limit] if limit else items
    ctx = ctx.copy()
    ctx['items'] = items
    return ctx


#---------- feed路由从这里开始 -----------#
@bp.route('/chuansongme/articles/<string:category>')
@bp.route('/chuansongme/articles')
def chuansongme_articles(category=''):
    from rsshub.spiders.chuansongme.articles import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

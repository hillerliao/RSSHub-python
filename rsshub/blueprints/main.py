from flask import Blueprint, render_template, current_app, request


bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('main/index.html')


@bp.route('/feeds')
def feeds():
    feed_rules = [rule for rule in current_app.url_map._rules if 'main' in rule.endpoint][:-2]
    return render_template('main/feeds.html', rules=feed_rules)


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
@bp.route('/guokr/scentific')
def guokr_scientific():
    from rsshub.spiders.guokr.scientific import ctx
    return render_template('main/atom.xml', **filter_content(ctx))


@bp.route('/toutiao/today')
def toutiao_today():
    from rsshub.spiders.toutiao.today import ctx
    return render_template('main/atom.xml', **filter_content(ctx))

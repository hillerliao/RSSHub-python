from flask import Blueprint, render_template, request
from rsshub.extensions import cache

bp = Blueprint('main', __name__)

@bp.route('/word/<string:category>')
@bp.route('/')
@cache.cached(timeout=3600)
def word(category=''):
    from rsshub.spiders.word.word import ctx
    return render_template('main/word.html', **ctx(category))

@bp.route('/index')
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
    
    if include_title:
        include_keywords = include_title.split('|') if '|' in include_title else [include_title]
        items = [item for item in items if any(keyword in item['title'] for keyword in include_keywords)]
    
    if include_description:
        include_keywords = include_description.split('|') if '|' in include_description else [include_description]
        items = [item for item in items if any(keyword in item['description'] for keyword in include_keywords)]
    
    if exclude_title:
        exclude_keywords = exclude_title.split('|') if '|' in exclude_title else [exclude_title]
        items = [item for item in items if all(keyword not in item['title'] for keyword in exclude_keywords)]
    
    if exclude_description:
        exclude_keywords = exclude_description.split('|') if '|' in exclude_description else [exclude_description]
        items = [item for item in items if all(keyword not in item['description'] for keyword in exclude_keywords)]
    
    if limit:
        items = items[:limit]
    
    ctx = ctx.copy()
    ctx['items'] = items
    return ctx




#---------- feed路由从这里开始 -----------#
@bp.route('/cninfo/announcement/<string:stock_id>/<string:category>')
@bp.route('/cninfo/announcement')
def cninfo_announcement(stock_id='', category=''):
    from rsshub.spiders.cninfo.announcement import ctx
    return render_template('main/atom.xml', **filter_content(ctx(stock_id,category)))


@bp.route('/chuansongme/articles/<string:category>')
@bp.route('/chuansongme/articles')
def chuansongme_articles(category=''):
    from rsshub.spiders.chuansongme.articles import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))


@bp.route('/ctolib/topics/<string:category>')
@bp.route('/ctolib/topics')
def ctolib_topics(category=''):
    from rsshub.spiders.ctolib.topics import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/bbwc/realtime/<string:category>')
def bbwc_realtime(category=''):
    from rsshub.spiders.bbwc.realtime import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))


@bp.route('/infoq/recommend')
def infoq_recommend():
    from rsshub.spiders.infoq.recommend import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))


@bp.route('/infoq/topic/<int:category>')
def infoq_topic(category=''):
    from rsshub.spiders.infoq.topic import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/infoq/profile/<string:category>')
def infoq_profile(category=''):
    from rsshub.spiders.infoq.profile import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/infoq/search/<string:category>/<int:type>')
def infoq_search(category='', type=''):
    from rsshub.spiders.infoq.search import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category, type)))

@bp.route('/dxzg/notice')
def dxzg_notice():
    from rsshub.spiders.dxzg.notice import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))


@bp.route('/earningsdate/prnewswire')
def earningsdate_prnewswire():
    from rsshub.spiders.earningsdate.prnewswire import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))

@bp.route('/earningsdate/globenewswire')
def earningsdate_globenewswire():
    from rsshub.spiders.earningsdate.globenewswire import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))

@bp.route('/earningsdate/businesswire')
def earningsdate_businesswire():
    from rsshub.spiders.earningsdate.businesswire import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))

@bp.route('/jiemian/newsflash/<string:category>')
def jiemian_newsflash(category=''):
    from rsshub.spiders.jiemian.newsflash import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/csrc/audit/<string:category>')
def csrc_audit(category=''):
    from rsshub.spiders.csrc.audit import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/caixin/scroll/<string:category>')
def caixin_scroll(category=''):
    from rsshub.spiders.caixin.scroll import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/eastmoney/report/<string:type>/<string:category>')
def eastmoney_report(category='', type=''):
    from rsshub.spiders.eastmoney.report import ctx
    return render_template('main/atom.xml', **filter_content(ctx(type,category)))

@bp.route('/xuangubao/<string:type>/<string:category>')
def xuangubao_xuangubao(type='', category=''):
    from rsshub.spiders.xuangubao.xuangubao import ctx
    return render_template('main/atom.xml', **filter_content(ctx(type, category)))

@bp.route('/cls/subject/<string:category>')
def cls_subject(category=''):
    from rsshub.spiders.cls.subject import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/cls/telegraph/')
def cls_telegraph():
    from rsshub.spiders.cls.telegraph import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))

@bp.route('/chaindd/column/<string:category>')
def chaindd_column(category=''):
    from rsshub.spiders.chaindd.column import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/techcrunch/tag/<string:category>')
def techcrunch_tag(category=''):
    from rsshub.spiders.techcrunch.tag import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/weiyangx/home')
def weiyangx_home():
    from rsshub.spiders.weiyangx.home import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))

@bp.route('/weiyangx/express/')
def weiyangx_express():
    from rsshub.spiders.weiyangx.express import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))

@bp.route('/weiyangx/tag/<string:category>')
def weiyangx_tag(category=''):
    from rsshub.spiders.weiyangx.tag import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/jintiankansha/column/<string:category>')
def jintiankansha_column(category=''):
    from rsshub.spiders.jintiankansha.column import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/interotc/cpgg/<string:category>')
def interotc_cpgg(category=''):
    from rsshub.spiders.interotc.cpgg import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/benzinga/ratings/<string:category>')
def benzinga_ratings(category=''):
    from rsshub.spiders.benzinga.ratings import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/chouti/section/<string:category>')
def chouti_section(category=''):
    from rsshub.spiders.chouti.section import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/chouti/search/<string:category>')
def chouti_search(category=''):
    from rsshub.spiders.chouti.search import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/chouti/user/<string:category>')
def chouti_user(category=''):
    from rsshub.spiders.chouti.user import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/zaobao/realtime/<string:category>')
def zaobao_realtime(category=''):
    from rsshub.spiders.zaobao.realtime import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/mp/tag/<string:mp>/<string:tag>')
def mp_tag(mp='', tag=''):
    from rsshub.spiders.mp.tag import ctx
    return render_template('main/atom.xml', **filter_content(ctx(mp,tag)))

@bp.route('/mp/rtag/<string:c1>/<string:tag>')
def mp_rtag(c1='', tag=''):
    from rsshub.spiders.mp.rtag import ctx
    return render_template('main/atom.xml', **filter_content(ctx(c1, tag)))

@bp.route('/producthunt/search/<string:keyword>/<string:period>')
def producthunt_search(keyword='', period=''):
    from rsshub.spiders.producthunt.search import ctx
    return render_template('main/atom.xml', **filter_content(ctx(keyword,period)))

@bp.route('/pgyer/<string:category>')
def pgyer_app(category=''):
    from rsshub.spiders.pgyer.app import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/economist/worldbrief')
def economist_wordlbrief(category=''):
    from rsshub.spiders.economist.worldbrief import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/baidu/suggest/<string:category>')
def baidu_suggest(category=''):
    from rsshub.spiders.baidu.suggest import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/mp/gh/<string:gh>')
def mp_gh(gh=''):
    from rsshub.spiders.mp.gh import ctx
    return render_template('main/atom.xml', **filter_content(ctx(gh)))

@bp.route('/mp/youwuqiong/<string:author>')
def mp_youwuqiong(author=''):
    from rsshub.spiders.mp.youwuqiong import ctx
    return render_template('main/atom.xml', **filter_content(ctx(author)))


@bp.route('/xinhuanet/zuixinbobao')
def xinhuanet_zuixinbobao():
    from rsshub.spiders.xinhuanet.zuixinbobao import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))


@bp.route('/xinhuanet/shizhenglianbo')
def xinhuanet_shizhenglianbo():
    from rsshub.spiders.xinhuanet.shizhenglianbo import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))


@bp.route('/xinhuanet/yaodianjujiao')
def xinhuanet_yaodianjujiao():
    from rsshub.spiders.xinhuanet.yaodianjujiao import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))


@bp.route('/xinhuanet/world')
def xinhuanet_world():
    from rsshub.spiders.xinhuanet.world import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))


@bp.route('/yfchuhai/express/')
def yfchuhai_express():
    from rsshub.spiders.yfchuhai.express import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))

@bp.route('/bjnews/<string:category>')
def bjnews_channel(category=''):
    from rsshub.spiders.bjnews.channel import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/appstore/top/<string:cc>/<string:genreid>')
def appstore_top(cc='', genreid=''):
    from rsshub.spiders.appstore.top import ctx
    return render_template('main/atom.xml', **filter_content(ctx(cc,genreid)))

@bp.route('/netease/comment/<string:category>')
def netease_comment(category=''):
    from rsshub.spiders.netease.comment import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/aisixiang/search/<string:category>/<string:keywords>')
def aisixiang_search(category='', keywords=''):
    from rsshub.spiders.aisixiang.search import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category, keywords)))

@bp.route('/hnzcy/bidding/<string:type>')
@cache.cached(timeout=3600)
def hnzcy_bidding(type=''):
    from rsshub.spiders.hnzcy.bidding import ctx
    return render_template('main/atom.xml', **filter_content(ctx(type)))

@bp.route('/sysu/ifcen')
@cache.cached(timeout=3600)
def sysu_ifcen(category='', keywords=''):
    from rsshub.spiders.sysu.ifcen import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/nhk/newseasy')
@cache.cached(timeout=3600)
def nhk_newseasy(category='', keywords=''):
    from rsshub.spiders.nhk.newseasy import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/nhk/topic/<string:category>')
@cache.cached(timeout=3600)
def nhk_topic(category='', keywords=''):
    from rsshub.spiders.nhk.topic import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/tadoku/books/<string:category>')
@cache.cached(timeout=3600)
def tadoku_books(category=''):
    from rsshub.spiders.tadoku.books import ctx
    return render_template('main/atom.xml', **filter_content(ctx(category)))

@bp.route('/filter/')
def rss_filter():
    from rsshub.spiders.rssfilter.filter import ctx
    feed_url = request.args.get("feed")
    return render_template('main/atom.xml', **filter_content(ctx(feed_url)))
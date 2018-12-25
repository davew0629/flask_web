from flask import render_template, current_app, session, request, jsonify

from info import redis_store, constants
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import index_blu


@index_blu.route('/news_list')
def news_list():
    # 获取首页新闻数据
    cid = request.args.get("cid", "1")
    page = request.args.get("page", "1")
    per_page = request.args.get("perpage", "10")

    print(cid, page, per_page)
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数")

    filters = []
    # 如果查询的不是最新的数据 需要添加条件
    if cid != 1:
        filters.append(News.category_id == cid)

    # 查询数据，按照过滤器规则，时间顺序降序，分页查询
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    # news_list 是模型对象列表
    news_list_model = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    # print(total_page, current_page, news_list_model)
    # new_dict_li 是字典列表
    news_dict_li = []
    for news in news_list_model:
        news_dict_li.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_dict_li": news_dict_li
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@index_blu.route('/')
@user_login_data
def index():
    # session['name'] = 'itcast'

    # logging.debug('test for debug 999')
    # logging.warning('test for debug 888')
    # logging.error('test for debug 777')
    # logging.fatal('test for debug 666')
    # current_app.logger.error("test eeror  hghjgjh")

    # return render()
    # return render_to_response()
    # redis_store.set("name", "itcast")  # 在redis中保存一个值 name itcast
    # return 'index page 666'

    # 查询分类数据 并通过模板渲染
    categories = Category.query.all()
    category_li = []
    for category in categories:
        category_li.append(category.to_dict())

    # 如果用户已经登录，将当前登录用户的数据传到模板中显示

    user_id = session.get('user_id', None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # 显示右侧新闻排行
    news_list = []
    print("准备获取新闻排行数据")
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_basic_dict())
    print(len(news_dict_li))

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li,
        "category_li": category_li
    }

    return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
from flask import render_template, session, current_app, abort, g, jsonify, request
from info import constants, db
from info.models import User, News, Comment, CommentLike
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blu


@news_blu.route('/followed_user', methods=["POST"])
@user_login_data
def followed_user():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="未登录")

    user_id = request.json.get("user_id")
    action = request.json.get("action")

    # 判断参数
    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 获取要被关注的用户
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not other:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    # 根据要执行的操作去修改对应的数据
    if action == "follow":
        if other not in user.followed:
            # 当前用户的关注列表添加一个值
            user.followed.append(other)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前用户已被关注")
    else:
        # 取消关注
        if other in user.followed:
            user.followed.remove(other)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前用户未被关注")

    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route('/comment_like', methods=["POST"])
@user_login_data
def comment_like():
    """
    评论点赞
    :return:
    """
    print("准备调用comment_like方法")
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 1. 取到请求参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    # 2. 判断参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 获取到要被点赞的评论模型
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    if action == "add":
        # 添加评论
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment.id).first()
        if not comment_like_model:
            # 点赞评论
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment.id
            db.session.add(comment_like_model)
            comment.like_count += 1
    else:
        # 取消点赞评论
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment.id).first()
        if comment_like_model:
            db.session.delete(comment_like_model)
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")

    print("comment_like方法完毕")
    return jsonify(errno=RET.OK, errmsg="OK")


@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def comment_news():
    """评论新闻或者回复某条新闻下指定的评论"""
    print("准备调用comment_news方法")
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")
    news_id = request.json.get("news_id")
    print(news_id)
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    print(news_id, parent_id)
    # 2 判断参数
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        print("flag here")
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据错误")

    comment = Comment()  # 初始化一个评论模型并赋
    comment.user_id = user.id
    comment.content = comment_content
    comment.news_id = news_id
    print(comment)
    if parent_id:
        comment.parent_id = parent_id
    # 添加到数据库,return 的时候需要使用到comment的id
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())


@news_blu.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):

    # 定义变量作为是否收藏的标记
    is_collected = False

    is_followed = False

    # 查询用户登陆信息
    # user = query_user_data()
    user = g.user
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_basic_dict())

    # 查询新闻数据，通过news_id
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not news:
        # 返回404页面
        abort(404)

    # 更新新闻的点击次数
    news.clicks += 1

    if user:
        # sqlalchemy会在使用的时候自动加载
        if news in user.collection_news:
            is_collected = True

    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    comment_like_ids = []
    if user:
        try:
            # 需求：查询当前用户在当前新闻里面都点赞了哪些评论
            # 1. 查询出当前新闻的所有评论 ([COMMENT]) 取到所有的评论id  [1, 2, 3, 4, 5]
            comment_ids = [comment.id for comment in comments]
            # 2. 再查询当前评论中哪些评论被当前用户所点赞 （[CommentLike]）查询comment_id 在第1步的评论id列表内的所有数据 & CommentList.user_id = g.user.id
            comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                     CommentLike.user_id == g.user.id).all()
            # 3. 取到所有被点赞的评论id 第2步查询出来是一个 [CommentLike] --> [3, 5]
            comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]  # [3, 5]
        except Exception as e:
            current_app.logger.error(e)

    comment_dict_li = []
    for comment in comments:
        comment_dict = comment.to_dict()
        # comment_dict["is_like"] = False
        # if comment.id in comment_like_ids:
        #     comment_dict["is_like"] = True
        comment_dict_li.append(comment_dict)

    # 如果当前新闻有作者，并且当前登录用户已关注过这个用户
    if news.user and user:
        if news.user in user.followed:
            is_followed = True

    data = {
        "news": news.to_dict(),
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li,
        "is_collected": is_collected,
        "comments": comment_dict_li,
        "is_followed": is_followed
    }

    return render_template("news/detail.html", data=data)


@news_blu.route("/news_collect", methods=['POST'])
@user_login_data
def collect_news():
    print("准备调用collect_news收藏方法")
    user = g.user
    if not user:
        # 用户不是登录状态
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")

    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    if action not in ["collect","cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误，事件不在列表")

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误，news_id错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据库查询news错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到news数据")

    if action == "cancel_collect":
        #
        if news in user.collection_news:
            user.collection_news.remove(news)
    else:
        if news not in user.collection_news:
            user.collection_news.append(news)

    print("操作成功")
    return jsonify(errno=RET.OK, errmsg="收藏操作成功！")

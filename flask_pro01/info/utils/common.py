# 共用的自定义工具类
import functools

from flask import session, current_app, g

from info.models import User


def do_index_class(index):
    # 返回指定索引对应的类名
    if index == 1:
        return "first"
    elif index == 2:
        return "second"
    elif index == 3:
        return "third"
    else:
        return ""


def user_login_data(f):
    @functools.wraps(f)
    # 使用该工具可以在装饰过程中保持被装饰函数的__name__属性不变
    # 原因：在同一模块下被装饰器函数装饰的函数会被赋予相同的装饰器名字wrapper
    def warrper(*args, **kwargs):
        user_id = session.get("user_id", None)
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user
        return f(*args, **kwargs)
    return warrper

# 不使用装饰器的方法
# def query_user_data():
#     user_id = session.get("user_id", None)
#     user = None
#     if user_id:
#         try:
#             user = User.query.get(user_id)
#         except Exception as e:
#             current_app.logger.error(e)
#         return user
#     return None

from logging.handlers import RotatingFileHandler
from flask import Flask, g, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis
from flask_wtf import CSRFProtect
from config import config
import logging
import pymysql
pymysql.install_as_MySQLdb()

# 原来指定session的存储位置(数据库类型)
from flask_session import Session


# flask扩展中可以先初始化扩展的对象，再去调用init——app方法初始化
db = SQLAlchemy()

redis_store = None  # type:StrictRedis
# redis_store:StrictRedis = None python3.5 do not support annotations


def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 类似与工厂方法
def create_app(config_name):
    # 创建app对象之前开启日志,传入配置名
    setup_log(config_name)

    app = Flask(__name__)

    app.config.from_object(config["default"])

    # db = SQLAlchemy(app)

    db.init_app(app)

    # 初始化redis存储对象
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT, decode_responses=True)

    # 开启当前项目CSRF保护,只做服务器验证
    # 从cookies中去除随机值 从表单中去除随机值，然后进行校验并且响应校验结果
    # 表单中随机添加token
    CSRFProtect(app)
    # 设置session保存指定位置
    Session(app)

    #
    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class, "index_class")

    from info.utils.common import user_login_data

    @app.errorhandler(404)
    @user_login_data
    def page_not_found(e):
        user = g.user
        data = {"user": user.to_dict() if user else None}
        return render_template('news/404.html', data=data)

    @app.after_request
    def after_request(response):
        # print("调用方法生成csrf_token")
        csrf_token = generate_csrf()
        # print(csrf_token)
        response.set_cookie("csrf_token", csrf_token)
        return response

    # 注册蓝图
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    from info.modules.news import news_blu
    app.register_blueprint(news_blu)
    from info.modules.profile import profile_blu
    app.register_blueprint(profile_blu)
    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu, url_prefix="/admin")

    return app

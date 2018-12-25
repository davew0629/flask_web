from redis import StrictRedis

import os
import logging
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # 项目的配置
    # DEBUG = True

    SECRET_KEY = 'afLWSqolE06SiU0a2skKntN3q1LZBWcxVQdN2kv+6W3OazEpu8tnwk0WALKFJDir'
    # 为数据库添加配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/information27"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 请求结束后自动执行一次db.session.commit操作
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # redis 配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    SESSION_TYPE = "redis"
    # 开启session签名
    SESSION_USE_SIGNER = True
    # 指定session保存的redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 设置需要过期
    SESSION_PERMANENT = False
    # 设置过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 2

    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


# 定义配置字典
class DevelopmentConfig(Config):
    # 开发环境
    DEBUG = True
    # MAIL_SERVER = 'smtp.googlemail.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    #                           'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    # 测试环境
    DEBUG = False
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
    #                       'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    # 生产环境
    DEBUG = False
    LOG_LEVEL = logging.WARNING
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #                       'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

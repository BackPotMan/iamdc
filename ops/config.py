# -*- coding: utf-8 -*-
import os

class Config(object):

    DEBUG = False
    # 是否是开发模式
    DEV = False

    SECRET_KEY = '\x9bl\xbc\xc6\x01\xaf^\r\x13\xb2\xb2T\xce\x87d\xd1\xf5\x07\xb6r\x8c\r\xe8\x93'

    #数据库iamdcdb
    SQLALCHEMY_DATABASE_URI = 'mysql://deployer:A637f37955dbfcE1@192.168.1.18:3306/iamdcdb?charset=utf8'

    # 日志文件
    LOG_FILE = "ops.log"

class DevConfig(Config):

    DEBUG = True
    # 开发模式
    DEV = True

    # 数据库iamdcdb
    SQLALCHEMY_DATABASE_URI = 'mysql://opser:123456@localhost:3306/iamdcdb?charset=utf8'

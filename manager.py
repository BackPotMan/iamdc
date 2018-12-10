# -*- coding: utf-8 -*-

from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager,Shell
from ops.database.model import db
from run import app

"""
migrate使用方法:
第一次使用  python manager.py db init

后面每次有表修改执行下面两句进行修改
python manager.py db migrate
python manager.py db upgrade

"""

manager = Manager(app)
migrate = Migrate(app, db)  #注册migrate到flask
manager.add_command('db', MigrateCommand)  #在终端环境下添加一个db命令


if __name__ == '__main__':
    manager.run()

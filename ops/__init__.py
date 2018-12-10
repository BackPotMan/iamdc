# -*- coding: utf-8 -*-
from flask import Flask,request,render_template,url_for,redirect,abort,session
from jinja2 import TemplateNotFound
from ops.database.model import db,user
from ops.users.login import userLogin
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)

# 加载配置文件
app.config.from_object('ops.config.DevConfig')

# #初始化models
db.init_app(app)
db.app = app
db.create_all()

# 导入蓝图
modules = [
    ('ops.users.api', 'userBlue', '/users'),         # 用户管理模块
#    ('ops.assets.api', 'assetsBlue', '/assets'),    # 资源管理模块
#    ('ops.deploy.api', 'deployBlue', '/deploy'),    # 发布系统模块
    ('ops.case.api', 'caseBlue', '/case'),          # 工单系统模块
#    ('ops.setting.api', 'settingBlue', '/setting'), # 后台设置模块
#    ('ops.monitor.api', 'monitorBlue', '/monitor'), # 监控系统模块
]
for md, blp, prefix in modules:
    app.register_blueprint(getattr(__import__(md, fromlist=[blp]), blp), url_prefix=prefix)


@app.route('/')
def index():

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    try:
        return render_template('index.html',userInfo=loginData['user'])
    except TemplateNotFound:
        abort(404)


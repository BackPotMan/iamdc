# -*- coding: utf-8 -*-
import datetime
from flask_sqlalchemy import SQLAlchemy
from custom_type import ChoiceType,ChoiceTypeInteger
import werkzeug
"""
注意：
1、表名称以全部小写字母
2、字段名称全部小写字母，尽量使用下划线隔开每个单词，如 目标ip: target_ip
3、一对多关系中 db.relationship() 不需要使用 backref='xxx'
"""

db = SQLAlchemy()

class department(db.Model):
    """
    部门表
    """
    #__tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 部门名称
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    # 英文名称
    enname = db.Column(db.String(255), nullable=False, unique=True, index=True)
    # 父节点
    parent = db.Column(db.Integer,nullable=True,default=0)
    # 创建时间
    ctime = db.Column(db.DateTime, default=datetime.datetime.now)
    # 修改时间
    mtime = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __unicode__(self):
        return u"%s" % self.name

class user(db.Model):
    """
    用户表
    """
    #__tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 用户名
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    # 中文名称
    cnname = db.Column(db.String(255), nullable=False)
    # 密码，不允许在数据库中明文存储
    password_hash = db.Column(db.String(255))
    # 所属部门(外键到部门表)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    # 所属部门(关系反向映射)
    department = db.relationship('department', foreign_keys=department_id, backref='users')
    # 部门领导
    LEADER_STR = [(1, u'普通员工'),(0, u'部门负责人')]
    leader = db.Column(ChoiceTypeInteger(LEADER_STR), default=1)
    # 是否离职
    ## is_quit = db.Column(db.Boolean, default=True)
    ISQUIT_STR = [(1, u'在职'),(0, u'离职')]
    is_quit = db.Column(ChoiceTypeInteger(ISQUIT_STR), default=1)
    # 用户角色
    ROLE_STR = [(0, u'系统管理员'), (1, u'普通账号')]
    role = db.Column(ChoiceTypeInteger(ROLE_STR), default=1)
    # 最后登录时间
    last_login = db.Column(db.DateTime, nullable=True)
    # 创建时间
    ctime = db.Column(db.DateTime, default=datetime.datetime.now)
    # 修改时间
    mtime = db.Column(db.DateTime, onupdate=datetime.datetime.now)


    def __unicode__(self):
        return u"%s" % self.name

    def save_last_login_time(self):
        self.last_login = datetime.datetime.now
        db.session.add(self)
        db.session.commit()

    # 所以需要对用户传入的明文密码进行加密
    @property
    def password(self):
        """
        password属性函数
        不允许直接读取原始值
        """
        return "密码不是可读形式!"

    @password.setter
    def password(self, password):
        """
        设置密码hash值
        """
        #self.password_hash = werkzeug.security.generate_password_hash(password)
        self.password_hash = werkzeug.generate_password_hash(password)

    def verify_password(self, password):
        """
        将用户输入的密码明文与数据库比对
        """
        #return werkzeug.security.check_password_hash(self.password_hash,password)
        return werkzeug.check_password_hash(self.password_hash, password)


class casetype(db.Model):
    """
    工单类型
    """
    #__tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 类型名称
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    # 工单类型创建人
    createuser_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    createuser = db.relationship('user',foreign_keys=createuser_id,backref='casetype')
    # 默认确认时长（分）
    confirm_duration = db.Column(db.Integer, default=30,nullable=False)
    # 默认执行时长（分）
    exec_duration = db.Column(db.Integer, default=30, nullable=False)
    # 默认有效期（天）
    effective_date = db.Column(db.Integer, default=5, nullable=False)
    # 工单类型表单
    type_form = db.Column(db.Text,nullable=True)
    # 执行流
    exec_model = db.relationship('caseexecmodel', backref=db.backref('casetype', lazy='dynamic', uselist=True))
    # 审核流
    audit_model = db.relationship('caseauditmodel', backref=db.backref('casetype', lazy='dynamic', uselist=True))
    # 创建时间
    ctime = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    # 修改时间
    mtime = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    # 状态
    STATUS_STR = [(1, u'启用'),(2, u'禁用'),(3, u'已删除')]
    status = db.Column(ChoiceTypeInteger(STATUS_STR),default=1)

    def __unicode__(self):
        return u'%s' % self.name

class caseexecmodel(db.Model):
    """
    执行人流程（多个执行人）
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 工单类型
    casetype_id = db.Column(db.Integer, db.ForeignKey('casetype.id',ondelete='CASCADE'))
    case_type = db.relationship('casetype', foreign_keys=casetype_id,backref=db.backref("caseexecmodel",  cascade="all, delete-orphan"))
    # 执行人（可以配置负数表示自动执行）
    user_id = db.Column(db.Integer, nullable=False)
    # 执行顺序
    order = db.Column(db.SmallInteger, nullable=False)

    def __unicode__(self):
        return u'id: %d' % self.id

class caseauditmodel(db.Model):
    """
    审核流程（多个审核人）
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 工单类型
    casetype_id = db.Column(db.Integer, db.ForeignKey('casetype.id',ondelete='CASCADE'))
    case_type = db.relationship('casetype', foreign_keys=casetype_id,backref=db.backref("caseauditmodel",cascade="all, delete-orphan"))
    # 审核人（可以配置负数表示默认上级或自动审核）
    user_id = db.Column(db.Integer, nullable=False)
    # 审核顺序
    order = db.Column(db.SmallInteger, nullable=False)

    def __unicode__(self):
        return u'id: %d' % self.id


class case(db.Model):
    """
    需求工单
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 工单标题
    title = db.Column(db.String(250),nullable=False)
    # 工单类型
    casetype_id = db.Column(db.Integer, db.ForeignKey('casetype.id'))
    casetype = db.relationship('casetype', foreign_keys=casetype_id)
    # 工单创建人
    createuser_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    createuser = db.relationship('user',foreign_keys=createuser_id,backref='case')
    # 工单需求 json 数据
    content = db.Column(db.Text,nullable=False)
    # 工单结果 json 数据
    result = db.Column(db.Text,nullable=True)
    # 第几个审核人, 为当前审核人（顺序）
    auditNum = db.Column(db.SmallInteger, nullable=False,default=0)
    # 第几个执行人，为当前执行人（顺序）
    execNum = db.Column(db.SmallInteger, nullable=False,default=0)
    # 审核状态
    STATUS_STR = [(1, u'待提交'),
                  (2, u'审核中'),
                  (3, u'执行人确认中'),
                  (4, u'执行人执行中'),
                  (5, u'执行人延期执行中'),
                  (6, u'执行完成,用户确认中'),
                  (7, u'审核驳回,等待用户确认'),
                  (8, u'执行驳回,等待用户确认'),
                  (9, u'用户确认不通过,等待执行重做'),
                  (10, u'完成关闭'),
                  (11, u'驳回关闭'),
                  (12, u'撤销关闭'),
                  ]
    status = db.Column(ChoiceTypeInteger(STATUS_STR),default=2)
    # 创建时间
    ctime = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    # 修改时间
    mtime = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    # 审核流
    auditflow = db.relationship('caseaudit', backref=db.backref('case', lazy='dynamic', uselist=True))
    # 执行流
    execflow = db.relationship('caseexec', backref=db.backref('case', lazy='dynamic', uselist=True))
    # 操作记录
    operation = db.relationship('caseoperation', backref=db.backref('case', lazy='dynamic', uselist=True))

    def __unicode__(self):
        return u'id: %d' % self.id

class caseaudit(db.Model):
    """
    工单审核流程（多个审核人）
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 工单
    case_id = db.Column(db.Integer, db.ForeignKey('case.id',ondelete='CASCADE'))
    case_rs = db.relationship('case', foreign_keys=case_id,
                              backref=db.backref("caseaudit",cascade="all, delete-orphan"))
    # 审核人
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_rs = db.relationship('user', foreign_keys=user_id)
    # 审核顺序
    order = db.Column(db.SmallInteger, nullable=False)
    # 执行状态
    STATUS_STR = [(0, u'未审核'),(1,u'已审核')]
    status = db.Column(ChoiceTypeInteger(STATUS_STR),default=0)

    def __unicode__(self):
        return u'id: %d' % self.id

class caseexec(db.Model):
    """
    工单执行人流程（多个执行人）
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 工单
    case_id = db.Column(db.Integer, db.ForeignKey('case.id', ondelete='CASCADE'))
    case_rs = db.relationship('case', foreign_keys=case_id,
                              backref=db.backref("caseexec", cascade="all, delete-orphan"))
    # 执行人
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_rs = db.relationship('user', foreign_keys=user_id)
    # 执行顺序
    order = db.Column(db.SmallInteger, nullable=False)
    # 执行状态
    STATUS_STR = [(0, u'未执行'),(1,u'已执行'),(2, u'已超时')]
    status = db.Column(ChoiceTypeInteger(STATUS_STR), default=0)

    def __unicode__(self):
        return u'id: %d' % self.id

class caseoperation(db.Model):
    """
    工单操作表
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 工单
    case_id = db.Column(db.Integer, db.ForeignKey('case.id', ondelete='CASCADE'))
    case_rs = db.relationship('case', foreign_keys=case_id,
                              backref=db.backref("caseoperation", cascade="all, delete-orphan"))
    # 操作人
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_rs = db.relationship('user', foreign_keys=user_id)
    # 操作类型
    STATUS_STR = [(1, u'提交'),
                          (2, u'审核通过'),
                          (3, u'审核不通过'),
                          (4, u'审核转发'),
                          (5, u'确认执行'),
                          (6, u'执行确认不通过'),
                          (7, u'延期执行'),
                          (8, u'执行完成'),
                          (9, u'执行转发'),
                          (10,u'用户确认不通过'),
                          (11, u'关闭'),
                          (12,u'重走流程'),
                          (13,u'重新编辑'),
                          (14, u'撤回工单'),
                          (15,u'回复'),]
    status = db.Column(ChoiceTypeInteger(STATUS_STR), default=1)
    # 回复内容
    content = db.Column(db.String(500), nullable=True)
    # 创建时间
    ctime = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)

    def __unicode__(self):
        return u'id: %d' % self.id


class project(db.Model):
    """
    项目表
    """
    #__tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 项目名称
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    # 项目英文名称
    enname = db.Column(db.String(100), nullable=False)
    # 负责人(外键到用户表)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 负责人(关系反向映射)
    user = db.relationship('user', foreign_keys=user_id, backref='project')
    # 创建时间
    ctime = db.Column(db.DateTime, default=datetime.datetime.now)
    # 修改时间
    mtime = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __unicode__(self):
        return u"%s" % self.name

class engineroom(db.Model):
    """
    机房表
    """
    #__tablename__ = 'engineroom'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 机房名称
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    # 英文名称
    enname = db.Column(db.String(100), nullable=True)
    # 联系人
    contact = db.Column(db.String(100), nullable=True)
    # 电话
    phone = db.Column(db.String(30), nullable=True)
    # 邮箱
    mail = db.Column(db.String(200), nullable=True)
    # 机房地址
    address = db.Column(db.String(255), nullable=True)
    # 创建时间
    ctime = db.Column(db.DateTime, default=datetime.datetime.now)
    # 修改时间
    mtime = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __unicode__(self):
        return u"%s" % self.name

# class Network(db.Model):
#     """
#     网络IP
#     """
#     # __tablename__ = 'network'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     # ip 地址
#     ip_address = db.Column(db.String(50), nullable=False)
#     # ip 版本号
#     IP_VERSION_STR = [(4, u'ipv4'),
#                      (6, u'ipv6')
#                      ]
#     ip_version = db.Column(ChoiceTypeInteger(IP_VERSION_STR), nullable=False,default=4)
#     # ip 类型
#     IP_TYPE_STR = [(1, u'内网'),
#                       (2, u'外网'),
#                       (3, u'内网VIP'),
#                       (4, u'外网VIP')
#                       ]
#     ip_type = db.Column(ChoiceTypeInteger(IP_TYPE_STR), nullable=False, default=4)
#     # 所属机房(外键到机房表)
#     engineroom_id = db.Column(db.Integer, db.ForeignKey('engineroom.id'), nullable=False)
#     # 所属机房(关系反向映射)
#     engineroom = db.relationship('Engineroom', foreign_keys=engineroom_id, backref='network')
#     # 带宽类型
#     BANDWIDTH_TYPE_STR = [(1, u'独享带宽'),
#                   (2, u'共享带宽')]
#     bandwidth_type = db.Column(ChoiceTypeInteger(BANDWIDTH_TYPE_STR), nullable=False,default=2)
#     # 带宽大小
#     bandwidth_size = db.Column(db.String(10), nullable=True)
#     # 绑定类型
#     BIND_TYPE_STR = [(0,u"未选择设备类型"),(1,u'主机'),(2,u'路由'),(3,u'交换机')]
#     bind_type = db.Column(ChoiceTypeInteger(BIND_TYPE_STR), nullable=False,default=0)
#     # 绑定设备ID
#     bind_id = db.Column(db.String(100), nullable=True)
#     # 状态
#     STATUS_NETWORK_STR = [(1, u'未绑定'),(2, u'已绑定'),(3, u'已冻结')]
#     status = db.Column(ChoiceTypeInteger(STATUS_NETWORK_STR), nullable=False, default=1)
#     # 创建时间
#     ctime = db.Column(db.DateTime, default=datetime.datetime.now)
#     # 修改时间
#     mtime = db.Column(db.DateTime, onupdate=datetime.datetime.now)
#
# class Server(db.Model):
#     """
#     服务器主机
#     """
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     # 主机名
#     hostname = db.Column(db.String(200), nullable=False)
#     # 资产编号
#     property_no = db.Column(db.String(100), unique=True, nullable=True)
#     # 服务器资产类型
#     PROPERTY_TYPE_STR = [(1, u'自购'),
#                          (2, u'租用'),
#                          (3, u'第三方提供')]
#     property_type = db.Column(ChoiceTypeInteger(PROPERTY_TYPE_STR), nullable=False)
#     # 服务器使用类型
#     USE_TYPE_STR = [(1, u'本司自用'),
#                     (2, u'第三方使用')]
#     use_type = db.Column(ChoiceTypeInteger(USE_TYPE_STR), nullable=False)
#     # 是否vm虚拟机, 不是虚拟机则用0表示, 否则就代表虚拟机的宿主机id
#     is_vm = db.Column(db.SmallInteger, nullable=False, default=0)
#     # 服务器使用状态
#     STATUS_STR = [(101,u'在用-正常使用中'),
#                   (102,u'空闲-正常空闲'),
#                   (103,u'已报废'),
#                   (104,u'已退租')]
#     status = db.Column(ChoiceTypeInteger(STATUS_STR), nullable=False)
#     # 主机所属机房
#     engineroom_id = db.Column(db.Integer, db.ForeignKey('engineroom.id'), nullable=False)
#     # 主机所属机房
#     engineroom = db.relationship('Engineroom', foreign_keys=engineroom_id, backref='server')
#     # 主机项目
#     serverproject = db.relationship('Serverproject', backref=db.backref('serverproject', lazy='dynamic', uselist=True),cascade="all, delete, delete-orphan")
#     # 主机IP
#     serverip = db.relationship('Serverip', backref=db.backref('serverip', lazy='dynamic', uselist=True),cascade="all, delete, delete-orphan")
#     # 创建时间
#     ctime = db.Column(db.DateTime, default=datetime.datetime.now)
#     # 修改时间
#     mtime = db.Column(db.DateTime, onupdate=datetime.datetime.now)
#
#     def __unicode__(self):
#         return u'propertyNo: %s , propertyType: %s , saltid: %s' % (self.propertyNo, self.propertyType, self.isVM)
#
# class Serverip(db.Model):
#     """
#     服务器挂钩多个IP地址
#     """
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     # 服务器
#     server_id = db.Column(db.Integer, db.ForeignKey('server.id'))
#     server = db.relationship('Server', foreign_keys=server_id)
#     # 主机绑定IP(外键到网络表)
#     network_id = db.Column(db.Integer, db.ForeignKey('network.id'), nullable=False)
#     # 主机绑定IP(关系反向映射)
#     network = db.relationship('Network', foreign_keys=network_id, backref='serverip')
#
#     def __unicode__(self):
#         return u'id: %d' % self.id
#
# class Serverproject(db.Model):
#     """
#     服务器挂钩多个项目
#     """
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     # 服务器
#     server_id = db.Column(db.Integer, db.ForeignKey('server.id'))
#     server = db.relationship('Server', foreign_keys=server_id)
#     # project
#     project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
#     project = db.relationship('Project', foreign_keys=project_id)
#
#     def __unicode__(self):
#         return u'id: %d' % self.id
# coding=utf-8

import json
from jinja2 import TemplateNotFound
from flask import Blueprint, Response,request,render_template,url_for,redirect,abort,session,g
from ops.database.model import db,department,user
from sqlalchemy import or_,and_,desc
from ops.users.login import userLogin

## 用户蓝图
userBlue = Blueprint('users', __name__ , template_folder='../templates/users',static_url_path='',static_folder='')


@userBlue.route('/user/', methods=['GET', 'POST'])
def userList():
    """
    用户管理
    """
    # print request.args.items().__str__()
    # print request.form.items()

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': '','data':[]}

    ## 添加用户
    if request.form.has_key('oper') and request.form['oper'] == "add":
        name = str(request.form['name'])
        cnname = str(request.form['cnname'])
        departmentID = int(request.form['department'])
        leader = int(request.form['leader'])
        role = int(request.form['role'])
        isQuit = int(request.form['is_quit'])
        password = str(request.form['password'])

        ## check
        checkData = user.query.filter(or_(user.name == name)).first()
        if checkData:
            returnData['status'] = 1
            returnData['message'] = '该用户名称已经存在'
            return Response(json.dumps(returnData), mimetype="application/json")

        ## add
        try:
            addData = user(name=name, cnname=cnname,password=password,department_id=departmentID,leader=leader,is_quit=isQuit,role=role)
            db.session.add(addData)
            db.session.commit()
        except:
            returnData['status'] = 1
            returnData['message'] = '新增失败'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 删除用户
    elif request.form.has_key('oper') and request.form['oper'] == "del":
        ids = str(request.form['id']).split(',')

        for id in ids:
            ## check
            checkData = user.query.filter(user.id == id).first()
            if not checkData:
                returnData['status'] = 1
                returnData['message'] = returnData['message']+'id:'+str(id)+' 该用户不存在;'

            ## delete
            try:
                db.session.delete(checkData)
                db.session.commit()
            except:
                returnData['status'] = 1
                returnData['message'] = returnData['message'] + 'id:' + str(id) + ' 该用户删除失败;'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 编辑用户
    elif request.form.has_key('oper') and request.form['oper'] == "edit":
        id = int(request.form['id'])
        name = str(request.form['name'])
        cnname = str(request.form['cnname'])
        departmentID = int(request.form['department'])
        leader = int(request.form['leader'])
        role = int(request.form['role'])
        isQuit = int(request.form['is_quit'])
        password = str(request.form['password'])

        ## check
        checkData = user.query.filter(user.id != id).filter(or_(user.name == name)).first()
        if checkData:
            returnData['status'] = 1
            returnData['message'] = '该用户名称已经存在'
            return Response(json.dumps(returnData), mimetype="application/json")

        ## edit
        try:
            editData = user.query.filter(user.id == id).first()
            editData.name = name
            editData.cnname = cnname
            editData.password = password
            editData.department_id = departmentID
            editData.is_quit = isQuit
            editData.leader = leader
            editData.role = role

            db.session.add(editData)
            db.session.commit()
        except:
            returnData['status'] = 1
            returnData['message'] = '编辑失败'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 获取用户(给页面表格下拉框准备， 前端js函数：getUsers)
    elif request.form.has_key('oper') and request.form['oper'] == "getUsers":
        allData = user.query.filter().all()
        if allData:
            userStr = ""  # 组合成适用于编辑框的select格式
            for u in allData:
                if userStr:
                    userStr = userStr + ";" + str(u.id) + ":" + str(u.name)
                else:
                    userStr = str(u.id) + ":" + str(u.name)
                returnData['data'].append({'id': u.id, 'name': u.name, 'cnname': u.cnname})
            returnData['message'] = userStr

        else:
            returnData['status'] = 1
            returnData['message'] = "error"
        return Response(json.dumps(returnData), mimetype="application/json")

    ## request.method == "GET":
    elif request.args.has_key('type') and request.args.get('type') == "load" or \
                    request.args.has_key('type') and request.args.get('type') == "search":

        load_search = request.args.get("_search")
        load_nd = int(request.args.get("nd"))
        load_rows = int(request.args.get("rows"))
        load_page = int(request.args.get("page"))
        load_sidx = str(request.args.get("sidx"))
        load_sord = str(request.args.get("sord"))
        len_min = load_page * load_rows - load_rows
        len_max = load_page * load_rows
        loadData = {"total": "0", "page": str(load_page), "records": "0", "data": []}

        allData = user.query.filter()
        if request.args.get('type') == "search":
            _search_cnname = request.args.get("search_cnname")
            _search_enname = request.args.get("search_enname")
            if _search_enname:
                allData = allData.filter(user.name.ilike('%%%s%%' % _search_enname))
            if _search_cnname:
                allData = allData.filter(user.cnname.ilike('%%%s%%' % _search_cnname))

        ## sord
        if not load_sidx:
            load_sidx = "id"
        if load_sord == "desc":
            allData = allData.order_by(desc(load_sidx)).all()
        else:
            allData = allData.order_by(load_sidx).all()

        for record in allData[len_min:len_max]:
            _mtime = record.mtime
            last_login = record.last_login
            if not _mtime: _mtime = record.ctime
            if not last_login: last_login = ""
            tmpData = {'id': record.id,
               'name': record.name,
               'cnname': record.cnname,
               'password':"*********",
               'is_quit':record.is_quit.label,
               'role': record.role.label,
               'last_login':str(last_login),
               'department':record.department.name,
               'leader':record.leader.label,
               'ctime': str(record.ctime),
               'mtime': str(_mtime)
               }
            loadData['data'].append(tmpData)

        loadData['records'] = str(len(allData))  ## rows
        loadData['total'] = str(len(allData) / int(load_rows) + 1)  ## pages

        return Response(json.dumps(loadData), mimetype="application/json")

    else:
        pass

    try:
        return render_template('user.html',userInfo=loginData['user'])
    except TemplateNotFound:
        abort(404)

@userBlue.route('/department/', methods=['GET', 'POST'])
def departmentList():
    """
    部门管理
    """
    # print request.args.items().__str__()
    # print request.form

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': ''}

    ## 添加部门
    if request.form.has_key('oper') and request.form['oper'] == "add":
        name = str(request.form['name'])
        enname = str(request.form['enname'])
        parent_id = int(request.form['parent'])

        ## check
        checkData = department.query.filter(or_(department.name == name, department.enname == enname)).first()
        if checkData:
            returnData['status'] = 1
            returnData['message'] = '该部门名称已经存在'
            return Response(json.dumps(returnData), mimetype="application/json")

        ## add
        try:
            addData = department(name = name, enname = enname,parent = parent_id)
            db.session.add(addData)
            db.session.commit()
        except:
            returnData['status'] = 1
            returnData['message'] = '新增失败'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 删除部门
    elif request.form.has_key('oper') and request.form['oper'] == "del":
        ids = str(request.form['id']).split(',')

        for id in ids:
            ## check
            checkData = department.query.filter(department.id == id).first()
            if not checkData:
                returnData['status'] = 1
                returnData['message'] = returnData['message'] + 'id:' + str(id) + ' 该部门不存在;'

            ## delete
            try:
                db.session.delete(checkData)
                db.session.commit()
            except:
                returnData['status'] = 1
                returnData['message'] = returnData['message'] + 'id:' + str(id) + ' 删除失败;'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 修改部门
    elif request.form.has_key('oper') and request.form['oper'] == "edit":
        id = int(request.form['id'])
        name = str(request.form['name'])
        enname = str(request.form['enname'])
        parent_id = int(request.form['parent'])

        ## check
        checkData = department.query.filter(department.id != id) \
            .filter(or_(department.name == name,department.enname == enname)).first()
        if checkData:
            returnData['status'] = 1
            returnData['message'] = '该部门名称已经存在'
            return Response(json.dumps(returnData), mimetype="application/json")

        ## edit
        try:
            editData = department.query.filter(department.id == id).first()
            editData.name = name
            editData.enname = enname
            editData.parent = parent_id

            db.session.add(editData)
            db.session.commit()
        except:
            returnData['status'] = 1
            returnData['message'] = '编辑失败'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 获取部门(给页面下拉框准备， 前端js函数：getDepartment)
    elif request.form.has_key('oper') and request.form['oper'] == "getDepartment":

        allData = department.query.filter().all()
        if allData:
            depStr = ""  # 组合成适用于编辑框的select格式
            for dep in allData:
                if depStr:
                    depStr = depStr + ";" + str(dep.id) + ":" + str(dep.name)
                else:
                    depStr = str(dep.id) + ":" + str(dep.name)
            returnData['message'] = depStr
        else:
            returnData['status'] = 1
            returnData['message'] = "error"
        return Response(json.dumps(returnData), mimetype="application/json")

    ## request.method == "GET":
    elif request.args.has_key('type') and request.args.get('type') == "load" or \
        request.args.has_key('type') and request.args.get('type') == "search":

        load_search = request.args.get("_search")
        load_nd = int(request.args.get("nd"))
        load_rows = int(request.args.get("rows"))
        load_page = int(request.args.get("page"))
        load_sidx = str(request.args.get("sidx"))
        load_sord = str(request.args.get("sord"))
        len_min = load_page * load_rows - load_rows
        len_max = load_page * load_rows
        loadData = {"total": "0", "page": str(load_page), "records": "0", "data": []}

        allData = department.query.filter()
        if request.args.get('type') == "search":
            _search_cnname = request.args.get("search_cnname")
            _search_enname = request.args.get("search_enname")
            if _search_cnname:
                allData = allData.filter(department.name.ilike('%%%s%%' % _search_cnname))
            if _search_enname:
                allData = allData.filter(department.enname.ilike('%%%s%%' % _search_enname))

        ## sord
        if not load_sidx:
            load_sidx = "id"
        if load_sord == "desc":
            allData = allData.order_by(desc(load_sidx)).all()
        else:
            allData = allData.order_by(load_sidx).all()

        for record in allData[len_min:len_max]:
            _mtime = record.mtime
            if not _mtime:_mtime = record.ctime

            if record.parent == 0 :
                parent = "顶级部门"
            else:
                p = department.query.filter(department.id == record.parent).first()
                parent = str(p.name)

            tmpData = {'id': record.id,
                'name': record.name,
                'enname': record.enname,
                'parent' : parent,
                'ctime': str(record.ctime),
                'mtime': str(_mtime)
            }
            loadData['data'].append(tmpData)

        loadData['records'] = str(len(allData))  ## rows
        loadData['total'] = str(len(allData) / int(load_rows) + 1)  ## pages

        return Response(json.dumps(loadData), mimetype="application/json")
    else:
        pass

    try:
        return render_template('department.html',userInfo=loginData['user'])
    except TemplateNotFound:
        abort(404)


@userBlue.route('/login/', methods=['GET', 'POST'])
def login():
    ###
    ## 登录
    ###

    allUser = user.query.filter().all()
    userNum = len(allUser)

    if request.form.has_key('oper') and request.form['oper'] == "login":
        username = str(request.form['username'])
        password = str(request.form['password'])

        if userNum == 0:

            addDepartment = department(name='sa', enname='sa')
            db.session.add(addDepartment)

            addUser = user()
            addUser.name = username
            addUser.cnname = username
            addUser.department = addDepartment
            addUser.leader = 0
            addUser.role = 0
            addUser.password = password
            db.session.add(addUser)
            db.session.commit()

            session['username'] = username
            return redirect("/")
        else:
            loginUser = user.query.filter(user.name == username).first()
            if loginUser is not None and loginUser.verify_password(password):
                session['username'] = username
                return redirect("/")
            else:
                return redirect("/users/login/")

    try:
        return render_template('login.html', userNum=userNum)
    except TemplateNotFound:
        abort(404)


@userBlue.route('/logout/', methods=['GET', 'POST'])
def logout():
    if 'username' in session:
        session.pop('username', None)
    return redirect("/users/login/")


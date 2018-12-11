# coding=utf-8

import json
from jinja2 import TemplateNotFound
from flask import Blueprint, Response,request,render_template,url_for,redirect,abort,session,g
from ops.database.model import db,department,user,project
from sqlalchemy import or_,and_,desc
from ops.users.login import userLogin

## 用户蓝图
assetsBlue = Blueprint('assets', __name__ , template_folder='../templates/assets',static_url_path='',static_folder='')

@assetsBlue.route('/project/', methods=['GET', 'POST'])
def projectList():
    """
    项目管理管理
    """
    # print request.args.items().__str__()
    # print request.form.items()

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': '','data':[]}

    ## 添加项目
    if request.form.has_key('oper') and request.form['oper'] == "add":
        name = str(request.form['name'])
        enname = str(request.form['enname'])
        leader = int(request.form['leader'])

        ## check
        checkData = project.query.filter(or_(project.name == name,project.enname == enname)).first()
        if checkData:
            returnData['status'] = 1
            returnData['message'] = '该项目名称已经存在'
            return Response(json.dumps(returnData), mimetype="application/json")

        ## add
        try:
            addData = project(name=name, enname=enname,user_id=leader)
            db.session.add(addData)
            db.session.commit()
        except:
            returnData['status'] = 1
            returnData['message'] = '新增失败'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 删除项目
    elif request.form.has_key('oper') and request.form['oper'] == "del":
        ids = str(request.form['id']).split(',')

        for id in ids:
            ## check
            checkData = project.query.filter(project.id == id).first()
            if not checkData:
                returnData['status'] = 1
                returnData['message'] = returnData['message']+'id:'+str(id)+' 该项目不存在;'

            ## delete
            try:
                db.session.delete(checkData)
                db.session.commit()
            except:
                returnData['status'] = 1
                returnData['message'] = returnData['message'] + 'id:' + str(id) + ' 该项目删除失败;'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 编辑项目
    elif request.form.has_key('oper') and request.form['oper'] == "edit":
        id = int(request.form['id'])
        name = str(request.form['name'])
        enname = str(request.form['enname'])
        leader = int(request.form['leader'])

        ## check
        checkData = project.query.filter(project.id != id).filter(or_(project.name == name,project.enname == enname)).first()
        if checkData:
            returnData['status'] = 1
            returnData['message'] = '该项目名称已经存在'
            return Response(json.dumps(returnData), mimetype="application/json")

        ## edit
        try:
            editData = project.query.filter(project.id == id).first()
            editData.name = name
            editData.enname = enname
            editData.leader = leader

            db.session.add(editData)
            db.session.commit()
        except:
            returnData['status'] = 1
            returnData['message'] = '编辑失败'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 获取项目选择框下拉列表
    elif request.form.has_key('oper') and request.form['oper'] == "getProjects":
        allData = project.query.filter().all()
        if allData:
            projectStr = ""  # 组合成适用于编辑框的select格式
            for p in allData:
                if projectStr:
                    projectStr = projectStr + ";" + str(p.id) + ":" + str(p.name)
                else:
                    projectStr = str(p.id) + ":" + str(p.name)
                returnData['data'].append({'id': p.id, 'name': p.name, 'enname': p.enname})
            returnData['message'] = projectStr

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

        allData = project.query.filter()
        if request.args.get('type') == "search":
            _search_cnname = request.args.get("search_cnname")
            _search_enname = request.args.get("search_enname")
            if _search_cnname:
                allData = allData.filter(project.name.ilike('%%%s%%' % _search_cnname))
            if _search_enname:
                allData = allData.filter(project.enname.ilike('%%%s%%' % _search_enname))

        ## sord
        if not load_sidx:
            load_sidx = "id"
        if load_sord == "desc":
            allData = allData.order_by(desc(load_sidx)).all()
        else:
            allData = allData.order_by(load_sidx).all()

        for record in allData[len_min:len_max]:
            _mtime = record.mtime
            if not _mtime: _mtime = record.ctime
            tmpData = {'id': record.id,
               'name': record.name,
               'enname': record.enname,
               'leader': record.user.name,
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
        return render_template('project.html',userInfo=loginData['user'])
    except TemplateNotFound:
        abort(404)





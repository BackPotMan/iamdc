# coding=utf-8

import json
from jinja2 import TemplateNotFound
from flask import Blueprint, Response,request,render_template,url_for,redirect,abort,session,g
from ops.database.model import db,user,casetype,caseexecmodel,caseauditmodel,case,caseaudit,caseexec,caseoperation
from sqlalchemy import or_,and_,desc
from ops.users.login import userLogin

## 用户蓝图
caseBlue = Blueprint('case', __name__ , template_folder='../templates/case',static_url_path='',static_folder='')


@caseBlue.route('/type/', methods=['GET', 'POST'])
def caseTypeList():
    """
    工单类型管理
    """
    # print request.args.items().__str__()
    # print request.form

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': '', 'data': []}

    ## 添加工单类型
    if request.form.has_key('oper') and request.form['oper'] == "addCaseType":

        casetype_name = str(request.form['casetype_name'])
        casetype_executor = int(request.form['casetype_executor'])
        casetype_checkleader = str(request.form['casetype_checkleader']).split(',')

        try:
            ## 新增工单类型
            addCaseType = casetype()
            addCaseType.name = casetype_name
            addCaseType.createuser_id = loginData['user']['id']
            db.session.add(addCaseType)

            ## 添加执行人
            addCaseExecModel = caseexecmodel()
            addCaseExecModel.case_type = addCaseType
            addCaseExecModel.user_id = casetype_executor
            addCaseExecModel.order = 0
            db.session.add(addCaseExecModel)

            ## 添加审核列表
            for checkleader in casetype_checkleader:
                addCaseAuditModel = caseauditmodel()
                addCaseAuditModel.case_type = addCaseType
                addCaseAuditModel.user_id = int(checkleader)
                addCaseAuditModel.order = casetype_checkleader.index(checkleader)
                db.session.add(addCaseAuditModel)
            #
            db.session.commit()
        except Exception as e:
            returnData['status'] = 1
            returnData['message'] = '新增失败:'+str(e)
            #db.session().rollback()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 删除工单类型
    elif request.form.has_key('oper') and request.form['oper'] == "delCaseType":
        casetype_ids = str(request.form['casetype_ids']).split(',')

        for casetypeId in casetype_ids:
            delData = casetype.query.filter(casetype.id == int(casetypeId)).first()
            db.session.delete(delData)
            db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 修改工单类型
    elif request.form.has_key('oper') and request.form['oper'] == "editCaseType":

        casetype_id = int(request.form['casetype_id'])
        casetype_name = str(request.form['casetype_name'])
        casetype_executor = int(request.form['casetype_executor'])
        casetype_checkleader = str(request.form['casetype_checkleader']).split(',')

        try:
            ## 编辑工单类型
            editCaseType = casetype.query.filter(casetype.id == casetype_id).first()
            editCaseType.name = casetype_name
            db.session.add(editCaseType)

            ## 删除执行人和审核人
            delExecData = caseexecmodel.query.filter(caseexecmodel.casetype_id == editCaseType.id ).all()
            for i in delExecData:
                db.session.delete(i)
            delAuditData = caseauditmodel.query.filter(caseauditmodel.casetype_id == editCaseType.id ).all()
            for i in delAuditData:
                db.session.delete(i)

            ## 添加执行人
            addCaseExecModel = caseexecmodel()
            addCaseExecModel.case_type = editCaseType
            addCaseExecModel.user_id = casetype_executor
            addCaseExecModel.order = 0
            db.session.add(addCaseExecModel)

            ## 添加审核列表
            for checkleader in casetype_checkleader:
                addCaseAuditModel = caseauditmodel()
                addCaseAuditModel.case_type = editCaseType
                addCaseAuditModel.user_id = int(checkleader)
                addCaseAuditModel.order = casetype_checkleader.index(checkleader)
                db.session.add(addCaseAuditModel)
            #
            db.session.commit()
        except:
            returnData['status'] = 1
            returnData['message'] = '修改失败'
        return Response(json.dumps(returnData), mimetype="application/json")

    ## 获取单条工单类型记录(为编辑工单准备数据)
    elif request.form.has_key('oper') and request.form['oper'] == "getCaseType":
        casetype_id = int(request.form['casetype_id'])

        getData = casetype.query.filter(casetype.id == casetype_id).first()
        rData = {}
        rData['id'] = getData.id
        rData['name'] = getData.name

        rData['executor'] = []
        for execModel in getData.exec_model:
            if execModel.user_id == "-1":
                rData['executor'].append("-1_默认上级")
            else:
                executor = user.query.filter(user.id == execModel.user_id).first()
                rData['executor'].append(str(executor.id) + "_" + str(executor.cnname) + "(" + str(executor.name) + ")")

        rData['checkleader'] = []
        for auditModel in getData.audit_model:
            if str(auditModel.user_id) == "-1":
                rData['checkleader'].append("-1_默认上级")
            else:
                checkleader = user.query.filter(user.id == auditModel.user_id).first()
                rData['checkleader'].append(str(checkleader.id) + "_" + str(checkleader.cnname) + "(" + str(checkleader.name) + ")")

        rData['users'] = []
        allUser = user.query.filter().all()
        for record in allUser:
            rData['users'].append({'id': record.id, 'name': record.name, 'cnname': record.cnname})

        return Response(json.dumps(rData), mimetype="application/json")

    ## request.method == "GET": 工单类型列表
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

        allData = casetype.query.filter()
        if request.args.get('type') == "search":
            _search_cnname = request.args.get("search_cnname")
            _search_enname = request.args.get("search_enname")
            if _search_enname:
                allData = allData.filter(casetype.name.ilike('%%%s%%' % _search_enname))
            if _search_cnname:
                allData = allData.filter(casetype.name.ilike('%%%s%%' % _search_cnname))

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
               'exec_model': "",
               'audit_model':"",
               'status': record.status.label,
               'ctime': str(record.ctime),
               }
            loadData['data'].append(tmpData)

            executor_str = ""
            for execModel in record.exec_model:
                if str(execModel.user_id) == "-1":
                    executor_name = "默认上级"
                else:
                    user_record = user.query.filter(user.id == int(execModel.user_id)).first()
                    executor_name = user_record.cnname

                if executor_str == "":
                    executor_str = "<span> " + executor_name + " </span>"
                else:
                    executor_str = executor_str + "<span class='glyphicon glyphicon-arrow-right'></span><span> " + executor_name + " </span>"
            tmpData['exec_model'] = executor_str

            checkleader_str = ""
            for auditModel in record.audit_model:
                if str(auditModel.user_id) == "-1":
                    checkleader_name = "默认上级"
                else:
                    user_record = user.query.filter(user.id == int(auditModel.user_id)).first()
                    checkleader_name = user_record.cnname

                if checkleader_str == "":
                    checkleader_str = "<span> " + checkleader_name + " </span>"
                else:
                    checkleader_str = checkleader_str + "<span class='glyphicon glyphicon-arrow-right'></span><span> " + checkleader_name + " </span>"
            tmpData['audit_model'] = checkleader_str

        loadData['records'] = str(len(allData))  ## rows
        loadData['total'] = str(len(allData) / int(load_rows) + 1)  ## pages

        return Response(json.dumps(loadData), mimetype="application/json")

    else:
        pass

    try:
        return render_template('caseType.html',userInfo=loginData['user'])
    except TemplateNotFound:
        abort(404)


@caseBlue.route('/create/', methods=['GET', 'POST'])
def caseCreate():
    """
    创建工单
    """
    # print request.args.items().__str__()
    # print request.form

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': '', 'data': []}

    ## 添加工单
    if request.form.has_key('oper') and request.form['oper'] == "addCase":
        caseTypeID =  int(request.form['casetype'])
        caseTitle = str(request.form['casetitle'])
        caseRequire = str(request.form['caserequire'])
        caseResult = str(request.form['caseresult'])

        ## 工单类型
        getCaseType = casetype.query.filter(casetype.id == caseTypeID).first()

        ## 判断是保存还是提交
        caseStatus = 2
        if request.form.has_key('save'):caseStatus=1

        ## 添加工单
        addCase = case()
        addCase.title = caseTitle
        addCase.casetype_id = caseTypeID
        addCase.createuser_id = loginData['user']['id']
        addCase.content = caseRequire
        addCase.result = caseResult
        addCase.status = caseStatus
        db.session.add(addCase)

        ## 添加审核人
        for auditUser in getCaseType.audit_model:
            if auditUser.user_id == -1:
                leaderUser = user.query.filter(user.department_id == loginData['user']['department_id']).filter(
                            user.leader == 0).first()
                audituser_id = leaderUser.id
            else:
                audituser_id = auditUser.user_id

            addCaseAudit = caseaudit()
            addCaseAudit.case_rs = addCase
            addCaseAudit.user_id = audituser_id
            addCaseAudit.order = auditUser.order
            addCaseAudit.status = 0
            db.session.add(addCaseAudit)

        ## 添加执行人
        for execUser in getCaseType.exec_model:
            addCaseExec = caseexec()
            addCaseExec.case_rs = addCase
            addCaseExec.user_id = execUser.user_id   ##后续需要修改
            addCaseExec.order = execUser.order
            addCaseExec.status = 0
            db.session.add(addCaseExec)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = addCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = 1
        addCaseOperation.content = ""
        db.session.add(addCaseOperation)

        db.session.commit()

        return redirect("/case/mycreate/")

    else:
        getData = casetype.query.filter().all()
        for record in getData:
            returnData['data'].append({'casetype_id':record.id,'casetype_name':record.name})

    try:
        return render_template('caseCreate.html', casetype_list=returnData['data'],userInfo=loginData['user'])
    except TemplateNotFound:
        abort(404)


@caseBlue.route('/mycreate/', methods=['GET', 'POST'])
def caseMyCreate():
    """
    我创建的工单
    """
    # print request.args.items().__str__()
    # print request.form

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': '', 'data': []}
    caseview = 0

    ## 撤回工单
    if request.form.has_key('oper') and request.form['oper'] == "revokeCase":
        case_id = int(request.form['caseid'])

        try:
            getCase = case.query.filter(case.id == case_id).first()
            getCase.status = 1
            getCase.auditNum = 0
            getCase.execNum = 0
            db.session.add(getCase)

            ## 修改审核人状态
            for auditFlow in getCase.auditflow:
                auditFlow.status = 0
                db.session.add(auditFlow)

            ## 修改执行人状态
            for execFlow in getCase.execflow:
                execFlow.status = 0
                db.session.add(execFlow)

            ## 添加操作步骤
            addCaseOperation = caseoperation()
            addCaseOperation.case_rs = getCase
            addCaseOperation.user_id = loginData['user']['id']
            addCaseOperation.status = 14
            addCaseOperation.content = "revoke Case"
            db.session.add(addCaseOperation)

            db.session.commit()

        except :
            print "revokeCase error"

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 删除工单
    elif request.form.has_key('oper') and request.form['oper'] == "deleteCase":
        case_id = int(request.form['caseid'])

        getCase = case.query.filter(case.id == case_id).first()
        db.session.delete(getCase)
        db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 编辑工单
    elif request.form.has_key('oper') and request.form['oper'] == "editCase":

        caseid =  int(request.form['caseid'])
        caserequire = str(request.form['caserequire'])

        editCase = case.query.filter(and_(case.id == caseid, case.createuser_id == loginData['user']['id'])).first()

        ## 判断是保存还是提交
        casestatus = 2
        operationstatus = 1
        if request.form.has_key('save'):
            casestatus=1
        if request.form.has_key('reset'):
            casestatus = 9
            operationstatus = 10
            editCase.execNum = 0
            for execUser in editCase.execflow:
                execUser.status = 0
                db.session.add(execUser)
        if request.form.has_key('close'):
            casestatus = 10
            operationstatus = 11

        ##
        editCase.content = caserequire
        editCase.status = casestatus
        db.session.add(editCase)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = editCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = operationstatus
        addCaseOperation.content = ""
        db.session.add(addCaseOperation)

        db.session.commit()

        return redirect("/case/mycreate/")

    ## 回复工单
    elif request.form.has_key('oper') and request.form['oper'] == "sendMessage":
        case_id = int(request.form['caseid'])
        message = str(request.form['message'])

        getCase = case.query.filter(case.id == case_id).first()
        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = getCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = 15
        addCaseOperation.content = message
        db.session.add(addCaseOperation)
        db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## request.method == "GET":  工单列表
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

        allData = case.query.filter(case.createuser_id == loginData['user']['id']).filter(case.status.in_([1,2,3,4,5,6,7,8,9]))
        if request.args.get('type') == "search":
            _search_cnname = request.args.get("search_cnname")
            if _search_cnname:
                allData = allData.filter(case.title.ilike('%%%s%%' % _search_cnname))

        ## sord
        if not load_sidx:
            load_sidx = "id"
        if load_sord == "desc":
            allData = allData.order_by(desc(load_sidx)).all()
        else:
            allData = allData.order_by(load_sidx).all()

        for record in allData[len_min:len_max]:

            if record.status.value == 2:
                userName = record.auditflow[record.auditNum].user_rs.name
            elif record.status.value in [3,4,5,9]:
                userName = record.execflow[record.execNum].user_rs.name
            else :
                userName = record.createuser.name

            tmpData = {'id': record.id,
                'title': record.title,
                'casetype': record.casetype.name,
                'user' : userName,
                'status': record.status.label,
                'ctime': str(record.ctime),
            }
            loadData['data'].append(tmpData)

        loadData['records'] = str(len(allData))  ## rows
        loadData['total'] = str(len(allData) / int(load_rows) + 1)  ## pages

        return Response(json.dumps(loadData), mimetype="application/json")

    ## request.method == "GET":  工单详情
    elif request.args.has_key('type') and request.args.get('type') == "view":
        case_id = int(request.args.get("caseID"))
        caseview = 1

        viewData = {}
        getCase = case.query.filter(case.id == case_id).first()
        viewData.update({'case_id':getCase.id,
                         'case_title':getCase.title,
                         'case_createuser':getCase.createuser.name,
                         'case_result':getCase.result,
                         'case_content': getCase.content,
                         'case_status': getCase.status.value,
                         'case_status_label': getCase.status.label,
                         'case_ctime': getCase.ctime,
                         'case_type': getCase.casetype.name,
                         })

        viewData.update({'audit_user':[]})
        for auditUser in getCase.auditflow:
            viewData['audit_user'].append({'name':auditUser.user_rs.name,'status':auditUser.status.value})

        viewData.update({'exec_user': []})
        for execUser in getCase.execflow:
            viewData['exec_user'].append({'name':execUser.user_rs.name,'status':execUser.status.value})

        viewData.update({'operation_user': []})
        for operationUser in getCase.operation:
            viewData['operation_user'].append({'name':operationUser.user_rs.name,
                                               'operation_type':operationUser.status.label,
                                               'content': operationUser.content,
                                               'ctime':operationUser.ctime})

        return render_template('caseMyCreate.html', userInfo=loginData['user'], caseview=caseview,
                               viewData=viewData)

    else:
        pass

    try:
        return render_template('caseMyCreate.html',userInfo=loginData['user'],caseview=caseview)
    except TemplateNotFound:
        abort(404)


@caseBlue.route('/check/', methods=['GET', 'POST'])
def caseCheck():
    """
    我的审核工单
    """
    # print request.args.items().__str__()
    # print request.form

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': '', 'data': []}
    caseview = 0

    ## 审核ok
    if request.form.has_key('oper') and request.form['oper'] == "caseCheckOK":
        case_id = int(request.form['caseid'])

        getCase = case.query.filter(case.id == case_id).first()
        auditNum = getCase.auditNum
        if auditNum + 1 == len(getCase.auditflow):
            getCase.status = 3
        else:
            getCase.auditNum = auditNum + 1
            getCase.status = 2
        db.session.add(getCase)

        getAuditflow = caseaudit.query.filter(caseaudit.case_id == getCase.id).filter(caseaudit.order==auditNum).first()
        getAuditflow.status = 1
        db.session.add(getAuditflow)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = getCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = 2
        addCaseOperation.content = "check ok"
        db.session.add(addCaseOperation)

        db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 审核no
    elif request.form.has_key('oper') and request.form['oper'] == "caseCheckNO":
        case_id = int(request.form['caseid'])

        getCase = case.query.filter(case.id == case_id).first()
        getCase.status = 7
        getCase.auditNum = 0
        getCase.execNum = 0
        db.session.add(getCase)

        ## 修改审核人状态
        for auditFlow in getCase.auditflow:
            auditFlow.status = 0
            db.session.add(auditFlow)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = getCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = 3
        addCaseOperation.content = "check no"
        db.session.add(addCaseOperation)

        db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 转发审核人
    elif request.form.has_key('oper') and request.form['oper'] == "caseForwarding":
        case_id = int(request.form['caseid'])
        user_id = int(request.form['checkleader_id'])


        getCase = case.query.filter(case.id == case_id).first()
        getUser = user.query.filter(user.id == user_id).first()
        getAuditflow = caseaudit.query.filter(caseaudit.case_id == case_id ).filter(caseaudit.order == getCase.auditNum).first()
        getAuditflow.user_id = user_id
        db.session.add(getAuditflow)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = getCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = 4
        addCaseOperation.content = str(loginData['user']['name'])+" Forwarding to "+ str(getUser.name)
        db.session.add(addCaseOperation)

        db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## request.method == "GET":  审核工单列表
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

        allData = case.query.filter(case.status.in_([2,7]))
        if request.args.get('type') == "search":
            _search_cnname = request.args.get("search_cnname")
            if _search_cnname:
                allData = allData.filter(case.title.ilike('%%%s%%' % _search_cnname))

        ## sord
        if not load_sidx:
            load_sidx = "id"
        if load_sord == "desc":
            allData = allData.order_by(desc(load_sidx)).all()
        else:
            allData = allData.order_by(load_sidx).all()

        for record in allData[len_min:len_max]:


            if not record.auditflow[record.auditNum].user_id == loginData['user']['id']:
                continue

            userName = record.auditflow[record.auditNum].user_rs.name
            tmpData = {'id': record.id,
                'title': record.title,
                'casetype': record.casetype.name,
                'user' : userName,
                'status': record.status.label,
                'ctime': str(record.ctime),
            }
            loadData['data'].append(tmpData)

        loadData['records'] = str(len(allData))  ## rows
        loadData['total'] = str(len(allData) / int(load_rows) + 1)  ## pages

        return Response(json.dumps(loadData), mimetype="application/json")

    ## request.method == "GET":  审核工单详情
    elif request.args.has_key('type') and request.args.get('type') == "view":
        case_id = int(request.args.get("caseID"))
        caseview = 1

        viewData = {}
        getCase = case.query.filter(case.id == case_id).first()
        viewData.update({'case_id':getCase.id,
                         'case_title':getCase.title,
                         'case_createuser':getCase.createuser.name,
                         'case_result':getCase.result,
                         'case_content': getCase.content,
                         'case_status': getCase.status.value,
                         'case_status_label': getCase.status.label,
                         'case_ctime': getCase.ctime,
                         'case_type': getCase.casetype.name,
                         })

        viewData.update({'audit_user':[]})
        for auditUser in getCase.auditflow:
            viewData['audit_user'].append({'name':auditUser.user_rs.name,'status':auditUser.status.value})

        viewData.update({'exec_user': []})
        for execUser in getCase.execflow:
            viewData['exec_user'].append({'name':execUser.user_rs.name,'status':execUser.status.value})

        viewData.update({'operation_user': []})
        for operationUser in getCase.operation:
            viewData['operation_user'].append({'name':operationUser.user_rs.name,
                                               'operation_type':operationUser.status.label,
                                               'content':operationUser.content,
                                               'ctime':operationUser.ctime})


        return render_template('caseCheck.html', userInfo=loginData['user'], caseview=caseview,
                               viewData=viewData)

    else:
        pass

    try:
        return render_template('caseCheck.html',userInfo=loginData['user'],caseview=caseview)
    except TemplateNotFound:
        abort(404)


@caseBlue.route('/execute/', methods=['GET', 'POST'])
def caseExecute():
    """
    我的执行工单
    """
    # print request.args.items().__str__()
    # print request.form

    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': '', 'data': []}
    caseview = 0

    ## 确认执行ok
    if request.form.has_key('oper') and request.form['oper'] == "caseExecOK":
        case_id = int(request.form['caseid'])

        getCase = case.query.filter(case.id == case_id).first()
        getCase.status = 4
        db.session.add(getCase)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = getCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = 5
        addCaseOperation.content = "exec ok"
        db.session.add(addCaseOperation)

        db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 执行no
    elif request.form.has_key('oper') and request.form['oper'] == "caseExecNO":
        case_id = int(request.form['caseid'])

        getCase = case.query.filter(case.id == case_id).first()
        getCase.status = 8
        getCase.auditNum = 0
        getCase.execNum = 0
        db.session.add(getCase)

        ## 修改审核人状态
        for auditFlow in getCase.auditflow:
            auditFlow.status = 0
            db.session.add(auditFlow)


        ## 修改审核人状态
        for execFlow in getCase.execflow:
            execFlow.status = 0
            db.session.add(execFlow)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = getCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = 6
        addCaseOperation.content = "exec no"
        db.session.add(addCaseOperation)

        db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 转发执行人
    elif request.form.has_key('oper') and request.form['oper'] == "caseForwarding":
        case_id = int(request.form['caseid'])
        user_id = int(request.form['executor_id'])

        getCase = case.query.filter(case.id == case_id).first()
        getUser = user.query.filter(user.id == user_id).first()
        getExecflow = caseexec.query.filter(caseexec.case_id == case_id ).filter(caseexec.order == getCase.execNum).first()
        getExecflow.user_id = user_id
        db.session.add(getExecflow)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = getCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = 9
        addCaseOperation.content = str(loginData['user']['name'])+" Forwarding to "+ str(getUser.name)
        db.session.add(addCaseOperation)

        db.session.commit()

        return Response(json.dumps(returnData), mimetype="application/json")

    ## 执行
    elif request.form.has_key('oper') and request.form['oper'] == "caseComplete":
        case_id = int(request.form['caseid'])
        casere_result = str(request.form['caseresult'])

        ## 判断是保存还是执行完成
        casestatus = 5
        if request.form.has_key('complete'): casestatus = 6

        getCase = case.query.filter(case.id == case_id).first()
        getCase.status = casestatus
        getCase.result = casere_result
        db.session.add(getCase)

        getExecflow = caseexec.query.filter(caseexec.case_id == case_id).filter(
            caseexec.order == getCase.execNum).first()
        if casestatus == 6:
            getExecflow.status = 1
            db.session.add(getExecflow)

        ## 添加操作步骤
        addCaseOperation = caseoperation()
        addCaseOperation.case_rs = getCase
        addCaseOperation.user_id = loginData['user']['id']
        addCaseOperation.status = casestatus + 2
        addCaseOperation.content = ""
        db.session.add(addCaseOperation)

        db.session.commit()

        return redirect("/case/execute/?type=view&caseID="+str(case_id))

    ## request.method == "GET": 执行工单列表
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

        allData = case.query.filter(case.status.in_([3,4,5,6,8,9]))
        if request.args.get('type') == "search":
            _search_cnname = request.args.get("search_cnname")
            if _search_cnname:
                allData = allData.filter(case.title.ilike('%%%s%%' % _search_cnname))

        ## sord
        if not load_sidx:
            load_sidx = "id"
        if load_sord == "desc":
            allData = allData.order_by(desc(load_sidx)).all()
        else:
            allData = allData.order_by(load_sidx).all()

        for record in allData[len_min:len_max]:
            if not record.execflow[record.execNum].user_id == loginData['user']['id']:
                continue

            userName = record.execflow[record.execNum].user_rs.name
            tmpData = {'id': record.id,
                'title': record.title,
                'casetype': record.casetype.name,
                'user' : userName,
                'status': record.status.label,
                'ctime': str(record.ctime),
            }
            loadData['data'].append(tmpData)

        loadData['records'] = str(len(allData))  ## rows
        loadData['total'] = str(len(allData) / int(load_rows) + 1)  ## pages

        return Response(json.dumps(loadData), mimetype="application/json")

    ## request.method == "GET": 工单详情
    elif request.args.has_key('type') and request.args.get('type') == "view":
        case_id = int(request.args.get("caseID"))
        caseview = 1

        viewData = {}
        getCase = case.query.filter(case.id == case_id).first()
        viewData.update({'case_id':getCase.id,
                         'case_title':getCase.title,
                         'case_createuser':getCase.createuser.name,
                         'case_result':getCase.result,
                         'case_content': getCase.content,
                         'case_status': getCase.status.value,
                         'case_status_label': getCase.status.label,
                         'case_ctime': getCase.ctime,
                         'case_type': getCase.casetype.name,
                         })

        viewData.update({'audit_user':[]})
        for auditUser in getCase.auditflow:
            viewData['audit_user'].append({'name':auditUser.user_rs.name,'status':auditUser.status.value})

        viewData.update({'exec_user': []})
        for execUser in getCase.execflow:
            viewData['exec_user'].append({'name':execUser.user_rs.name,'status':execUser.status.value})

        viewData.update({'operation_user': []})
        for operationUser in getCase.operation:
            viewData['operation_user'].append({'name':operationUser.user_rs.name,
                                               'operation_type':operationUser.status.label,
                                               'content':operationUser.content,
                                               'ctime':operationUser.ctime})

        return render_template('caseExecute.html', userInfo=loginData['user'], caseview=caseview,
                               viewData=viewData)

    else:
        pass

    try:
        return render_template('caseExecute.html',userInfo=loginData['user'],caseview=caseview)
    except TemplateNotFound:
        abort(404)


@caseBlue.route('/history/', methods=['GET', 'POST'])
def caseHistory():
    """
    我的审核工单
    """
    loginData = userLogin()
    if loginData['status'] == 1 :
        return redirect(loginData['uri'])

    ## 请求返回结果数据
    returnData = {'status': 0, 'message': '', 'data': []}
    caseview = 0

    if request.args.has_key('type') and request.args.get('type') == "load" or \
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

        allData = case.query.filter(case.createuser_id == loginData['user']['id']).filter(case.status.in_([10,11,12]))
        if request.args.get('type') == "search":
            _search_cnname = request.args.get("search_cnname")
            if _search_cnname:
                allData = allData.filter(case.title.ilike('%%%s%%' % _search_cnname))

        ## sord
        if not load_sidx:
            load_sidx = "id"
        if load_sord == "desc":
            allData = allData.order_by(desc(load_sidx)).all()
        else:
            allData = allData.order_by(load_sidx).all()

        for record in allData[len_min:len_max]:

            isAuditUser = 0
            for auditUser in record.auditflow:
                if auditUser.user_id == loginData['user']['id']:
                    isAuditUser = 1
                    break

            isExecUser = 0
            for execUser in record.execflow:
                if execUser.user_id == loginData['user']['id']:
                    isExecUser = 1
                    break

            isCreateUser = 0
            if record.createuser_id == loginData['user']['id']:
                isCreateUser = 1

            if isCreateUser == 0 and isAuditUser == 0 and isExecUser == 0:
                continue

            tmpData = {'id': record.id,
                'title': record.title,
                'casetype': record.casetype.name,
                'status': record.status.label,
                'ctime': str(record.ctime),
            }
            loadData['data'].append(tmpData)

        loadData['records'] = str(len(allData))  ## rows
        loadData['total'] = str(len(allData) / int(load_rows) + 1)  ## pages

        return Response(json.dumps(loadData), mimetype="application/json")
    elif request.args.has_key('type') and request.args.get('type') == "view":
        case_id = int(request.args.get("caseID"))
        caseview = 1

        viewData = {}
        getCase = case.query.filter(case.id == case_id).first()
        viewData.update({'case_id':getCase.id,
                         'case_title':getCase.title,
                         'case_createuser':getCase.createuser.name,
                         'case_result':getCase.result,
                         'case_content': getCase.content,
                         'case_status': getCase.status.value,
                         'case_status_label': getCase.status.label,
                         'case_ctime': getCase.ctime,
                         'case_type': getCase.casetype.name,
                         })

        viewData.update({'audit_user':[]})
        for auditUser in getCase.auditflow:
            viewData['audit_user'].append({'name':auditUser.user_rs.name,'status':auditUser.status.value})

        viewData.update({'exec_user': []})
        for execUser in getCase.execflow:
            viewData['exec_user'].append({'name':execUser.user_rs.name,'status':execUser.status.value})

        viewData.update({'operation_user': []})
        for operationUser in getCase.operation:
            viewData['operation_user'].append({'name':operationUser.user_rs.name,
                                               'operation_type':operationUser.status.label,
                                               'content':operationUser.content,
                                               'ctime':operationUser.ctime})


        return render_template('caseHistory.html', userInfo=loginData['user'], caseview=caseview,
                               viewData=viewData)
    else:
        pass

    try:
        return render_template('caseHistory.html',userInfo=loginData['user'],caseview=caseview)
    except TemplateNotFound:
        abort(404)

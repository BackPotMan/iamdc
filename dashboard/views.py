#coding=utf-8
from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django.db.models import Q
from dashboard.models import *
import time,json,os,urllib,sys,subprocess,datetime,signal
import json

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

G_TICKET_STATUS = {1:'待提交',
                   2:'审核中',
                   3:'确认中',
                   4:'执行中',
                   5:'用户确认中',
                   6:'审核不通过,等待用户确认',
                   7:'确认不通过,等待用户确认',
                   8:'用户确认不通过,等待执行重做',
                   9:'已关闭'}

def getusers():
    all_user = Users.objects.all()
    data_user = []
    for user in all_user:
        tmp_record = {'id':user.u_id,'username':user.u_name,'engname':user.u_enname,'email':user.u_email,'role':user.u_role,'purview':user.u_purview,'status':user.u_status}
        data_user.append(tmp_record)

    return data_user

def ticketload(request,deftype,user_login):

    load_search = request.GET.get("_search",'')
    load_nd = int(request.GET.get("nd",''))
    load_rows = int(request.GET.get("rows",''))
    load_page = int(request.GET.get("page",''))
    load_sidx = str(request.GET.get("sidx",''))
    load_sord = str(request.GET.get("sord",''))
    len_min = load_page*load_rows - load_rows
    len_max = load_page*load_rows

    ## 
    if not load_sidx:
        load_sidx = "-ticket_id"
    if load_sord == "desc":
        load_sidx = "-"+load_sidx

    ## 工单记录(登陆用户)
    
    ### myticket
    if str(deftype) == "myticket":
        tickets_records = Ticket_Tickets.objects.filter(ticket_creator=user_login).exclude(ticket_status=9).order_by(load_sidx)

    ## mytask
    elif str(deftype) == "mytask":
        tickets_records = Ticket_Tickets.objects.filter(Q(ticket_executor=user_login,ticket_status=3)|Q(ticket_executor=user_login,ticket_status=4)|Q(ticket_creator=user_login,ticket_status=5)).order_by(load_sidx)

    ## mycheck
    elif str(deftype) == "mycheck":
        tickets_records = []
        user_login_tickets = Ticket_Tickets.objects.filter(tickets_users__users__exact=user_login,tickets_users__status__exact=1,ticket_status=2).order_by(load_sidx)
        for user_login_ticket in user_login_tickets:
            ticket_checkleader = Tickets_Users.objects.filter(ticket_tickets=user_login_ticket,status=1).order_by("tu_id")
            if ticket_checkleader[0].users.u_id == user_login.u_id:
                tickets_records.append(user_login_ticket)

    ## tickethistory
    else:
        tickets_records = Ticket_Tickets.objects.all().order_by(load_sidx)

    load_data = {"total":"0","page":str(load_page),"records":"0","data":[]}
    load_data['records'] = str(len(tickets_records))    ## rows
    load_data['total'] = str(len(tickets_records) / int(load_rows) + 1 )  ## pages


    for tickets_record in tickets_records[len_min:len_max]:
        ## 工单审核人名单
        ticket_checkleader = Tickets_Users.objects.filter(ticket_tickets=tickets_record,status=1).order_by("tu_id")

        ## 工单当前处理人
        ## 如果是保存状态,当前处理人为创建者
        ## 如果审核完毕，当前处理人为工单执行者
        if tickets_record.ticket_status == 1 or tickets_record.ticket_status == 5:
            opr_name = tickets_record.ticket_creator.u_name
        elif tickets_record.ticket_status == 9:
            opr_name = tickets_record.ticket_creator.u_name+"(已关闭)"
        elif len(ticket_checkleader) == 0:
            opr_name = tickets_record.ticket_executor.u_name
        else:
            opr_name = ticket_checkleader[0].users.u_name


        load_data['data'].append({'ticket_id':tickets_record.ticket_id,
                              'ticket_title':tickets_record.ticket_title,
                              'ticket_type':tickets_record.ticket_type.type_name,
                              'ticket_creator':tickets_record.ticket_creator.u_name,
                              'opr':opr_name,
                              'ticket_status':G_TICKET_STATUS[tickets_record.ticket_status],
                              'ticket_ctime':str(tickets_record.ticket_ctime),
                              })
    return load_data

def ticketview(request,deftype,user_login):
    ticketid = request.GET.get('ticketid','')
    ### myticket
    if str(deftype) == "myticket":
        tickets_record = Ticket_Tickets.objects.get(ticket_id=ticketid,ticket_creator=user_login)

    ## mytask
    elif str(deftype) == "mytask":
        tickets_record = Ticket_Tickets.objects.get(Q(ticket_executor=user_login,ticket_status=3)|Q(ticket_executor=user_login,ticket_status=4)|Q(ticket_creator=user_login,ticket_status=5))
 
    ## mycheck
    elif str(deftype) == "mycheck":
        tickets_record = Ticket_Tickets.objects.get(ticket_id=ticketid,ticket_checkleader=user_login)
 
    ## tickethistory
    else:
        tickets_record = Ticket_Tickets.objects.get(ticket_id=ticketid)

    ## 工单审核人名单
    #ticket_checkleader = Users.objects.filter(tickets_users__ticket_tickets__exact=tickets_record)
    ticket_checkleader = Tickets_Users.objects.filter(ticket_tickets=tickets_record).order_by("tu_id")

    ## 工单审核名单
    checkleader_record = []
    for checkleader_id in ticket_checkleader:
        checkleader_record.append(checkleader_id.users.u_name)

    if tickets_record.ticket_status == 5:
        checkleader_record.append(tickets_record.ticket_creator.u_name)

    tickets_info = {'ticket_id':tickets_record.ticket_id,
                          'ticket_title':tickets_record.ticket_title,
                          'ticket_type':tickets_record.ticket_type.type_name,
                          'ticket_creator':tickets_record.ticket_creator.u_name,
                          'ticket_checkleader':checkleader_record,
                          'ticket_executor':tickets_record.ticket_executor.u_name,
                          'ticket_status':tickets_record.ticket_status,
                          'ticket_ctime':str(tickets_record.ticket_ctime),
                          'ticket_require':tickets_record.ticket_require
                          }

    all_operating = Ticket_Operating.objects.filter(ticket_tickets=tickets_record).order_by('operating_id')
    all_reply = Ticket_Reply.objects.filter(ticket_tickets=tickets_record).order_by('reply_id')
    operating_info = []
    for operating in all_operating:
        tmp_operating = {'operating_id':operating.operating_id,
                         'operating_operator':operating.operating_operator.u_name,
                         'operating_type':operating.operating_type,
                         'operating_ctime':str(operating.operating_ctime),
                         'operating_content':operating.operating_content
                        }
        operating_info.append(tmp_operating)

    reply_info = [] 
    for reply in all_reply:
        tmp_reply = {'reply_id':reply.reply_id,
                     'reply_author':reply.reply_author.u_name,
                     'reply_content':reply.reply_content,
                     'reply_ctime':str(reply.reply_ctime),
                     'reply_mtime':str(reply.reply_mtime)
                    }
        reply_info.append(tmp_reply)


    return {'tickets_info':tickets_info,'operating_info':operating_info,'reply_info':reply_info}

def ticketcount(user_login):
    ### myticket
    myticketcount = Ticket_Tickets.objects.filter(ticket_creator=user_login).exclude(ticket_status=9).count()

    ## mytask
    mytaskcount = Ticket_Tickets.objects.filter(Q(ticket_executor=user_login,ticket_status=3)|Q(ticket_executor=user_login,ticket_status=4)|Q(ticket_creator=user_login,ticket_status=5)).count()

    ## mycheck
    mycheck_records = []
    user_login_tickets = Ticket_Tickets.objects.filter(tickets_users__users__exact=user_login,tickets_users__status__exact=1,ticket_status=2)
    for user_login_ticket in user_login_tickets:
        ticket_checkleader = Tickets_Users.objects.filter(ticket_tickets=user_login_ticket,status=1).order_by("tu_id")
        if ticket_checkleader[0].users.u_id == user_login.u_id:
            mycheck_records.append(user_login_ticket)
    mycheckcount = len(mycheck_records)

    totalcount = int(myticketcount)+int(mytaskcount)+int(mycheckcount)
    if mycheckcount == 0: mycheckcount=""
    if mytaskcount == 0: mytaskcount=""
    if myticketcount == 0: myticketcount=""
    if totalcount == 0: totalcount=""
    countdata={"totalcount":totalcount,"myticketcount":str(myticketcount),"mytaskcount":str(mytaskcount),"mycheckcount":str(mycheckcount)}
    return countdata

# Create your views here.
def index(request):
    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
    else:
        return HttpResponseRedirect("/login/")

    return render_to_response('index.html',locals())

def login(request):
    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        return HttpResponseRedirect("/")
    else:
        print "login fail"

    if str(request.method) == "POST":
        form_type = request.POST.get('type','')
        if form_type == "login":
            engname = request.POST.get("engname",'')
            password = request.POST.get("password",'')
            
            try:
                check_login_user = Users.objects.get(u_enname=engname,u_password=password)
                if check_login_user:
                    request.session["session_u_id"] = check_login_user.u_id
                    return HttpResponseRedirect("/")
                else:
                    return HttpResponseRedirect("/login/")
            except users.DoesNotExist:
                return HttpResponseRedirect("/login/")
        else:
            pass
    return render_to_response('login.html',locals())

def logout(request):

    if request.session.get('session_u_id',default=None):
        del request.session["session_u_id"]

    return HttpResponseRedirect("/login/")

def departmentmanage(request):
    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
        if user_login.u_purview == 0:
            page_content = 0
        else:
            page_content = 1
            return render_to_response('department.html',locals())
    else:
        return HttpResponseRedirect("/login/")

    

    if request.method == 'GET' and request.GET.has_key('type'):
        if str(request.GET.get("type",'')) == "load":

            load_search = request.GET.get("_search",'')
            load_nd = int(request.GET.get("nd",''))
            load_rows = int(request.GET.get("rows",''))
            load_page = int(request.GET.get("page",''))
            load_sidx = str(request.GET.get("sidx",''))
            load_sord = str(request.GET.get("sord",''))

            ##
            if not load_sidx:
                load_sidx = "-d_id"
            if load_sord == "desc":
                load_sidx = "-"+load_sidx
            load_data = {"total":"0","page":str(load_page),"records":"0","data":[]}

            department_records = Department.objects.all()
            if department_records:
                load_data['records'] = str(len(department_records))
                load_data['total'] = str(len(department_records) / int(load_rows) + 1 )  ## pages

                len_min = load_page*load_rows - load_rows
                len_max = load_page*load_rows

                for department_record in department_records[len_min:len_max]:
                    tmp_record = {}
                    tmp_record['d_id'] = department_record.d_id
                    tmp_record['d_name'] = department_record.d_name
                    tmp_record['d_enname'] = department_record.d_enname
                    tmp_record['d_ctime'] = str(department_record.d_ctime)
                    tmp_record['d_mtime'] = str(department_record.d_mtime)
                    load_data['data'].append(tmp_record)

            return HttpResponse(json.dumps(load_data))

        elif str(request.GET.get("type",'')) == "search":
            search_name = request.GET.get("search_name",'')

            load_search = request.GET.get("_search",'')
            load_nd = int(request.GET.get("nd",''))
            load_rows = int(request.GET.get("rows",''))
            load_page = int(request.GET.get("page",''))
            load_sidx = str(request.GET.get("sidx",''))
            load_sord = str(request.GET.get("sord",''))

            ##
            if not load_sidx:
                load_sidx = "-d_id"

            if load_sord == "desc":
                load_sidx = "-"+load_sidx

            load_data = {"total":"0","page":str(load_page),"records":"0","data":[]}

            department_records = Department.objects.filter(d_name__icontains=search_name)
            if department_records:
                load_data['records'] = str(len(department_records))
                load_data['total'] = str(len(department_records) / int(load_rows) + 1 )  ## pages

                len_min = load_page*load_rows - load_rows
                len_max = load_page*load_rows

                for department_record in department_records[len_min:len_max]:
                    tmp_record = {}
                    tmp_record['d_id'] = department_record.d_id
                    tmp_record['d_name'] = department_record.d_name
                    tmp_record['d_enname'] = department_record.d_enname
                    tmp_record['d_ctime'] = str(department_record.d_ctime)
                    tmp_record['d_mtime'] = str(department_record.d_mtime)
                    load_data['data'].append(tmp_record)

            return HttpResponse(json.dumps(load_data))

        else:
            pass

    elif request.method == 'POST' and request.POST.has_key('oper'):
        return_data = {'status':0,'msg':""}
        if str(request.POST.get('oper','')) == "add":
            d_name = request.POST.get('d_name','')
            d_enname = request.POST.get('d_enname','')

            if d_name and d_enname:
                check_name = Department.objects.filter(d_name=d_name)
                check_enname = Department.objects.filter(d_enname=d_enname)
                if check_name:
                    return_data = {'status':1,'msg':str(d_name)+" already exists!"}
                    return HttpResponse(json.dumps(return_data))
                if check_enname:
                    return_data = {'status':1,'msg':str(d_enname)+" already exists!"}
                    return HttpResponse(json.dumps(return_data))

                add_department = Department(d_name=d_name,d_enname=d_enname)
                add_department.save()
            else:
                return_data = {'status':1,'msg':""}

            return HttpResponse(json.dumps(return_data))
        elif str(request.POST.get('oper','')) == "edit":
            d_id = int(request.POST.get('id',''))
            d_name = request.POST.get('d_name','')
            d_enname = request.POST.get('d_enname','')

            if d_name and d_enname:
                check_name = Department.objects.filter(d_name=d_name).exclude(d_id=d_id)
                check_enname = Department.objects.filter(d_enname=d_enname).exclude(d_id=d_id)
                if check_name:
                    return_data = {'status':1,'msg':str(d_name)+" already exists!"}
                    return HttpResponse(json.dumps(return_data))
                if check_enname:
                    return_data = {'status':1,'msg':str(d_enname)+" already exists!"}
                    return HttpResponse(json.dumps(return_data))

                Department.objects.filter(d_id=d_id).update(d_name=d_name,d_enname=d_enname)
            else:
                return_data = {'status':1,'msg':""}

            return HttpResponse(json.dumps(return_data))
        elif str(request.POST.get('oper','')) == "del":
            d_id = int(request.POST.get('id',''))
            Department.objects.filter(d_id=d_id).delete()
        else:
            for key in request.POST:
                print key,request.POST.get(key,'')

    elif request.method == 'POST' and request.POST.has_key('type'):
        if request.POST.get('type','')=="getdepartment":
            return_data = {'status':0,'data':""}
            department_records = Department.objects.all()
            if department_records:
                department_str="" #组合成适用于编辑框的select格式
                for department_record in department_records:
                    if department_str:
                        department_str = department_str+";"+str(department_record.d_id)+":"+str(department_record.d_name)
                    else:
                        department_str = str(department_record.d_id)+":"+str(department_record.d_name)
                return_data['data'] = department_str
                print return_data['data']
            return HttpResponse(json.dumps(return_data))

    else:
        print request.method

    return render_to_response('department.html',locals())

def usercenter(request):

    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
        if user_login.u_purview == 0:
            page_content = 0
        else:
            page_content = 2
            return render_to_response('users.html',locals())
    else:
        return HttpResponseRedirect("/login/")

    role_dic = {1:"普通用户",2:"部门负责人"}

    page_content = 0
    if request.method == 'GET' and request.GET.has_key('type'):
        if str(request.GET.get("type",'')) == "load":

            load_search = request.GET.get("_search",'')
            load_nd = int(request.GET.get("nd",''))
            load_rows = int(request.GET.get("rows",''))
            load_page = int(request.GET.get("page",''))
            load_sidx = str(request.GET.get("sidx",''))
            load_sord = str(request.GET.get("sord",''))

            ##
            if not load_sidx:
                load_sidx = "-u_id"

            if load_sord == "desc":
                load_sidx = "-"+load_sidx

            load_data = {"total":"0","page":str(load_page),"records":"0","data":[]}

            users_records = Users.objects.all()
            if users_records:
                load_data['records'] = str(len(users_records))
                load_data['total'] = str(len(users_records) / int(load_rows) + 1 )  ## pages

                len_min = load_page*load_rows - load_rows
                len_max = load_page*load_rows

                for users_record in users_records[len_min:len_max]:
                    ## 反向查询
                    department_record = Department.objects.filter(users__u_id__exact=users_record.u_id)

                    tmp_record = {}
                    tmp_record['u_id'] = users_record.u_id
                    tmp_record['u_name'] = users_record.u_name
                    tmp_record['u_enname'] = users_record.u_enname
                    tmp_record['u_email'] = users_record.u_email
                    tmp_record['u_role'] = role_dic[users_record.u_role]
                    tmp_record['u_department'] = department_record[0].d_name
                    tmp_record['u_ctime'] = str(users_record.u_ctime)
                    tmp_record['u_mtime'] = str(users_record.u_mtime)
                    load_data['data'].append(tmp_record)
            return HttpResponse(json.dumps(load_data))

        elif str(request.GET.get("type",'')) == "search":
            search_name = request.GET.get("search_name",'')

            load_search = request.GET.get("_search",'')
            load_nd = int(request.GET.get("nd",''))
            load_rows = int(request.GET.get("rows",''))
            load_page = int(request.GET.get("page",''))
            load_sidx = str(request.GET.get("sidx",''))
            load_sord = str(request.GET.get("sord",''))

            ##
            if not load_sidx:
                load_sidx = "-u_id"

            if load_sord == "desc":
                load_sidx = "-"+load_sidx

            load_data = {"total":"0","page":str(load_page),"records":"0","data":[]}

            users_records = Users.objects.filter(u_name__icontains=search_name)
            if users_records:
                load_data['records'] = str(len(users_records))
                load_data['total'] = str(len(users_records) / int(load_rows) + 1 )  ## pages

                len_min = load_page*load_rows - load_rows
                len_max = load_page*load_rows

                for users_record in users_records[len_min:len_max]:
                    ## 反向查询
                    department_record = Department.objects.filter(users__u_id__exact=users_record.u_id)

                    tmp_record = {}
                    tmp_record['u_id'] = users_record.u_id
                    tmp_record['u_name'] = users_record.u_name
                    tmp_record['u_enname'] = users_record.u_enname
                    tmp_record['u_email'] = users_record.u_email
                    tmp_record['u_role'] = role_dic[users_record.u_role]
                    tmp_record['u_department'] = department_record[0].d_name
                    tmp_record['u_ctime'] = str(users_record.u_ctime)
                    tmp_record['u_mtime'] = str(users_record.u_mtime)
                    load_data['data'].append(tmp_record)

            return HttpResponse(json.dumps(load_data))

        elif str(request.GET.get("type",'')) == "profile":

            
            uid = request.GET.get('uid','')
            if str(user_login.u_id) == str(uid):
                print "ok"
                page_content = 1
            else:
                print "xxx"
                page_content = 0

            return render_to_response('users.html',locals())


        else:
            pass 

    elif request.method == 'POST' and request.POST.has_key('oper'):

        return_data = {'status':0,'msg':""}
        if str(request.POST.get('oper','')) == "add":
            u_name = request.POST.get('u_name','')
            u_enname = request.POST.get('u_enname','')
            u_role = int(request.POST.get('u_role',''))
            d_id = request.POST.get('u_department','')
            u_email = str(u_enname)+"@huangdc.com"
            u_password = "123456"

            department_record = Department.objects.get(d_id=d_id)
            if u_name and u_enname:
                check_enname = Users.objects.filter(u_enname=u_enname)
                if check_enname:
                    return_data = {'status':1,'msg':str(u_enname)+" already exists!"}
                    return HttpResponse(json.dumps(return_data))
                if str(u_role) == "3":
                    check_role_3 = Users.objects.filter(department=department_record,u_role=3)
                    if check_role_3:
                        return_data = {'status':1,'msg':"department role already exists!"}
                        return HttpResponse(json.dumps(return_data)) 

                add_user = Users(u_name=u_name,u_enname=u_enname,u_role=u_role,department=department_record,u_email=u_email,u_password=u_password)
                add_user.save()
            else:
                return_data = {'status':1,'msg':""}

            return HttpResponse(json.dumps(return_data))
        elif str(request.POST.get('oper','')) == "edit":
            u_id = request.POST.get('id','')
            u_name = request.POST.get('u_name','')
            u_enname = request.POST.get('u_enname','')
            u_role = int(request.POST.get('u_role',''))
            d_id = request.POST.get('u_department','')
            u_email = str(u_enname)+"@huangdc.com"

            department_record = Department.objects.get(d_id=d_id)
            if u_name and u_enname:
                check_enname = Users.objects.filter(u_enname=u_enname).exclude(u_id=u_id)
                if check_enname:
                    return_data = {'status':1,'msg':str(u_enname)+" already exists!"}
                    return HttpResponse(json.dumps(return_data))
                if str(u_role) == "2":
                    check_role_3 = Users.objects.filter(department=department_record,u_role=2).exclude(u_id=u_id)
                    if check_role_3:
                        return_data = {'status':1,'msg':"department role already exists!"}
                        return HttpResponse(json.dumps(return_data)) 

                Users.objects.filter(u_id=u_id).update(u_name=u_name,u_enname=u_enname,u_role=u_role,department=department_record,u_email=u_email)

            else:
                return_data = {'status':1,'msg':""}

            return HttpResponse(json.dumps(return_data))
        elif str(request.POST.get('oper','')) == "del":
            u_id = int(request.POST.get('id',''))
            Users.objects.filter(u_id=u_id).update(u_status=False)

        else:
            for key in request.POST:
                print key,request.POST.get(key,'')
    elif request.method == "POST" and request.POST.has_key('type'):

        if str(request.POST.get('type','')) == "getcheckleader":
            return HttpResponse(json.dumps(getusers()))
        else:
            pass
    else:
        print request.method

    print "xxxxxxxxx"

    return render_to_response('users.html',locals())

###########################################
def tickettype(request):
    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
        if user_login.u_purview == 0:
            page_content = 0
        else:
            page_content = 1
            return render_to_response('tickettype.html',locals())
    else:
        return HttpResponseRedirect("/login/")

    users_dic = getusers()

    if request.method == 'GET' and request.GET.has_key('type'):
        # load
        if str(request.GET.get("type",'')) == "load":
            print "type: load"
            for key in request.GET:
                print key,request.GET.get(key,'')
            load_search = request.GET.get("_search",'')
            load_nd = int(request.GET.get("nd",''))
            load_rows = int(request.GET.get("rows",''))
            load_page = int(request.GET.get("page",''))
            load_sidx = str(request.GET.get("sidx",''))
            load_sord = str(request.GET.get("sord",''))

            ##
            if not load_sidx:
                load_sidx = "-type_id"

            if load_sord == "desc":
                load_sidx = "-"+load_sidx

            type_records = Ticket_Type.objects.filter(type_status=True).order_by(load_sidx)


            load_data = {"total":"0","page":str(load_page),"records":"0","data":[]}
            load_data['records'] = str(len(type_records))
            load_data['total'] = str(len(type_records) / int(load_rows) + 1 )  ## pages

            len_min = load_page*load_rows - load_rows
            len_max = load_page*load_rows
            
            for type_record in type_records[len_min:len_max]:
                tmp_record = {}
                tmp_record['type_id'] = type_record.type_id
                tmp_record['type_name'] = type_record.type_name
                tmp_record['type_ctime'] = str(type_record.type_ctime)
                tmp_record['type_mtime'] = str(type_record.type_mtime)


                #反向查询   ing
                user_record = Users.objects.filter(ticket_type__type_id__exact=type_record.type_id)
                tmp_record['type_executor'] = user_record[0].u_name

                ###################################################################################
    
                checkleader_list = str(type_record.type_checkleader).split(',')
                checkleader_str = ""
                for checkleader_id  in checkleader_list:
                    if checkleader_id == "-1":
                        checkleader_name = "默认上级"
                    else:
                        user_record = Users.objects.get(u_id=checkleader_id)
                        checkleader_name = user_record.u_name

                    if checkleader_str == "":
                        checkleader_str = "<span> "+checkleader_name+" </span>"
                    else:
                        checkleader_str = checkleader_str+"<span class='glyphicon glyphicon-arrow-right'></span><span> "+checkleader_name+" </span>"
                tmp_record['type_checkleader'] = checkleader_str


                load_data['data'].append(tmp_record)

            return HttpResponse(json.dumps(load_data))
        
        else:
            print "type: 'xxxxxxxxxx'"

    if request.method == "POST" and request.POST.has_key('type'):

        if str(request.POST.get('type','')) == "getcheckleader":
            #checkleaders = {'799':'黄东葱','899':'黄东东'}
            return HttpResponse(json.dumps(users_dic))

        elif str(request.POST.get('type','')) == "addtickettype":
            #{'type':"addtickettype",'ticket_type_name','ticket_type_executor','checkleader'}
            ticket_type_name = request.POST.get('ticket_type_name','')
            uid = request.POST.get('ticket_type_executor','')
            checkleader = str(request.POST.get('checkleader','')) 
            ##　checkleader 格式 "'id','id'"

            print "ticket_type_name , executor_uid , checkleader",ticket_type_name,uid,checkleader

            ticket_type_executor = Users.objects.get(u_id=uid)

            ticket_record = Ticket_Type.objects.filter(type_name=ticket_type_name)
            if ticket_record:
                pass
            else:
                add_ticket_type = Ticket_Type(type_name = ticket_type_name,type_executor = ticket_type_executor,type_checkleader = checkleader)
                add_ticket_type.save()

            return_data = {"ok":"ok"}
            return HttpResponse(json.dumps(return_data))
        elif str(request.POST.get('type','')) == "gettyperecord":
            ticket_type_id = request.POST.get('ticket_type_id','')
            ticket_record = Ticket_Type.objects.get(type_id=ticket_type_id)
            data_record = {}
            data_record['type_id']=ticket_record.type_id
            data_record['type_name']=ticket_record.type_name

            user_record = Users.objects.filter(ticket_type__type_id__exact=ticket_type_id)
            data_record['type_executor'] = str(user_record[0].u_id)+"_"+user_record[0].u_name+"("+user_record[0].u_enname+")"

            data_record['type_checkleader'] = []
            for u_id in str(ticket_record.type_checkleader).split(','):
                if u_id == "-1":
                    data_record['type_checkleader'].append("-1_默认上级")
                else:
                    user_record = Users.objects.get(u_id=u_id)
                    data_record['type_checkleader'].append(str(user_record.u_id)+"_"+str(user_record.u_name)+"("+str(user_record.u_enname)+")")

            data_record['users'] = users_dic

            return HttpResponse(json.dumps(data_record))
        elif str(request.POST.get('type','')) == "edittickettype":
            #{'type':"addtickettype",'ticket_type_name','ticket_type_executor','checkleader'}
            ticket_type_id = request.POST.get('ticket_type_id','')
            ticket_type_name = request.POST.get('ticket_type_name','')
            u_id = request.POST.get('ticket_type_executor','')
            checkleader = str(request.POST.get('checkleader',''))

            ticket_type_executor = Users.objects.get(u_id=u_id)

            print "edit var_checkleader:",checkleader
            print ticket_type_id,ticket_type_name
            Ticket_Type.objects.filter(type_id=ticket_type_id).update(type_name = ticket_type_name,type_executor = ticket_type_executor,type_checkleader = checkleader)

            return_data = {"ok":"ok"}
            return HttpResponse(json.dumps(return_data))

        elif str(request.POST.get('type','')) == "deltickettype":
            type_id_list = request.POST.get('type_id_list','')
            print "del type_id_list:",type_id_list
            for typeid in type_id_list.split(','):
                Ticket_Type.objects.filter(type_id=typeid).update(type_status=False)

            return_data = {"ok":"ok"}
            return HttpResponse(json.dumps(return_data))
        else:
            pass
        
    return render_to_response('tickettype.html',locals())

def ticketadd(request):

    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
    else:
        return HttpResponseRedirect("/login/")

    # 获取全部状态为True的工单类型
    type_records = Ticket_Type.objects.filter(type_status=True)
    type_records_list = []
    if type_records:
        for type_record in type_records:
            tmp_record = {}
            tmp_record['type_id'] = type_record.type_id
            tmp_record['type_name'] = type_record.type_name
            type_records_list.append(tmp_record)

    users_dic = getusers()



    if str(request.method) == "POST":
        ## 生成一个唯一的 ticket_id
        new_ticket_id = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

        if request.POST.get('type','') == "addneed":

            type_id = request.POST.get('tickettype','')
            needtitle = request.POST.get('needtitle','')
            needrequire = request.POST.get('needrequire','')

            ## 查询工单类型记录
            ticket_type_record = Ticket_Type.objects.get(type_id=type_id)
 
            ## 获取审核人个数，及判断是否有默认上级,有则替换为部门负责人
            type_checkleader_list = str(ticket_type_record.type_checkleader).split(',')
            print "type_checkleader_list",str(type_checkleader_list)
            if "-1" in type_checkleader_list:
                deafult_index = int(type_checkleader_list.index("-1"))
                deafult_checkleader = Users.objects.get(department=user_login.department,u_role=2)
                if deafult_checkleader:
                    type_checkleader_list[deafult_index] = str(deafult_checkleader.u_id)
                else:
                    type_checkleader_list.remove("-1")
            checkleader_sum = len(type_checkleader_list)
            print "type_checkleader_list",str(type_checkleader_list)
            #type_checkleader = ','.join(type_checkleader_list)

            ### 反向查询工单类型处理人记录
            #ticket_executor_record = Users.objects.filter(ticket_type__type_id__exact=type_id)

            ## 判断是提交，还保存
            ticket_status = 1
            if "submit" in request.POST:
                ticket_status = 2

            ## 添加一条记录
            add_ticket_entries = Ticket_Tickets(ticket_id=new_ticket_id,
                             ticket_title = str(needtitle),
                             ticket_type = ticket_type_record,
                             ticket_executor = ticket_type_record.type_executor,
                             #ticket_checkleader = type_checkleader,
                             ticket_checksum = checkleader_sum,
                             ticket_require = needrequire,
                             ticket_creator = user_login,
                             ticket_result = "",
                             ticket_rtime = datetime.datetime.now(),
                             ticket_status = ticket_status,                        
                             )
            add_ticket_entries.save()

            for checkleader_uid in type_checkleader_list:
                print "checkleader_uid",str(checkleader_uid)
                checkleader_user_record = Users.objects.get(u_id = checkleader_uid)
                Tickets_Users(ticket_tickets=add_ticket_entries,users=checkleader_user_record,status=1).save()

            new_ticket = Ticket_Tickets.objects.get(ticket_id=new_ticket_id)

            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="创建工单",
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()

        return HttpResponseRedirect("/myticket/")

        #if form_type == "login":
    return render_to_response('ticketadd.html',locals())

def myticket(request):
    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
    else:
        return HttpResponseRedirect("/login/")

    page_content = 0
    if request.method == 'GET' and request.GET.has_key('type'):

        # load
        if str(request.GET.get("type",'')) == "load":
            load_data = ticketload(request,"myticket",user_login)
            return HttpResponse(json.dumps(load_data))

        # view
        elif str(request.GET.get('type','')) == "view":
            page_content = 1
            all_info= ticketview(request,"myticket",user_login)
            tickets_info = all_info['tickets_info']
            operating_info = all_info['operating_info']
            reply_info = all_info['reply_info']
            return render_to_response('myticket.html',locals())

        else:
            print "type: ''"

    elif request.method == 'POST' and request.POST.has_key('type'):
        print "x",request.method
        return_data = {'status':0,'msg':""}
        if request.POST.get('type','') == "modifyticket":
            ticketid = request.POST.get('needticketid','') 
            require = request.POST.get('needrequire','') 
            print "ticketid:",ticketid
            if "submit" in request.POST:
                Ticket_Tickets.objects.filter(ticket_id=ticketid).update(ticket_require=str(require),ticket_status=2)
                operating_type = "提交工单"
            else:
                Ticket_Tickets.objects.filter(ticket_id=ticketid).update(ticket_require=str(require),ticket_status=1)
                operating_type = "修改工单"

            new_ticket = Ticket_Tickets.objects.get(ticket_id=ticketid)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type=operating_type,
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()
            return HttpResponse(json.dumps(return_data))

        elif request.POST.get('type','') == "cancelticket":
            
            ticketid = request.POST.get('ticket_id','')
            Ticket_Tickets.objects.filter(ticket_id=ticketid).update(ticket_status=1)
            cancel_ticket = Ticket_Tickets.objects.get(ticket_id=ticketid)
            Tickets_Users.objects.filter(ticket_tickets=cancel_ticket).update(status=1)

            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="撤销工单",
                                             operating_content="",
                                             ticket_tickets=cancel_ticket
                                            )
            add_operating.save()

            return HttpResponse(json.dumps(return_data))
        elif request.POST.get('type','') == "deleteticket":

            ticketid = request.POST.get('ticket_id','')
            Ticket_Tickets.objects.filter(ticket_id=ticketid).delete()
            new_ticket = Ticket_Tickets.objects.get(ticket_id=ticketid)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="删除工单",
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()
            return HttpResponse(json.dumps(return_data))

        elif request.POST.get('type','') == "sendmessage":
            message = request.POST.get('message','')
            ticket_id = request.POST.get('ticket_id','')
            ticket_record = Ticket_Tickets.objects.get(ticket_id=ticket_id)
            print "message",message
            add_reply = Ticket_Reply(
                     reply_author=user_login,
                     reply_content=str(message),
                     ticket_tickets=ticket_record
                    )
            add_reply.save()
            return HttpResponse(json.dumps(return_data))
        else:
            print "messagxxxxx"


    return render_to_response('myticket.html',locals())

def mytask(request):
    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
    else:
        return HttpResponseRedirect("/login/")


    page_content = 0
    if request.method == 'GET' and request.GET.has_key('type'):

        # load
        if str(request.GET.get("type",'')) == "load":
            load_data = ticketload(request,"mytask",user_login)
            return HttpResponse(json.dumps(load_data))

        # search
        elif str(request.GET.get("type",'')) == "search":
            print "type: search"
            #return HttpResponse(json.dumps(njson2))

        # view
        elif str(request.GET.get('type','')) == "view":
            page_content = 1
            all_info= ticketview(request,"mytask",user_login)
            tickets_info = all_info['tickets_info']
            operating_info = all_info['operating_info']
            reply_info = all_info['reply_info']
            return render_to_response('mytask.html',locals())

        else:
            print "type: ''"

    elif request.method == 'POST' and request.POST.has_key('type'):
        print "x",request.method
        return_data = {'status':0,'msg':""}
        if request.POST.get('type','') == "forwarding":
            print "forwardingforwarding"
            ticket_id = str(request.POST.get("ticket_id",''))
            executor_uid = str(request.POST.get("executor_uid",''))

            switch_executor = Users.objects.get(u_id=executor_uid)
            Ticket_Tickets.objects.filter(ticket_id=ticket_id).update(ticket_executor=switch_executor)

            new_ticket = Ticket_Tickets.objects.get(ticket_id=ticket_id)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="转发处理",
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()
            return HttpResponse(json.dumps(return_data))

            return HttpResponse(json.dumps(return_data))
        elif request.POST.get('type','') == "execokticket":
            ticket_id = str(request.POST.get("ticket_id",''))
            Ticket_Tickets.objects.filter(ticket_id=ticket_id).update(ticket_status=4)
            new_ticket = Ticket_Tickets.objects.get(ticket_id=ticket_id)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="确认执行",
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()
            return HttpResponse(json.dumps(return_data))
        elif request.POST.get('type','') == "execnoticket":
            ticket_id = str(request.POST.get("ticket_id",''))
            Ticket_Tickets.objects.filter(ticket_id=ticket_id).update(ticket_status=1)
            new_ticket = Ticket_Tickets.objects.get(ticket_id=ticket_id)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="退回工单",
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()
            return HttpResponse(json.dumps(return_data))

        elif request.POST.get('type','') == "ticketcomplete":
            ticketid = request.POST.get('needticketid','') 
            require = str(request.POST.get('needrequire',''))
            result = str(request.POST.get('needresult',''))
            print "ticketid:",ticketid
            for key in request.POST:
                print key,"xxx",request.POST.get(key,'')
            if "complete" in request.POST:
                Ticket_Tickets.objects.filter(ticket_id=ticketid).update(ticket_require=require,ticket_result=result,ticket_status=5)
            else:
                Ticket_Tickets.objects.filter(ticket_id=ticketid).update(ticket_require=require,ticket_result=result,ticket_status=4)
            new_ticket = Ticket_Tickets.objects.get(ticket_id=ticketid)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="完成工单",
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()
        elif request.POST.get('type','') == "ticketclose":
            ticketid = request.POST.get('needticketid','') 
            require = str(request.POST.get('needrequire',''))
            result = str(request.POST.get('needresult',''))
            print "ticketid:",ticketid
            if "close" in request.POST:
                Ticket_Tickets.objects.filter(ticket_id=ticketid).update(ticket_require=require,ticket_result=result,ticket_status=9)
            else:
                Ticket_Tickets.objects.filter(ticket_id=ticketid).update(ticket_require=require,ticket_result=result,ticket_status=3)
            new_ticket = Ticket_Tickets.objects.get(ticket_id=ticketid)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="关闭工单",
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()
        else:
            pass

    return render_to_response('mytask.html',locals())

def mycheck(request):
    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
    else:
        return HttpResponseRedirect("/login/")

    page_content = 0
    if request.method == 'GET' and request.GET.has_key('type'):

        # load
        if str(request.GET.get("type",'')) == "load":
            load_data = ticketload(request,"mycheck",user_login)
            return HttpResponse(json.dumps(load_data))

        
        # search
        elif str(request.GET.get("type",'')) == "search":
            print "type: search"
            #return HttpResponse(json.dumps(njson2))

        # view
        elif str(request.GET.get('type','')) == "view":
            page_content = 1
            all_info= ticketview(request,"mycheck",user_login)
            tickets_info = all_info['tickets_info']
            operating_info = all_info['operating_info']
            reply_info = all_info['reply_info']
            return render_to_response('mycheck.html',locals())

        else:
            print "type: ''"

    elif request.method == 'POST' and request.POST.has_key('type'):
        print "x",request.method
        return_data = {'status':0,'msg':""}
        if request.POST.get('type','') == "checkokticket":
            ticket_id = str(request.POST.get("ticket_id",''))
            print "checkcheckcheckcheckcheckcheckcheckcheckcheckcheckx"

            ticket_record = Ticket_Tickets.objects.get(ticket_id=ticket_id)

            Tickets_Users.objects.filter(ticket_tickets=ticket_record,users=user_login).update(status=0)
            ticket_checkleader = Tickets_Users.objects.filter(ticket_tickets=ticket_record,status=1)
            if not ticket_checkleader:
                Ticket_Tickets.objects.filter(ticket_id=ticket_id).update(ticket_status=3)

            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="审核通过",
                                             operating_content="",
                                             ticket_tickets=ticket_record
                                            )
            add_operating.save()

            return HttpResponse(json.dumps(return_data))
        elif request.POST.get('type','') == "checknoticket":
            ticket_id = str(request.POST.get("ticket_id",''))
            Ticket_Tickets.objects.filter(ticket_id=ticket_id).update(ticket_status=1)
            new_ticket = Ticket_Tickets.objects.get(ticket_id=ticket_id)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="审核不通过",
                                             operating_content="",
                                             ticket_tickets=new_ticket
                                            )
            add_operating.save()
            return HttpResponse(json.dumps(return_data))

        elif request.POST.get('type','') == "forwarding":
            print "forwardingforwarding"
            ticket_id = str(request.POST.get("ticket_id",''))
            checkleader_uid = str(request.POST.get("checkleader_uid",''))
            switch_checkleader = Users.objects.get(u_id=checkleader_uid)
            switch_tickets = Ticket_Tickets.objects.get(ticket_id=ticket_id)

            Tickets_Users.objects.filter(ticket_tickets=switch_tickets,users=user_login).update(users=switch_checkleader)
            add_operating = Ticket_Operating(operating_operator=user_login,
                                             operating_type="转发审核",
                                             operating_content="",
                                             ticket_tickets=switch_tickets
                                            )
            add_operating.save()
            return HttpResponse(json.dumps(return_data))
        else:
            pass

    return render_to_response('mycheck.html',locals())

def tickethistory(request):
    if request.session.get('session_u_id',default=None):
        session_u_id = request.session.get('session_u_id')
        user_login = Users.objects.get(u_id=session_u_id)
        user_info = {'u_id':user_login.u_id,'u_name':user_login.u_name,'u_enname':user_login.u_enname,
                      'u_email':user_login.u_email,'u_role':user_login.u_role,'u_purview':user_login.u_purview,
                      'u_status':user_login.u_status
                      }
        count = ticketcount(user_login)
    else:
        return HttpResponseRedirect("/login/")


    page_content = 0
    if request.method == 'GET' and request.GET.has_key('type'):

        
        # load
        if str(request.GET.get("type",'')) == "load":
            load_data = ticketload(request,"tickethistory",user_login)
            return HttpResponse(json.dumps(load_data))
      
        # search
        elif str(request.GET.get("type",'')) == "search":
            print "type: search"
            #return HttpResponse(json.dumps(njson2))

        # view
        elif str(request.GET.get('type','')) == "view":
            page_content = 1
            all_info= ticketview(request,"tickethistory",user_login)
            tickets_info = all_info['tickets_info']
            operating_info = all_info['operating_info']
            reply_info = all_info['reply_info']
            return render_to_response('tickethistory.html',locals())

        else:
            print "type: ''"

    elif request.method == 'POST' and request.POST.has_key('type'):
        print "x",request.method

    return render_to_response('tickethistory.html',locals())
##########################################

def servertype(request):
    #return HttpResponse("xxxxxxxxx")
    #print req
    sjson = [ 
        {'id':"1",'name':"Desktop Computer",'note':"note",'stock':"Yes",'ship':"FedEx", 'sdate':"2007-12-03"},
        {'id':"2",'name':"Laptop",'note':"Long text ",'stock':"Yes",'ship':"InTime",'sdate':"2007-12-03"},
        {'id':"3",'name':"LCD Monitor",'note':"note3",'stock':"Yes",'ship':"TNT",'sdate':"2007-12-03"},
        {'id':"4",'name':"Speakers",'note':"note",'stock':"No",'ship':"ARAMEX",'sdate':"2007-12-03"},
        {'id':"5",'name':"Laser Printer",'note':"note2",'stock':"Yes",'ship':"FedEx",'sdate':"2007-12-03"},
        {'id':"6",'name':"Play Station",'note':"note3",'stock':"No", 'ship':"FedEx",'sdate':"2007-12-03"},
        {'id':"7",'name':"Mobile Telephone",'note':"note",'stock':"Yes",'ship':"ARAMEX",'sdate':"2007-12-03"}
    ]

    sjson2 = [ 
        {'id':"6",'name':"Play Station",'note':"note3",'stock':"No", 'ship':"FedEx",'sdate':"2007-12-03"},
        {'id':"7",'name':"Mobile Telephone",'note':"note",'stock':"Yes",'ship':"ARAMEX",'sdate':"2007-12-03"}
    ]   

    njson = {"total":"2","page":"1","records":"14","data":[
        {'id':"1",'type':"A1",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"单电源",'nic':"2",'diskhot':"Yes",'management':"Yes",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"2",'type':"A2",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"单电源",'nic':"2",'diskhot':"Yes",'management':"Yes",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"3",'type':"A3",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"单电源",'nic':"2",'diskhot':"No",'management':"Yes",'extranet':"No",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"4",'type':"B1",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"4",'diskhot':"No",'management':"Yes",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"5",'type':"B2",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"单电源",'nic':"3",'diskhot':"Yes",'management':"No",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"6",'type':"B3",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"2",'diskhot':"Yes",'management':"Yes",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"7",'type':"C1",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"4",'diskhot':"No",'management':"No",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"8",'type':"C2",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"4",'diskhot':"Yes",'management':"Yes",'extranet':"No",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"9",'type':"C3",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"单电源",'nic':"4",'diskhot':"No",'management':"No",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"10",'type':"D1",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"单电源",'nic':"1",'diskhot':"Yes",'management':"Yes",'extranet':"No",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"11",'type':"D2",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"3",'diskhot':"No",'management':"Yes",'extranet':"No",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"12",'type':"M1",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"4",'diskhot':"Yes",'management':"Yes",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"13",'type':"M2",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"单电源",'nic':"2",'diskhot':"No",'management':"Yes",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"14",'type':"M3",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"2",'diskhot':"Yes",'management':"Yes",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
    ]}


    njson2 = {"total":"2","page":"1","records":"2","data":[
        {'id':"11",'type':"D2",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"3",'diskhot':"No",'management':"Yes",'extranet':"No",'sdate':"2007-12-03",'scope':"scope1"},
        {'id':"12",'type':"M1",'cpu':"cpu1",'ram':"ram1",'disk':"disk1",'raid':"raid1",'power':"双电源",'nic':"4",'diskhot':"Yes",'management':"Yes",'extranet':"Yes",'sdate':"2007-12-03",'scope':"scope1"},
    ]}


    if request.method == 'GET' and request.GET.has_key('getdata'):
        if str(request.GET.get("getdata",'')) == "1":
            print "getdata 1"
            return HttpResponse(json.dumps(njson))
        if str(request.GET.get("getdata",'')) == "2":
            return HttpResponse(json.dumps(njson2))
    elif request.method == 'POST':
        print "x",request.method

    print "xxxxxxxxx"

    return render_to_response('servertype.html')
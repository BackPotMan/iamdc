
from flask import session
from ops.database.model import db,user

def userLogin():

    returnData = {'status': 1, 'uri': '', 'user': {}}
    if 'username' in session:
        username = session['username']
        userLogin = user.query.filter(user.name == username).first()
        if userLogin:
            returnData['user'] = {'id': userLogin.id,
                                  'name':userLogin.name,
                                  'cnname':userLogin.cnname,
                                  'department_id':userLogin.department_id,
                                  'leader':userLogin.leader.value
                                  }
            returnData['uri'] = "/"
            returnData['status'] = 0
        else:
            session.pop('username', None)
            returnData['uri'] = "/users/login/"
    else:
        returnData['uri'] = "/users/login/"

    return returnData

import random
from flask import Flask, render_template, redirect,url_for
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request
from google.auth.transport import requests
import datetime
from multiprocessing.sharedctypes import Value

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()


######################### Create and Retrieve UserInfo #########################
def createUserInfo(claims):
 entity_key = datastore_client.key('UserInfo', claims['email'])
 entity = datastore.Entity(key = entity_key)
 if "name" in claims.keys():
    ssName = claims["name"]
 else: 
    ssName = claims["email"]
 entity.update({
 'email': claims['email'],
 'name': ssName,
 'Taskboard_list': []
 })
 datastore_client.put(entity)

def retrieveUserInfo(claims):
 entity_key = datastore_client.key('UserInfo', claims['email'])
 entity = datastore_client.get(entity_key)
 return entity

def checkUserData():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    UserInfo = None
    addresses = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
        except ValueError as exc:
            error_message=str(exc)
    return claims
####################### Create and Retrieve Taskboards ###########################
def CreateTaskboard(claims, name):
    id = random.getrandbits(63)
    entity_key = datastore_client.key('Taskboard', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'name': name,
        'task_list': [],
        'user_list': [],
        'owner': claims['email'],
        'task_active': 0,
        'task_completed': 0,
        'currenttask_completed': 0,
        'total_task': 0
    })
    datastore_client.put(entity)
    addUserToTaskBoard(entity, claims['email'])
    return id

def retrieveSingleTaskBoard(id):
    entity_key = datastore_client.key('Taskboard', id)
    entity = datastore_client.get(entity_key)
    return entity

def retrieveTaskBoard(UserInfo):
   TaskBoard_id = UserInfo['Taskboard_list']
   TaskBoard_keys = []
   for i in range(len(TaskBoard_id)):
      TaskBoard_keys.append(datastore_client.key('Taskboard', TaskBoard_id[i]))
   TaskBoard_list = datastore_client.get_multi(TaskBoard_keys)
  
   return TaskBoard_list
####################### Binding Taskboard to User ###########################
def addTaskBoardToUser(UserInfo, id):
   TaskBoard_keys = UserInfo['Taskboard_list']
   TaskBoard_keys.append(id)
   UserInfo.update({
         'TaskBoard_list': TaskBoard_keys
   })
   datastore_client.put(UserInfo)






####################### Create and Retrieve Task ###########################

def createTask(claims, title, due_date, status, assigned):
    id = random.getrandbits(63)
    entity_key = datastore_client.key('Task', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'title' : title,
        'due_date' : due_date,
        'status': status,
        'assigned': assigned,
        'completed_time': None
    })
    datastore_client.put(entity)
    return id

def retrieveSingleTask(id):
    entity_key = datastore_client.key('Task', id)
    entity = datastore_client.get(entity_key)
    return entity

def retrieveTask(Taskboard):
   Task_id = Taskboard['task_list']
   Task_keys = []
   for i in range(len(Task_id)):
      Task_keys.append(datastore_client.key('Task', Task_id[i]))
   task_list = datastore_client.get_multi(Task_keys) 
   return task_list

####################### Binding Task to Taskboard ###########################

def addTaskToTaskBoard(Taskboard, id):
   Task_keys = Taskboard['task_list']
   Task_keys.append(id)
   Taskboard.update({
         'task_list': Task_keys
   })
   datastore_client.put(Taskboard)

###################### Name check function for check task name ###########################
def namecheck(Task_title, task_list):
    samename = False
    for Task in task_list:
        if Task_title == Task['title']:
            samename = True
    return samename 


####################### Binding User to Taskboard and Retrive  ###########################
def addUserToTaskBoard(Taskboard, email):
   user_keys = Taskboard['user_list']
   user_keys.append(email)
   Taskboard.update({
         'user_list': user_keys
   })
   datastore_client.put(Taskboard)

def retrieveUser(Taskboard):
   user_id = Taskboard['user_list']
   user_keys = []
   for i in range(len(user_id)):
      user_keys.append(datastore_client.key('UserInfo', user_id[i]))
   user_list = datastore_client.get_multi( user_keys)
  
   return user_list

####################### Function to check the Task Status  ###########################
def update_Taskstatus(Taskboard):
    Task = retrieveTask(Taskboard)
    task_active = 0
    task_completed = 0
    currenttask_completed = 0
    total_task = 0
    for Task in Task:
        
        if Task['status'] == "complete":
            task_completed = task_completed + 1
            if Task['currenttask_completed'].date() == datetime.datetime.now().date():
                currenttask_completed = currenttask_completed + 1
        else:
            task_active = task_active + 1
    total_task = task_active + task_completed
    Taskboard.update({
        'task_active': task_active,
        'task_completed': task_completed,
        'currenttask_completed': currenttask_completed,
        'total_task': total_task
    })
    datastore_client.put(Taskboard)

####################### Delete Board ###########################
def deleteBoard(Taskboard_id, UserInfo):
    Taskboard_key = datastore_client.key('Taskboard', Taskboard_id)
    datastore_client.delete(Taskboard_key)
    
    Taskboard_list = UserInfo['Taskboard_list']
    Taskboard_list.remove(Taskboard_id)
    UserInfo.update({
        'Taskboard_list' : Taskboard_list
    })
    datastore_client.put(UserInfo)

####################### Delete Task ###########################
def deleteTask(Taskboard_id, Task_id):
    Taskboard = retrieveSingleTaskBoard(Taskboard_id)
    Task_list_keys = Taskboard['task_list']
    Task_key = datastore_client.key('Task', Task_id)
    datastore_client.delete(Task_key)
    Task_list_keys.remove(Task_id)
    Taskboard.update({
        'task_list' : Task_list_keys
    })
    datastore_client.put(Taskboard)


def deleteUser(Taskboard_id, user):
    Taskboard = retrieveSingleTaskBoard(Taskboard_id)
    user_list_keys = Taskboard['user_list']
    user_list_keys.remove(user)
    Taskboard.update({
        'user_list' : user_list_keys
    })
    datastore_client.put(Taskboard)
    Tasks = retrieveTask(Taskboard)
    for Task in Tasks:
        if Task['assigned'] == user:
            Task.update({
                'assigned': "unassigned"
            })
            datastore_client.put(Task)
    entity_key = datastore_client.key('UserInfo', user)
    entity = datastore_client.get(entity_key)
    Taskboard_keys = entity['Taskboard_list']
    Taskboard_keys.remove(Taskboard_id)
    entity.update({
        'Taskboard_list': Taskboard_keys
    })
    datastore_client.put(entity)


################################## App Routes ######################################################################################################


#########################  app route function inorder to delete user email #########################
@app.route('/delete_user/<email>', methods=['GET', 'POST'])
def delete_user(email):
    id_token = request.cookies.get("token")
    error_message = None
    baby_id = int(request.form['Taskboard_id'])
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                    id_token, firebase_request_adapter)
            deleteUser(baby_id, email)           
        except ValueError as exc:
            error_message = str(exc)
    return redirect(url_for("viewboard", id=baby_id))

#########################  app route function inorder to delete task #########################

@app.route('/delete_task/<int:id>', methods=['GET', 'POST'])
def delete_task(id):
    id_token = request.cookies.get("token")
    error_message = None
    baby_id = id
    if request.method == 'POST':
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                        id_token, firebase_request_adapter)
                deleteTask( baby_id, id)
            except ValueError as exc:
                error_message = str(exc)
        return redirect(url_for("viewboard", id= baby_id))
    else:
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                        id_token, firebase_request_adapter)
                Taskboard = retrieveSingleTaskBoard(id)
                Task = retrieveSingleTask(id)
            except ValueError as exc:
                error_message = str(exc)
        return render_template('delete_task.html', Taskboard=Taskboard, baby_id=baby_id, user_data=claims, error_message=error_message,Task=Task)

#########################  app route function inorder to delete board #########################
@app.route('/deleteboard/<int:id>', methods=['GET','POST'])
def deleteboard(id):
    id_token = request.cookies.get("token")
    error_message=None
    claims=None
    Taskboard_id = id
    
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                    id_token, firebase_request_adapter)
            UserInfo = retrieveUserInfo(claims)
            Taskboard = retrieveSingleTaskBoard(id)
            if not Taskboard['task_list']:
                if len(Taskboard['user_list']) == 1:
                    deleteBoard(Taskboard_id, UserInfo)
            else:
                return redirect(url_for("boardlist", id=Taskboard_id))
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/board_list')

#########################  app route function inorder to rename board #########################

@app.route('/renameboard/<int:id>', methods=['GET','POST'])
def renameboard(id):
    id_token = request.cookies.get("token")
    error_message = None
    baby_id = id
    claims=None
    if request.method == 'POST':
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                        id_token, firebase_request_adapter)
                Taskboard = retrieveSingleTaskBoard(id)
                Taskboard.update({
                    'name': request.form['name']
                })
                datastore_client.put(Taskboard)
            except ValueError as exc:
                error_message = str(exc)
        return redirect(url_for('boardlist'))
    else:
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                        id_token, firebase_request_adapter)
                Taskboard = retrieveSingleTaskBoard(id)

            except ValueError as exc:
                error_message = str(exc)
        return render_template('renameboard.html', Taskboard=Taskboard, baby_id=baby_id,user_data=claims, error_message=error_message)


#########################  app route function inorder to check status of the task #########################

@app.route('/check_task', methods=['POST'])
def Check_task():
    id_token = request.cookies.get("token")
    error_message = None
    baby_id = int(request.form['Taskboard_id'])
    id = int(request.form['id'])
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            Task = retrieveSingleTask( id)
            if request.form['status'] == 'complete':
                Task.update({
                    'status': request.form['status'],
                    'currenttask_completed': datetime.datetime.now()
                })
            else:
                Task.update({
                    'status': request.form['status'],
                    'currenttask_completed': None
                })
            datastore_client.put(Task)
        except ValueError as exc:
            error_message = str(exc)
    return redirect(url_for("viewboard", id=baby_id))

#########################  app route function inorder to add User #########################
@app.route('/adduser/<int:id>', methods=['GET','POST'])
def add_user(id):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    UserInfo = None
    baby_id = id
    if request.method == 'POST':
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                UserInfo = retrieveUserInfo(claims)
                Taskboard = retrieveSingleTaskBoard(id)         
                entity_key = datastore_client.key('UserInfo', request.form['email'])
                entity = datastore_client.get(entity_key)
                if entity:
                    addUserToTaskBoard(Taskboard, request.form['email'])
                    addTaskBoardToUser(entity, baby_id) 
            except ValueError as exc:
                error_message = str(exc)
        return redirect(url_for("viewboard", id=baby_id))
    else:
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                Taskboard = retrieveSingleTaskBoard(id)               
            except ValueError as exc:
                error_message = str(exc)
        return render_template('adduser.html', Taskboard=Taskboard, baby_id=baby_id, user_data=claims, error_message=error_message)

#########################  app route function inorder to add task #########################
@app.route('/addtask/<int:id>', methods=['GET','POST'])
def create_task(id):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    UserInfo = None
    baby_id = id
    if request.method == 'POST':
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                UserInfo = retrieveUserInfo(claims)
                Taskboard = retrieveSingleTaskBoard(id)
                Task = retrieveTask(Taskboard)
                title = request.form['title']
                if namecheck(title,Task ):
                    error_message = 'Task Exist'
                    return render_template('error.html', error_message=error_message,Taskboard=Taskboard,UserInfo=UserInfo,user_data=claims)    
                task_id = createTask(claims, request.form['title'], request.form['due_date'], request.form['status'], request.form['assigned'])
                addTaskToTaskBoard(Taskboard, task_id)
            except ValueError as exc:
                error_message = str(exc)
        return redirect(url_for("viewboard", id=baby_id))
    else:
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(
                        id_token, firebase_request_adapter)
                Taskboard = retrieveSingleTaskBoard(id)
                user = retrieveUser(Taskboard) 
            except ValueError as exc:
                error_message = str(exc)
        return render_template('addtask.html', Taskboard=Taskboard, baby_id=baby_id, user_data=claims, error_message=error_message,user=user)

#########################  app route function inorder to view board #########################

@app.route('/viewboard/<int:id>', methods=['GET','POST'])
def viewboard(id):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    UserInfo = None
    Taskboard = None
    baby_id = id
    user = None
    Task = None
    if request.method == 'GET':
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                UserInfo = retrieveUserInfo(claims)
                Taskboard = retrieveSingleTaskBoard(id)
                update_Taskstatus(Taskboard)
                Task = retrieveTask(Taskboard)
                user = retrieveUser(Taskboard)
            except ValueError as exc:
                error_message = str(exc)
        return render_template('viewboard.html', user_data=claims, error_message=error_message, UserInfo=UserInfo,Taskboard=Taskboard, baby_id=baby_id, Task=Task,user=user)

#########################  app route function inorder to add board list #########################

@app.route('/board_list', methods=["GET","POST"])
def boardlist():
   id_token = request.cookies.get("token")
   user_data=None
   error_message = None
   UserInfo = None
   Taskboard = None

   if id_token:
      try:
         claims = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
         UserInfo = retrieveUserInfo(claims)
         Taskboard= retrieveTaskBoard(UserInfo)
      except ValueError as exc:
         error_message = str(exc)
   return render_template('board_list.html', user_data=claims, error_message=error_message,UserInfo=UserInfo,Taskboard=Taskboard)

#########################  app route function inorder to add board #########################
@app.route('/addboard', methods=["GET","POST"])    
def taskboard():
   id_token = request.cookies.get("token")
   user_data=None
   error_message = None
   UserInfo = None
   Taskboard = None
   if request.method == "POST":
      if id_token:
         try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
            UserInfo = retrieveUserInfo(claims)
            id = CreateTaskboard(claims, request.form['name'])
            if id != False:
              addTaskBoardToUser(UserInfo, id)
         except ValueError as exc:
            error_message = str(exc)
      return redirect(url_for("boardlist"))
   else:
      if id_token:
         try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
            UserInfo = retrieveUserInfo(claims)
            Taskboard=retrieveTaskBoard(UserInfo)
         except ValueError as exc:
            error_message = str(exc)
      return render_template('addboard.html', user_data=claims, error_message=error_message,UserInfo=UserInfo,Taskboard=Taskboard)

#########################  app route function for index and home page #########################
@app.route('/', methods=["GET","POST"])
def root():
   id_token = request.cookies.get("token")
   error_message = None
   claims = None
   UserInfo = None
   Taskboard = None
   if request.method == "GET":
      if id_token:
         try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
            UserInfo = retrieveUserInfo(claims)
            if UserInfo == None:
               createUserInfo(claims)
               UserInfo = retrieveUserInfo(claims)
            Taskboard =  retrieveTaskBoard(UserInfo)
         except ValueError as exc:
            error_message = str(exc)

      return render_template('home.html', user_data=claims, error_message=error_message,UserInfo=UserInfo,Taskboard=Taskboard)
   else:
      return render_template('index.html')


#########################  app route function for rredirecting the index page #########################
@app.route('/index', methods=["GET","POST"])
def mainpage():
   return render_template('index.html')





if __name__ == '__main__':
 app.run(host='127.0.0.1', port=8080, debug=True)

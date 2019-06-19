from cryptography import fernet
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_session
import base64
from cravat import admin_util as au
import aiosqlite3
import asyncio
import os
import hashlib

class ServerAdminDb ():
    def __init__ (self):
        pass

    async def init (self):
        conf_dir = au.get_conf_dir()
        admin_db_path = os.path.join(conf_dir, 'admin.sqlite')
        if os.path.exists(admin_db_path) == False:
            self.db = await aiosqlite3.connect(admin_db_path)
            self.cursor = await self.db.cursor()
            await self.cursor.execute('create table users (email text, passwordhash text, sessionkey text, question text, answerhash text)')
            await self.cursor.execute('create table jobs (jobname text, username text, submit date, runtime integer, numinput integer, annotators text, genome text)')
            m = hashlib.sha256()
            adminpassword = 'admin'
            m.update(adminpassword.encode('utf-16be'))
            adminpasswordhash = m.hexdigest()
            self.cursor.execute('insert into users values ("admin", "{}", "", "", "")'.format(adminpasswordhash))
            self.cursor.close()
            self.db.commit()
        else:
            self.db = await aiosqlite3.connect(admin_db_path)
            self.cursor = await self.db.cursor()

    async def check_sessionkey (self, username, sessionkey):
        q = 'select * from users where email="{}" and sessionkey="{}"'.format(username, sessionkey)
        await self.cursor.execute(q)
        r = await self.cursor.fetchone()
        if r is not None:
            return True
        else:
            return False
    
    async def set_sessionkey (self, username, sessionkey):
        await self.cursor.execute('update users set sessionkey="{}" where email="{}"'.format(sessionkey, username))
        await self.db.commit()

    async def check_password (self, username, passwordhash):
        q = 'select * from users where email="{}" and passwordhash="{}"'.format(username, passwordhash)
        await self.cursor.execute(q)
        r = await self.cursor.fetchone()
        if r is not None:
            return True
        else:
            return False
    
    async def add_job_info (self, job_id, username, submission_time, assembly):
        await self.cursor.execute('insert into jobs values ("{}", "{}", "{}", {}, {}, "{}", "{}")'.format(job_id, username, 'submission_time', -1, -1, '', assembly))
        await self.db.commit()

    async def check_username_presence (self, username):
        await self.cursor.execute('select * from users where email="{}"'.format(username))
        r = await self.cursor.fetchone()
        if r is None:
            return False
        else:
            return True

    async def add_user (self, username, passwordhash, question, answerhash):
        await self.cursor.execute('insert into users values ("{}", "{}", "{}", "{}", "{}")'.format(username, passwordhash, "", question, answerhash))
        await self.db.commit()

    async def store_sessionkey (self, username, sessionkey):
        await self.cursor.execute('update users set sessionkey="{}" where email="{}"'.format(sessionkey, username))
        await self.db.commit()

    async def get_password_question (self, email):
        await self.cursor.execute('select question from users where email="{}"'.format(email))
        r = await self.cursor.fetchone()
        if r is None:
            return None
        else:
            return r[0]

    async def check_password_answer (self, email, answerhash):
        await self.cursor.execute('select * from users where email="{}" and answerhash="{}"'.format(email, answerhash))
        r = await self.cursor.fetchone()
        if r is None:
            return False
        else:
            return True

    async def set_temp_password (self, email):
        temppassword = 'temp_password'
        m = hashlib.sha256()
        m.update(temppassword.encode('utf-16be'))
        temppasswordhash = m.hexdigest()
        await self.cursor.execute('update users set passwordhash="{}" where email="{}"'.format(temppasswordhash, email))
        await self.db.commit()
        return temppassword

    async def set_password (self, email, passwordhash):
        await self.cursor.execute('update users set passwordhash="{}" where email="{}"'.format(passwordhash, email))
        await self.db.commit()

loop = asyncio.get_event_loop()
admindb = ServerAdminDb()
async def admindbinit ():
    await admindb.init()
loop.create_task(admindbinit())

def get_session_key ():
    fernet_key = fernet.Fernet.generate_key()
    session_key = str(fernet_key)
    return session_key

def setup (app):
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    cookie = EncryptedCookieStorage(secret_key)
    aiohttp_session.setup(app, cookie)

async def get_session (request):
    session = await aiohttp_session.get_session(request)
    return session

async def new_session (request):
    session = await aiohttp_session.new_session(request)
    return session

async def is_admin_loggedin (request):
    session = await aiohttp_session.get_session(request)
    r = await is_loggedin(request)
    if session['username'] == 'admin' and r:
        return True
    else:
        return False

async def is_loggedin (request):
    session = await aiohttp_session.get_session(request)
    if 'username' not in session or 'sessionkey' not in session:
        response = False
    else:
        response = await admindb.check_sessionkey(session['username'], session['sessionkey'])
    return response

async def get_username (request):
    session = await aiohttp_session.get_session(request)
    return session['username']

async def add_job_info (request, job, job_options):
    session = await get_session(request)
    username = session['username']
    await admindb.add_job_info(job.info['id'], username, job.get_info_dict()['submission_time'], job_options['assembly'])

def create_user_dir_if_not_exist (username):
    root_jobs_dir = au.get_jobs_dir()
    user_job_dir = os.path.join(root_jobs_dir, username)
    if os.path.exists(user_job_dir) == False:
        os.mkdir(user_job_dir)

async def signup (request):
    queries = request.rel_url.query
    username = queries['username']
    password = queries['password']
    m = hashlib.sha256()
    m.update(password.encode('utf-16be'))
    passwordhash = m.hexdigest()
    question = queries['question']
    answer = queries['answer']
    m = hashlib.sha256()
    m.update(answer.encode('utf-16be'))
    answerhash = m.hexdigest()
    r = await admindb.check_username_presence(username)
    if r == True:
        response = 'already registered'
    else:
        await admindb.add_user(username, passwordhash, question, answerhash)
        session = await get_session(request)
        session['username'] = username
        session['logged'] = True
        create_user_dir_if_not_exist(username)
        sessionkey = get_session_key()
        session['sessionkey'] = sessionkey
        await admindb.store_sessionkey(username, sessionkey)
        response = 'success'
    return response

async def login (request):
    queries = request.rel_url.query
    username = queries['username']
    password = queries['password']
    m = hashlib.sha256()
    m.update(password.encode('utf-16be'))
    passwordhash = m.hexdigest()
    r = await admindb.check_password(username, passwordhash)
    if r == True:
        session = await new_session(request)
        session['username'] = username
        session['logged'] = True
        sessionkey = get_session_key()
        session['sessionkey'] = sessionkey
        await admindb.set_sessionkey(username, sessionkey)
        response = 'success'
    else:
        response = 'fail'
    return response

async def get_password_question (request):
    queries = request.rel_url.query
    email = queries['email']
    question = await admindb.get_password_question(email)
    return question

async def check_password_answer (request):
    queries = request.rel_url.query
    email = queries['email']
    answer = queries['answer']
    m = hashlib.sha256()
    m.update(answer.encode('utf-16be'))
    answerhash = m.hexdigest()
    r = await admindb.check_password_answer(email, answerhash)
    return r

async def set_temp_password (request):
    queries = request.rel_url.query
    email = queries['email']
    temppassword = await admindb.set_temp_password(email)
    return temppassword

async def change_password (request):
    session = await get_session(request)
    if 'username' not in session:
        response = 'Not logged in'
        return response
    email = session['username']
    queries = request.rel_url.query
    oldpassword = queries['oldpassword']
    newpassword = queries['newpassword']
    m = hashlib.sha256()
    m.update(oldpassword.encode('utf-16be'))
    oldpasswordhash = m.hexdigest()
    r = await admindb.check_password(email, oldpasswordhash)
    if r == False:
        response = 'User authentication failed.'
    else:
        m = hashlib.sha256()
        m.update(newpassword.encode('utf-16be'))
        newpasswordhash = m.hexdigest()
        await admindb.set_password(email, newpasswordhash)
        response = 'success'
    return response

async def check_logged (request):
    session = await get_session(request)
    if not 'username' in session:
        response = {'logged': False, 'email': ''}
    else:
        username = session['username']
        r = await is_loggedin(request)
        if r == True:
            response = {'logged': True, 'email': username}
        else:
            response = {'logged': False, 'email': ''}
    return response

async def logout (request):
    session = await new_session(request)
    session['username'] = None
    response = 'success'
    return response


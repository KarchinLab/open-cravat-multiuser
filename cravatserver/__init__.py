from aiohttp import web
from cryptography import fernet
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_session
import base64
from cravat import admin_util as au
import aiosqlite3
import sqlite3
import asyncio
import os
import hashlib
from cravat.constants import admindb_path
import datetime
from collections import defaultdict

class ServerAdminDb ():
    def __init__ (self):
        initdb = not os.path.exists(admindb_path)
        db = sqlite3.connect(admindb_path)
        cursor = db.cursor()
        if initdb:    
            cursor.execute('create table users (email text, passwordhash text, question text, answerhash text)')
            m = hashlib.sha256()
            adminpassword = 'admin'
            m.update(adminpassword.encode('utf-16be'))
            adminpasswordhash = m.hexdigest()
            cursor.execute('insert into users values ("admin", "{}", "", "")'.format(adminpasswordhash))
            db.commit()
            cursor.execute('create table jobs (jobid text, username text, submit date, runtime integer, numinput integer, annotators text, assembly text)')
            cursor.execute('create table config (key text, value text)')
            fernet_key = fernet.Fernet.generate_key()
            cursor.execute('insert into config (key, value) values ("fernet_key",?)',[fernet_key])
            cursor.execute('create table sessions (username text, sessionkey text)')
            db.commit()
        else:
            cursor.execute('select value from config where key="fernet_key"')
            fernet_key = cursor.fetchone()[0]
        self.secret_key = base64.urlsafe_b64decode(fernet_key)
        self.sessions = defaultdict(set)

    async def init (self):
        self.db = await aiosqlite3.connect(admindb_path)
        self.cursor = await self.db.cursor()

    async def check_sessionkey (self, username, sessionkey):
        print(self.sessions)
        if sessionkey in self.sessions[username]:
            return True
        else:
            await self.cursor.execute('select username from sessions where sessionkey = ?',[sessionkey])
            r = await self.cursor.fetchone()
            if r and r[0] == username:
                self.sessions[username].add(sessionkey)
                return True
            else:
                return False

    async def add_sessionkey (self, username, sessionkey):
        self.sessions[username].add(sessionkey)
        await self.cursor.execute('insert into sessions (username, sessionkey) values (?, ?)',[username, sessionkey])
        await self.db.commit()
    
    async def remove_sessionkey(self, username, sessionkey):
        self.sessions[username].remove(sessionkey)
        await self.cursor.execute('delete from sessions where username=? and sessionkey=?',[username, sessionkey])
        await self.db.commit()

    async def check_password (self, username, passwordhash):
        q = 'select * from users where email="{}" and passwordhash="{}"'.format(username, passwordhash)
        await self.cursor.execute(q)
        r = await self.cursor.fetchone()
        if r is not None:
            return True
        else:
            return False
    
    async def add_job_info (self, username, job):
        await self.cursor.execute('insert into jobs values ("{}", "{}", "{}", {}, {}, "{}", "{}")'.format(job.info['id'], username, job.info['submission_time'], -1, -1, ','.join(job.info['annotators']), job.info['assembly']))
        await self.db.commit()

    async def check_username_presence (self, username):
        await self.cursor.execute('select * from users where email="{}"'.format(username))
        r = await self.cursor.fetchone()
        if r is None:
            return False
        else:
            return True

    async def add_user (self, username, passwordhash, question, answerhash):
        await self.cursor.execute('insert into users values ("{}", "{}", "{}", "{}")'.format(username, passwordhash, question, answerhash))
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

    async def get_input_stat (self, start_date, end_date):
        db = await aiosqlite3.connect(admindb_path)
        cursor = await self.db.cursor()
        q = 'select sum(numinput), max(numinput), avg(numinput) from jobs where submit>="{}" and submit<="{}" and numinput!=-1'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchall()
        row = row[0]
        s = row[0] if row[0] is not None else 0
        m = row[1] if row[1] is not None else 0
        a = row[2] if row[2] is not None else 0
        response = [s, m, a]
        await cursor.close()
        await db.close()
        return response

    async def get_user_stat (self, start_date, end_date):
        db = await aiosqlite3.connect(admindb_path)
        cursor = await self.db.cursor()
        q = 'select count(distinct username) from jobs where submit>="{}" and submit<="{}"'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            num_unique_users = 0
        else:
            num_unique_users = row[0]
        q = 'select username, count(*) as c from jobs where submit>="{}" and submit<="{}" group by username order by c desc limit 1'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            (frequent_user, frequent_user_num_jobs) = (0, 0)
        else:
            (frequent_user, frequent_user_num_jobs) = row
        q = 'select username, sum(numinput) s from jobs where submit>="{}" and submit<="{}" group by username order by s desc limit 1'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            (heaviest_user, heaviest_user_num_input) = (0, 0)
        else:
            (heaviest_user, heaviest_user_num_input) = row
        response = {'num_uniq_user': num_unique_users, 'frequent':[frequent_user, frequent_user_num_jobs], 'heaviest':[heaviest_user, heaviest_user_num_input]}
        await cursor.close()
        await db.close()
        return response

    async def get_job_stat (self, start_date, end_date):
        db = await aiosqlite3.connect(admindb_path)
        cursor = await self.db.cursor()
        q = 'select count(*) from jobs where submit>="{}" and submit<="{}"'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            num_jobs = 0
        else:
            num_jobs = row[0]
        q = 'select date(submit) as d, count(*) as c from jobs where submit>="{}" and submit<="{}" group by d order by d asc'.format(start_date, end_date)
        await cursor.execute(q)
        rows = await cursor.fetchall()
        submits = []
        counts = []
        for row in rows:
            submits.append(row[0])
            counts.append(row[1])
        response = {'num_jobs': num_jobs, 'chartdata': [submits, counts]}
        await cursor.close()
        await db.close()
        return response

    async def get_annot_stat (self, start_date, end_date):
        db = await aiosqlite3.connect(admindb_path)
        cursor = await self.db.cursor()
        q = 'select annotators from jobs where submit>="{}" and submit<="{}"'.format(start_date, end_date)
        await cursor.execute(q)
        rows = await cursor.fetchall()
        annot_count = {}
        for row in rows:
            annots = row[0].split(',')
            for annot in annots:
                if not annot in annot_count:
                    annot_count[annot] = 0
                annot_count[annot] += 1
        response = {'annot_count': annot_count}
        await cursor.close()
        await db.close()
        return response

    async def get_assembly_stat (self, start_date, end_date):
        db = await aiosqlite3.connect(admindb_path)
        cursor = await self.db.cursor()
        q = 'select assembly, count(*) as c from jobs where submit>="{}" and submit<="{}" group by assembly order by c desc'.format(start_date, end_date)
        await cursor.execute(q)
        rows = await cursor.fetchall()
        assembly_count = []
        for row in rows:
            (assembly, count) = row
            assembly_count.append([assembly, count])
        response = assembly_count
        await cursor.close()
        await db.close()
        return response

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
    cookie = EncryptedCookieStorage(admindb.secret_key)
    aiohttp_session.setup(app, cookie)

async def get_session (request):
    session = await aiohttp_session.get_session(request)
    return session

async def new_session (request):
    session = await aiohttp_session.new_session(request)
    return session

async def is_admin_loggedin (request):
    session = await get_session(request)
    r = await is_loggedin(request)
    if 'username' in session and session['username'] == 'admin' and r:
        return True
    else:
        return False

async def get_username (request):
    session = await get_session(request)
    if 'username' in session:
        username = session['username']
    else:
        username = None
    return username

async def add_job_info (request, job):
    session = await get_session(request)
    username = session['username']
    await admindb.add_job_info(username, job)

def create_user_dir_if_not_exist (username):
    root_jobs_dir = au.get_jobs_dir()
    user_job_dir = os.path.join(root_jobs_dir, username)
    if os.path.exists(user_job_dir) == False:
        os.mkdir(user_job_dir)

async def signup (request):
    global servermode
    if servermode:
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
            await admindb.add_sessionkey(username, sessionkey)
            response = 'success'
    else:
        response = 'fail'
    return web.json_response(response)

async def login (request):
    global servermode
    if servermode:
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
            await admindb.add_sessionkey(username, sessionkey)
            response = 'success'
        else:
            response = 'fail'
    else:
        response = 'fail'
    return web.json_response(response)

async def get_password_question (request):
    global servermode
    if servermode:
        queries = request.rel_url.query
        email = queries['email']
        question = await admindb.get_password_question(email)
        if question is None:
            response = {'status':'fail', 'msg':'No such email'}
        else:
            response = {'status':'success', 'msg': question}
    else:
        response = {'status':'fail', 'msg':'no server mode'}
    return web.json_response(response)

async def check_password_answer (request):
    global servermode
    if servermode:
        queries = request.rel_url.query
        email = queries['email']
        answer = queries['answer']
        m = hashlib.sha256()
        m.update(answer.encode('utf-16be'))
        answerhash = m.hexdigest()
        correct = await admindb.check_password_answer(email, answerhash)
        if correct:
            temppassword = await set_temp_password(request)
            response = {'success': True, 'msg': temppassword}
        else:
            response = {'success': False, 'msg': 'Wrong answer'}
    else:
        response = {'success': False, 'msg': 'no server mode'}
    return web.json_response(response)

async def set_temp_password (request):
    queries = request.rel_url.query
    email = queries['email']
    temppassword = await admindb.set_temp_password(email)
    return temppassword

async def change_password (request):
    global servermode
    if servermode:
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
    else:
        response = 'no server mode'
    return web.json_response(response)

async def is_loggedin (request):
    session = await get_session(request)
    if 'username' not in session or 'sessionkey' not in session:
        response = False
    else:
        response = await admindb.check_sessionkey(session['username'], session['sessionkey'])
    return response

async def check_logged (request):
    global servermode
    if servermode:
        if 'Cache-Control' in request.headers:
            session = await new_session(request)
        else:
            session = await get_session(request)
        if not 'username' in session:
            logged = False
            email = ''
        else:
            username = session['username']
            r = await is_loggedin(request)
            if r == True:
                logged = True
                email = username
            else:
                logged = False
                email = ''
        response = {'logged': logged, 'email': email}
    else:
        response = 'no server mode'
    return web.json_response(response)

async def logout (request):
    global servermode
    if servermode:
        session = await get_session(request)
        await admindb.remove_sessionkey(session['username'], session['sessionkey'])
        ns = await new_session(request)
        ns['username'] = None
        response = 'success'
    else:
        response = 'no server mode'
    return web.json_response(response)

async def get_input_stat (request):
    global servermode
    if not servermode:
        return web.json_response('no server mode')
    r = await is_admin_loggedin(request)
    if r == False:
        return web.json_response('no admin')
    queries = request.rel_url.query
    start_date = queries['start_date']
    end_date = queries['end_date']
    rows = await admindb.get_input_stat(start_date, end_date)
    return web.json_response(rows)

async def get_user_stat (request):
    global servermode
    if not servermode:
        return web.json_response('no server mode')
    r = await is_admin_loggedin(request)
    if r == False:
        return web.json_response('no admin')
    queries = request.rel_url.query
    start_date = queries['start_date']
    end_date = queries['end_date']
    rows = await admindb.get_user_stat(start_date, end_date)
    return web.json_response(rows)

async def get_job_stat (request):
    global servermode
    if not servermode:
        return web.json_response('no server mode')
    r = await is_admin_loggedin(request)
    if r == False:
        return web.json_response('no admin')
    queries = request.rel_url.query
    start_date = queries['start_date']
    end_date = queries['end_date']
    response = await admindb.get_job_stat(start_date, end_date)
    return web.json_response(response)

async def get_annot_stat (request):
    global servermode
    if not servermode:
        return web.json_response('no server mode')
    r = await is_admin_loggedin(request)
    if r == False:
        return web.json_response('no admin')
    queries = request.rel_url.query
    start_date = queries['start_date']
    end_date = queries['end_date']
    response = await admindb.get_annot_stat(start_date, end_date)
    return web.json_response(response)

async def get_assembly_stat (request):
    global servermode
    if not servermode:
        return web.json_response('no server mode')
    r = await is_admin_loggedin(request)
    if r == False:
        return web.json_response('no admin')
    queries = request.rel_url.query
    start_date = queries['start_date']
    end_date = queries['end_date']
    response = await admindb.get_assembly_stat(start_date, end_date)
    return web.json_response(response)

async def restart (request):
    global servermode
    if servermode:
        username = await get_username(request)
        if username != 'admin':
            return web.json_response({'success': False, 'msg': 'Only admin can change the settings.'})
        r = await is_loggedin(request)
        if r == False:
            return web.json_response({'success': False, 'mgs': 'Only logged-in admin can change the settings.'})
    '''
    queries = request.rel_url.query
    if 'maxnumconcurjobs' in queries:
        system_conf = au.get_system_conf()
        max_num_concurrent_jobs = queries['maxnumconcurjobs']
        try:
            system_conf['max_num_concurrent_jobs'] = int(max_num_concurrent_jobs)
            au.write_system_conf_file(system_conf)
            print('Maximum number of concurrent jobs set to {}.'.format(max_num_concurrent_jobs))
        except:
            print('Wrong format for maximum number of concurrent jobs: {}'.format(max_num_concurrent_jobs))
    '''
    os.execvp('wcravat', ['wcravat', '--server', '--donotopenbrowser'])

def add_routes (router):
    router.add_route('GET', '/server/login', login)
    router.add_route('GET', '/server/logout', logout)
    router.add_route('GET', '/server/signup', signup)
    router.add_route('GET', '/server/passwordquestion', get_password_question)
    router.add_route('GET', '/server/passwordanswer', check_password_answer)
    router.add_route('GET', '/server/changepassword', change_password)
    router.add_route('GET', '/server/checklogged', check_logged)
    router.add_route('GET', '/server/inputstat', get_input_stat)
    router.add_route('GET', '/server/userstat', get_user_stat)
    router.add_route('GET', '/server/jobstat', get_job_stat)
    router.add_route('GET', '/server/annotstat', get_annot_stat)
    router.add_route('GET', '/server/assemblystat', get_assembly_stat)
    router.add_route('GET', '/server/restart', restart)
    router.add_static('/server', os.path.join(os.path.dirname(os.path.realpath(__file__))))


from aiohttp import web
from cryptography import fernet
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_session
import base64
from cravat import admin_util as au
import aiosqlite
import sqlite3
import asyncio
import os
import hashlib
from cravat.constants import admindb_path
import datetime
from collections import defaultdict
import json
import time
from base64 import b64decode
import random

admindb = None

class ServerAdminDb ():
    def __init__ (self):
        initdb = not os.path.exists(admindb_path)
        conn = sqlite3.connect(admindb_path)
        cursor = conn.cursor()
        self.sessions = defaultdict(set)
        if initdb:    
            cursor.execute('create table users (email text, passwordhash text, question text, answerhash text, settings text)')
            m = hashlib.sha256()
            adminpassword = 'admin'
            m.update(adminpassword.encode('utf-16be'))
            adminpasswordhash = m.hexdigest()
            cursor.execute('insert into users values ("admin", "{}", "", "", null)'.format(adminpasswordhash))
            conn.commit()
            cursor.execute('create table jobs (jobid text, username text, submit date, runtime integer, numinput integer, annotators text, assembly text)')
            cursor.execute('create table config (key text, value text)')
            fernet_key = fernet.Fernet.generate_key()
            cursor.execute('insert into config (key, value) values ("fernet_key",?)',[fernet_key])
            cursor.execute('create table sessions (username text, sessionkey text, last_active text default current_timestamp, primary key (username, sessionkey))')
            conn.commit()
        else:
            cursor.execute('select value from config where key="fernet_key"')
            fernet_key = cursor.fetchone()[0]
            cursor.execute('select username, sessionkey from sessions')
            rows = cursor.fetchall()
            for row in rows:
                (username, sessionkey) = row
                if username not in self.sessions:
                    self.sessions[username] = set()
                self.sessions[username].add(sessionkey)
        self.secret_key = base64.urlsafe_b64decode(fernet_key)
        cursor.close()
        conn.close()

    async def get_db_conn (self):
        if admindb_path is None:
            return None
        conn = await aiosqlite.connect(admindb_path)
        return conn

    async def init (self):
        await self.create_apilog_table_if_necessary()

    async def check_sessionkey (self, username, sessionkey):
        if username not in self.sessions or sessionkey not in self.sessions[username]:
            return False
        else:
            conn = await self.get_db_conn()
            cursor = await conn.cursor()
            await cursor.execute('select username from sessions where sessionkey = ?',[sessionkey])
            r = await cursor.fetchone()
            await cursor.close()
            await conn.close()
            if r and r[0] == username:
                if sessionkey not in self.sessions[username]:
                    self.sessions[username].add(sessionkey)
                return True
            else:
                return False

    async def add_sessionkey (self, username, sessionkey):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        self.sessions[username].add(sessionkey)
        await cursor.execute('insert into sessions (username, sessionkey) values (?, ?)',[username, sessionkey])
        await conn.commit()
        await cursor.close()
        await conn.close()
    
    async def remove_sessionkey(self, username, sessionkey):
        self.sessions[username].discard(sessionkey)
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute('delete from sessions where username=? and sessionkey=?',[username, sessionkey])
        await conn.commit()
        await cursor.close()
        await conn.close()

    async def update_last_active(self, username, sessionkey):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute('update sessions set last_active = current_timestamp where username=? and sessionkey=?',[username, sessionkey])
        await conn.commit()
        await cursor.close()
        await conn.close()

    async def clean_sessions(self, max_age):
        """
        Delete sessions older than a number of seconds.
        """
        conn = await self.get_db_conn()
        if conn is not None:
            cursor = await conn.cursor()
            await cursor.execute(f'delete from sessions where last_active <= datetime(current_timestamp,"-{max_age} seconds")')
            await conn.commit()
            await cursor.close()
        await conn.close()

    async def check_password (self, username, passwordhash):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'select * from users where email="{}" and passwordhash="{}"'.format(username, passwordhash)
        await cursor.execute(q)
        r = await cursor.fetchone()
        await cursor.close()
        await conn.close()
        if r is not None:
            return True
        else:
            return False
    
    async def add_job_info (self, username, job):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'insert into jobs values ("{}", "{}", "{}", {}, {}, "{}", "{}")'.format(job.info['id'], username, job.info['submission_time'], -1, -1, ','.join(job.info['annotators']), job.info['assembly'])
        await cursor.execute(q)
        await conn.commit()
        await cursor.close()
        await conn.close()

    async def check_username_presence (self, username):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute('select * from users where email="{}"'.format(username))
        r = await cursor.fetchone()
        await cursor.close()
        await conn.close()
        if r is None:
            return False
        else:
            return True

    async def add_user (self, username, passwordhash, question, answerhash):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        default_settings = {'lastAssembly':None}
        await cursor.execute('insert into users values (?, ?, ?, ?, ?)',[username, passwordhash, question, answerhash, json.dumps(default_settings)])
        await conn.commit()
        await cursor.close()
        await conn.close()

    async def get_password_question (self, email):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute('select question from users where email="{}"'.format(email))
        r = await cursor.fetchone()
        await cursor.close()
        await conn.close()
        if r is None:
            return None
        else:
            return r[0]

    async def check_password_answer (self, email, answerhash):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute('select * from users where email="{}" and answerhash="{}"'.format(email, answerhash))
        r = await cursor.fetchone()
        await cursor.close()
        await conn.close()
        if r is None:
            return False
        else:
            return True

    async def set_temp_password (self, email):
        temppassword = ''.join([chr(random.randint(97,122)) for v in range(8)])
        m = hashlib.sha256()
        m.update(temppassword.encode('utf-16be'))
        temppasswordhash = m.hexdigest()
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute('update users set passwordhash="{}" where email="{}"'.format(temppasswordhash, email))
        await conn.commit()
        await cursor.close()
        await conn.close()
        return temppassword

    async def set_username (self, email, newemail):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute(f'select * from users where email="{newemail}"')
        r = await cursor.fetchone()
        if r is not None:
            await cursor.close()
            await conn.close()
            return 'Duplicate username'
        cursor = await conn.cursor()
        q = f'update users set email="{newemail}" where email="{email}"'
        await cursor.execute(q)
        q = f'update jobs set username="{newemail}" where username="{email}"'
        await cursor.execute(q)
        await conn.commit()
        await cursor.close()
        await conn.close()
        root_jobs_dir = au.get_jobs_dir()
        old_job_dir = os.path.join(root_jobs_dir, email)
        new_job_dir = os.path.join(root_jobs_dir, newemail)
        os.rename(old_job_dir, new_job_dir)
        return ''

    async def set_password (self, email, passwordhash):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute('update users set passwordhash="{}" where email="{}"'.format(passwordhash, email))
        await conn.commit()
        await cursor.close()
        await conn.close()

    async def get_input_stat (self, start_date, end_date):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'select sum(numinput), max(numinput), avg(numinput) from jobs where submit>="{}" and submit<="{}T23:59:59" and numinput!=-1'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchall()
        row = row[0]
        s = row[0] if row[0] is not None else 0
        m = row[1] if row[1] is not None else 0
        a = row[2] if row[2] is not None else 0
        response = [s, m, a]
        await cursor.close()
        await conn.close()
        return response

    async def get_user_stat (self, start_date, end_date):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'select count(distinct username) from jobs where submit>="{}" and submit<="{}T23:59:59"'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            num_unique_users = 0
        else:
            num_unique_users = row[0]
        q = 'select username, count(*) as c from jobs where submit>="{}" and submit<="{}T23:59:59" group by username order by c desc limit 1'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            (frequent_user, frequent_user_num_jobs) = (0, 0)
        else:
            (frequent_user, frequent_user_num_jobs) = row
        q = 'select username, sum(numinput) s from jobs where submit>="{}" and submit<="{}T23:59:59" group by username order by s desc limit 1'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            (heaviest_user, heaviest_user_num_input) = (0, 0)
        else:
            (heaviest_user, heaviest_user_num_input) = row
        response = {'num_uniq_user': num_unique_users, 'frequent':[frequent_user, frequent_user_num_jobs], 'heaviest':[heaviest_user, heaviest_user_num_input]}
        await cursor.close()
        await conn.close()
        return response

    async def get_job_stat (self, start_date, end_date):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'select count(*) from jobs where submit>="{}" and submit<="{}T23:59:59"'.format(start_date, end_date)
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            num_jobs = 0
        else:
            num_jobs = row[0]
        q = 'select date(submit) as d, count(*) as c from jobs where submit>="{}" and submit<="{}T23:59:59" group by d order by d asc'.format(start_date, end_date)
        await cursor.execute(q)
        rows = await cursor.fetchall()
        submits = []
        counts = []
        for row in rows:
            submits.append(row[0])
            counts.append(row[1])
        response = {'num_jobs': num_jobs, 'chartdata': [submits, counts]}
        await cursor.close()
        await conn.close()
        return response

    async def get_api_stat (self, start_date, end_date):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = f'select sum(count) from apilog where writetime>="{start_date}" and writetime<="{end_date}T23:59:59"'
        await cursor.execute(q)
        row = await cursor.fetchone()
        if row is None:
            num_api_access = 0
        else:
            num_api_access = row[0]
        response = {'num_api_access': num_api_access}
        await cursor.close()
        await conn.close()
        return response

    async def get_annot_stat (self, start_date, end_date):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'select annotators from jobs where submit>="{}" and submit<="{}T23:59:59"'.format(start_date, end_date)
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
        await conn.close()
        return response

    async def get_assembly_stat (self, start_date, end_date):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'select assembly, count(*) as c from jobs where submit>="{}" and submit<="{}T23:59:59" group by assembly order by c desc'.format(start_date, end_date)
        await cursor.execute(q)
        rows = await cursor.fetchall()
        assembly_count = []
        for row in rows:
            (assembly, count) = row
            assembly_count.append([assembly, count])
        response = assembly_count
        await cursor.close()
        await conn.close()
        return response

    async def get_user_settings (self, username):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'select settings from users where email=?'
        await cursor.execute(q,[username])
        r = await cursor.fetchone()
        await cursor.close()
        await conn.close()
        if r is None:
            return None
        else:
            settings = r[0]
            if settings is None:
                return {}
            else:
                return json.loads(settings)
    
    async def update_user_settings (self, username, d):
        newsettings = await self.get_user_settings(username)
        newsettings.update(d)
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        await cursor.execute('update users set settings=? where email=?',[json.dumps(newsettings), username])
        await cursor.close()
        await conn.close()

    async def delete_user (self, username):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = f'delete from users where email="{username}"'
        await cursor.execute(q)
        q = f'delete from sessions where username="{username}"'
        await cursor.execute(q)
        await conn.commit()
        await cursor.close()
        await conn.close()

    async def create_apilog_table_if_necessary (self):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        q = 'select count(name) from sqlite_master where type="table" and name="apilog"'
        await cursor.execute(q)
        r = await cursor.fetchone()
        if r[0] == 0:
            q = 'create table apilog (writetime text, count int)'
            await cursor.execute(q)
            await conn.commit()
        await cursor.close()
        await conn.close()

    async def write_single_api_access_count_to_db (self, t, count):
        conn = await self.get_db_conn()
        cursor = await conn.cursor()
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
        q = f'insert into apilog values ("{ts}", {count})'
        await cursor.execute(q)
        await conn.commit()
        await cursor.close()
        await conn.close()

async def update_last_active(request):
    session = await get_session(request)
    username = session.get('username')
    sessionkey = session.get('sessionkey')
    if username and sessionkey:
        await admindb.update_last_active(username, sessionkey)

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

async def is_loggedin (request):
    session = await get_session(request)
    if 'username' not in session or 'sessionkey' not in session:
        response = False
    else:
        response = await admindb.check_sessionkey(session['username'], session['sessionkey'])
    return response

async def is_admin_loggedin (request):
    r = await is_loggedin(request)
    if r == False:
        return False
    session = await get_session(request)
    if 'username' in session and 'admin' in session['username']:
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
            create_user_dir_if_not_exist(username)
            sessionkey = get_session_key()
            session['username'] = username
            session['sessionkey'] = sessionkey
            await admindb.add_sessionkey(username, sessionkey)
            response = 'success'
    else:
        response = 'fail'
    return web.json_response(response)

async def login (request):
    global servermode
    fail_string = 'fail'
    if servermode:
        auth_header = request.headers.get('Authorization')
        if auth_header is None:
            return web.json_response(fail_string)
        auth_toks = auth_header.split()
        if auth_toks[0] != 'Basic' or len(auth_toks) < 2:
            return web.json_response(fail_string)
        credential_toks = b64decode(auth_toks[1]).decode().split(':')
        if len(credential_toks) < 2:
            return web.json_response(fail_string)
        username, password = credential_toks
        if username.startswith('guest_'):
            guest_login = True
            datestr = username.split('_')[2]
            creation_date = datetime.datetime(
                int(datestr[:4]), 
                int(datestr[4:6]), 
                int(datestr[6:8]))
            current_date = datetime.datetime.now()
            days_passed = (current_date - creation_date).days
            global system_conf
            guest_lifetime = system_conf.get('guest_lifetime', 7)
            if days_passed > guest_lifetime:
                await admindb.delete_user(username)
                return web.json_response(fail_string)
            else:
                days_rem = guest_lifetime - days_passed
        else:
            guest_login = False
        m = hashlib.sha256()
        m.update(password.encode('utf-16be'))
        passwordhash = m.hexdigest()
        r = await admindb.check_password(username, passwordhash)
        if r == True:
            session = await get_session(request)
            session['username'] = username
            sessionkey = get_session_key()
            session['sessionkey'] = sessionkey
            await admindb.add_sessionkey(username, sessionkey)
            if guest_login:
                return web.json_response('guestsuccess_' + str(days_rem))
            else:
                return web.json_response('success')
        else:
            return web.json_response(fail_string)
    else:
        return web.json_response(fail_string)

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
        response = {'status':'fail', 'msg':'no multiuser mode'}
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
        response = {'success': False, 'msg': 'no multiuser mode'}
    return web.json_response(response)

async def set_temp_password (request):
    queries = request.rel_url.query
    email = queries['email']
    temppassword = await admindb.set_temp_password(email)
    return temppassword

async def change_password (request):
    global servermode
    if servermode:
        queries = request.rel_url.query
        newemail = queries['newemail']
        oldpassword = queries['oldpassword']
        newpassword = queries['newpassword']
        r = await is_loggedin(request)
        if r == False:
            response = 'Not logged in'
            return web.json_response(response)
        session = await get_session(request)
        if 'username' not in session:
            response = 'Not logged in'
            return web.json_response(response)
        username = session['username']
        m = hashlib.sha256()
        m.update(oldpassword.encode('utf-16be'))
        oldpasswordhash = m.hexdigest()
        if username.startswith('guest_') == False and '@' not in username:
            r = await admindb.check_password(username, oldpasswordhash)
        else:
            r = True
        if r == False:
            response = 'User authentication failed.'
        else:
            if newemail != '':
                r = await admindb.set_username(username, newemail)
                if r != '':
                    return web.json_response(r)
                else:
                    username = newemail
            if newpassword != '':
                m = hashlib.sha256()
                m.update(newpassword.encode('utf-16be'))
                newpasswordhash = m.hexdigest()
                await admindb.set_password(username, newpasswordhash)
            response = 'success'
    else:
        response = 'no multiuser mode'
    return web.json_response(response)

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
            day_rem = -1
        else:
            username = session['username']
            r = await is_loggedin(request)
            if r == True:
                logged = True
                email = username
            else:
                logged = False
                email = ''
            if username.startswith('guest_'):
                datestr = username.split('_')[2]
                creation_date = datetime.datetime(
                    int(datestr[:4]), 
                    int(datestr[4:6]), 
                    int(datestr[6:8]))
                current_date = datetime.datetime.now()
                days_passed = (current_date - creation_date).days
                global system_conf
                guest_lifetime = system_conf.get('guest_lifetime', 7)
                days_rem = guest_lifetime - days_passed
            else:
                days_rem = -1
        response = {'logged': logged, 'email': email, 'days_rem': days_rem}
    else:
        response = 'no multiuser mode'
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
        response = 'no multiuser mode'
    return web.json_response(response)

async def get_input_stat (request):
    global servermode
    if not servermode:
        return web.json_response('no multiuser mode')
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
        return web.json_response('no multiuser mode')
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
        return web.json_response('no multiuser mode')
    r = await is_admin_loggedin(request)
    if r == False:
        return web.json_response('no admin')
    queries = request.rel_url.query
    start_date = queries['start_date']
    end_date = queries['end_date']
    response = await admindb.get_job_stat(start_date, end_date)
    return web.json_response(response)

async def get_api_stat (request):
    global servermode
    if not servermode:
        return web.json_response('no multiuser mode')
    r = await is_admin_loggedin(request)
    if r == False:
        return web.json_response('no admin')
    queries = request.rel_url.query
    start_date = queries['start_date']
    end_date = queries['end_date']
    response = await admindb.get_api_stat(start_date, end_date)
    return web.json_response(response)

async def get_annot_stat (request):
    global servermode
    if not servermode:
        return web.json_response('no multiuser mode')
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
        return web.json_response('no multiuser mode')
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
    os.execvp('wcravat', ['wcravat', '--multiuser', '--headless'])

async def show_login_page (request):
    global servermode
    global server_ready
    if not servermode or not server_ready:
        global logger
        logger.info('Login page requested but no multiuser mode. Redirecting to submit index...')
        return web.HTTPFound('/submit/index.html')
    r = await is_loggedin(request)
    if r == False:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nocache', 'login.html')
        return web.FileResponse(p)
    else:
        logger.info('Login page requested but already logged in. Redirecting to submit index...')
        return web.HTTPFound('/submit/index.html')

async def get_user_settings (request):
    session = await get_session(request)
    response = await admindb.get_user_settings(session['username'])
    return web.json_response(response)

async def update_user_settings (request, d):
    session = await get_session(request)
    return await admindb.update_user_settings(session['username'], d)

async def setup_module ():
    global admindb
    admindb = ServerAdminDb()
    await admindb.init()

system_conf = au.get_system_conf()

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
    router.add_route('GET', '/server/apistat', get_api_stat)
    router.add_route('GET', '/server/annotstat', get_annot_stat)
    router.add_route('GET', '/server/assemblystat', get_assembly_stat)
    router.add_route('GET', '/server/restart', restart)
    router.add_route('GET', '/server/usersettings', get_user_settings)
    router.add_route('GET', '/server/nocache/login.html', show_login_page)
    router.add_static('/server', os.path.join(os.path.dirname(os.path.realpath(__file__))))


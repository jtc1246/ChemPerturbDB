from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from _thread import start_new_thread
from time import sleep, time
import json
from myBasics import binToBase64
from mySecrets import hexToStr
import os
from queue import Queue
# from R_http import *
# from utils import *
from random import randint
import subprocess
# from ai import process_ai
# from ai2 import process_ai_chat
from myHttp import http

# SERVER = 'http://jtc1246.com:9020'
SERVER = 'http://chemperturbdb.weill.cornell.edu/'


NO_CACHE = 100000001
CACHE_ALL = 100000002

CACHE_MODE = NO_CACHE
BROWSER_CACHE = False

USE_BUILT = False
WRITE_LOG = False

LOG_PATH = './server_logs.txt'

registered = []

csses = os.listdir('./css')
jses = os.listdir('./js')
if USE_BUILT:
    jses = os.listdir('./js-build')
jses.remove('consts.js')
imgs = os.listdir('./imgs')


cached_files = {}
log_file = None


def access_file(path: str, bin: bool):
    if (CACHE_MODE == CACHE_ALL and path in cached_files):
        data = cached_files[path]
    else:
        with open(path.replace('/js/', '/js-build/') if USE_BUILT else path, 'rb') as f:
            data = f.read()
        if (CACHE_MODE == CACHE_ALL):
            cached_files[path] = data
    if (bin):
        return data
    return data.decode('utf-8')


for css in csses:
    if (not css.endswith('.css')):
        continue
    registered.append(f'/css/{css}')

for js in jses:
    if (not js.endswith('.js')):
        continue
    registered.append(f'/js/{js}')

for img in imgs:
    tmp = img.lower()
    if (not tmp.endswith('.png') and not tmp.endswith('.jpg') and not tmp.endswith('.jpeg')  and not tmp.endswith('.gif')):
        continue
    registered.append(f'/imgs/{img}')

log_queue = Queue()


class Request(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.do_log()
        path = self.path
        if (path == '/'):
            path = '/index.html'
        if (path == '/index.html'):
            path = '/html/index.html'
        if (path.startswith('/html/')):
            return process_html(self, path)
        if (path.startswith('/api/')):
            return process_get_api(self, path)
        if (path.startswith('/ai/')):
            return process_ai(self, path)
        if (path == '/js/consts.js'):
            return process_constsjs(self)
        return process_404(self)

    def do_log(self):
        self.logs = {}
        path = self.path
        header = dict(self.headers)
        ip = self.client_address[0]
        self.logs['path'] = path
        self.logs['header'] = header
        self.logs['ip'] = ip
        start_time = time()
        self.logs['start_time'] = format(start_time * 1000, '.3f')
        return

    def finish_log(self, status, type, length):
        '''type: html, constjs, api, 404, not_allowed, post, 都是字符串'''
        self.logs['status'] = status
        self.logs['type'] = type
        self.logs['resp_length'] = length
        self.logs['finish_time'] = format(time() * 1000, '.3f')
        log_queue.put(json.dumps(self.logs, ensure_ascii=False))
        return

    def do_POST(self) -> None:
        if(self.path != '/chat'):
            self.send_response(404)
            self.send_header('Connection', 'keep-alive')
            self.send_header('Content-Length', 13)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
            self.wfile.flush()
            return
        process_ai_chat(self, self.path)

    def log_message(self, format, *args):
        pass
    
    def do_OPTIONS(self):
        print('http OPTIONS')
        self.send_response(200)
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Content-Length', 0)
        self.end_headers()
        self.wfile.write(b'')
        self.wfile.flush()
        return


def process_html(request: Request, path: str) -> None:
    if (path.find('..') >= 0):
        return process_404(request, attack=True)
    print(path)
    path = '.' + path
    try:
        html = access_file(path, False)
    except:
        return process_404(request)
    for reg in registered:
        if (html.find(reg) == -1):
            continue
        file = access_file('.' + reg, True)
        file = binToBase64(file)
        if (reg.endswith('.css')):
            html = html.replace(reg, f'data:text/css;base64,{file}')
        if (reg.endswith('.js')):
            html = html.replace(reg, f'data:application/javascript;base64,{file}')
        if (reg.endswith('.png')):
            html = html.replace(reg, f'data:image/png;base64,{file}')
        if (reg.endswith('.jpg') or reg.endswith('.jpeg')):
            html = html.replace(reg, f'data:image/jpeg;base64,{file}')
        if (reg.endswith('.gif')):
            html = html.replace(reg, f'data:image/gif;base64,{file}')
    html = html.encode('utf-8')
    request.send_response(200)
    request.send_header('Connection', 'keep-alive')
    request.send_header('Content-Type', 'text/html')
    request.send_header('Content-Length', len(html))
    if (BROWSER_CACHE):
        request.send_header('Cache-Control', 'max-age=300')
    request.end_headers()
    request.finish_log(200, 'html', len(html))
    request.wfile.write(html)
    request.wfile.flush()
    return


def process_constsjs(request: Request) -> None:
    print('consts.js')
    request.send_response(200)
    data = access_file('./js/consts.js', True)
    request.send_header('Connection', 'keep-alive')
    request.send_header('Content-Length', len(data))
    request.send_header('Content-Type', 'application/javascript')
    request.send_header('Cache-Control', 'max-age=1800')
    request.end_headers()
    request.finish_log(200, 'constjs', len(data))
    request.wfile.write(data)
    request.wfile.flush()
    return

get_cache = {}

def access_get_http(url: str):
    if (url in get_cache):
        return get_cache[url]
    resp = http(url, Decode=False, Timeout=3600000)
    if(resp['status'] != 0):
        return
    status = resp['code']
    data = resp['text']
    get_cache[url] = (status, data)
    return (status, data)


def process_get_api(request: Request, path: str) -> None:
    url = SERVER + path
    # resp = http(url, Decode=False, Timeout=3600000)
    # print(resp)
    # if(resp['status'] != 0):
    #     return
    # status = resp['code']
    # data = resp['text']
    status, data = access_get_http(url)
    request.send_response(status)
    request.send_header('Connection', 'keep-alive')
    request.send_header('Content-Length', len(data))
    request.end_headers()
    request.wfile.write(data)
    request.wfile.flush()
    return

def process_ai(request: Request, path: str) -> None:
    url = SERVER + path
    resp = http(url, Decode=False, Timeout=3600000)
    print(resp)
    if(resp['status'] != 0):
        return
    status = resp['code']
    data = resp['text']
    request.send_response(status)
    request.send_header('Connection', 'keep-alive')
    request.send_header('Content-Length', len(data))
    request.end_headers()
    request.wfile.write(data)
    request.wfile.flush()
    return

def process_ai_chat(request: Request, path: str) -> None:
    url = SERVER + path
    body = request.rfile.read(int(request.headers['Content-Length']))
    resp = http(url, Decode=False, Timeout=3600000, Method='POST', Body=body, Header={'Content-Length': len(body)})
    print(resp)
    if(resp['status'] != 0):
        return
    status = resp['code']
    data = resp['text']
    request.send_response(status)
    request.send_header('Connection', 'keep-alive')
    request.send_header('Content-Length', len(data))
    request.end_headers()
    request.wfile.write(data)
    request.wfile.flush()
    return

def process_post_api(request: Request, path: str) -> None:
    request.send_response(404)
    request.send_header('Connection', 'keep-alive')
    request.send_header('Content-Length', 13)
    request.end_headers()
    request.finish_log(404, 'post', 13)
    request.wfile.write(b'404 Not Found')
    request.wfile.flush()
    return


def process_404(request: Request, attack=False) -> None:
    request.send_response(404)
    request.send_header('Connection', 'keep-alive')
    request.send_header('Content-Length', 13)
    request.end_headers()
    request.finish_log(404, '404' if not attack else 'not_allowed', 13)
    request.wfile.write(b'404 Not Found')
    request.wfile.flush()
    return


if (WRITE_LOG):
    try:
        f = open(LOG_PATH, 'r')
    except:
        log_file = open(LOG_PATH, 'w')
    if (log_file == None):
        f.close()
        log_file = open(LOG_PATH, 'a')
        log_file.write('\n\n')


def write_logs():
    if (WRITE_LOG == False):
        return
    log_file.write(format(time() * 1000, '.3f') + ': Server started\n')
    log_file.flush()
    while True:
        l = log_queue.get()
        current_time = format(time() * 1000, '.3f')
        l = current_time + ': ' + l + '\n'
        log_file.write(l)
        log_file.flush()


def remove_tmp_files():
    while True:
        sleep(60)
        _ = subprocess.check_output('rm -rf ../tmp/*.csv', shell=True)


server = ThreadingHTTPServer(('0.0.0.0', 9020), Request)
start_new_thread(server.serve_forever, ())
start_new_thread(write_logs, ())
start_new_thread(remove_tmp_files, ())
while True:
    sleep(10)

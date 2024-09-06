from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from _thread import start_new_thread
from time import sleep, time
import json
from myBasics import binToBase64
from mySecrets import hexToStr
import os
from queue import Queue
from R_http import *
from utils import *
from random import randint
import subprocess
from ai import process_ai
from ai2 import process_ai_chat


PORT = 9020  # SET YOUR PORT HERE


NO_CACHE = 100000001
CACHE_ALL = 100000002

CACHE_MODE = CACHE_ALL
BROWSER_CACHE = True

USE_BUILT = False
WRITE_LOG = True

LOG_PATH = '../server_logs.txt'

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
        log_queue.put(json.dumps(self.logs, ensure_ascii=False))
        return

    def finish_log(self, status, type, length):
        '''type: html, constjs, api, 404, not_allowed, post, ai, chat 都是字符串'''
        self.logs['status'] = status
        self.logs['type'] = type
        self.logs['resp_length'] = length
        self.logs['finish_time'] = format(time() * 1000, '.3f')
        log_queue.put(json.dumps(self.logs, ensure_ascii=False))
        return

    def do_POST(self) -> None:
        self.do_log()
        if(self.path != '/chat'):
            self.send_response(404)
            self.send_header('Connection', 'keep-alive')
            self.send_header('Content-Length', 13)
            self.end_headers()
            self.finish_log(404, 'post', 13)
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


def process_get_api(request: Request, path: str) -> None:
    # sleep(1)
    if (path.startswith('/api/expression_by_gene/')):
        path = path[len('/api/expression_by_gene/'):]
        print(f'API received: gene, {path}')
        path = path.upper()
        file_name = f'tmp-{randint(100000000000, 999999999999)}.pdf'
        result = violinPlotsingle(GENES_FORMATTED_TO_ORIGIN[path], './tmp/'+file_name)
        if(result[0]):
            png_bytes = pdf_to_png_bytes('../tmp/'+file_name)
            data = {'left': binToBase64(png_bytes), 'right': BLANK_PNG}
            response_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            status = 200
        else:
            status = 400
            error_msg = binary_to_str(result[1])
            if(error_msg==''):
                error_msg = 'Unknown error'
            response_body = json.dumps({'error': error_msg}, ensure_ascii=False).encode('utf-8')
        request.send_response(status)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        request.send_header('Content-Length', len(response_body))
        request.end_headers()
        request.finish_log(status, 'api', len(response_body))
        request.wfile.write(response_body)
        request.wfile.flush()
        return
    if (path.startswith('/api/expression_by_geneset/')):
        path = path[len('/api/expression_by_geneset/'):]
        print(f'API received: geneset, {path}')
        if (False):
            pass
        else:
            status = 400
            data = {'error': 'This function is not finished currently.'}
        request.send_response(status)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        result = json.dumps(data, ensure_ascii=False).encode('utf-8')
        request.send_header('Content-Length', len(result))
        request.end_headers()
        request.finish_log(status, 'api', len(result))
        request.wfile.write(result)
        request.wfile.flush()
        return
    if (path.startswith('/api/expression_by_multi/')):
        path = path[len('/api/expression_by_multi/'):]
        print(f'API received: exp_multi, {path}')
        data = format_input_multi(hexToStr(path))
        file_name = f'tmp-{randint(100000000000, 999999999999)}.pdf'
        result = dotPlotMulti(data, './tmp/'+file_name)
        if(result[0]):
            png_bytes = pdf_to_png_bytes('../tmp/'+file_name)
            data = {'left': binToBase64(png_bytes), 'right': BLANK_PNG}
            response_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            status = 200
        else:
            status = 400
            error_msg = binary_to_str(result[1])
            if(error_msg==''):
                error_msg = 'Unknown error'
            response_body = json.dumps({'error': error_msg}, ensure_ascii=False).encode('utf-8')
        request.send_response(status)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        request.send_header('Content-Length', len(response_body))
        request.end_headers()
        request.finish_log(status, 'api', len(response_body))
        request.wfile.write(response_body)
        request.wfile.flush()
        return
    if (path.startswith('/api/enrichment/')):
        path = path[len('/api/enrichment/'):]
        print(f'API received: enrichment, {hexToStr(path)}')
        json_data = json.loads(hexToStr(path))
        if (False):
            pass
        else:
            type_ = json_data['type']
            name = json_data['name']
            file_name = f'tmp-{randint(100000000000, 999999999999)}.pdf'
            if(type_==0):
                # beta cell
                if(name.endswith('dentity')):
                    rname = "Beta Cell Identity"
                if(name.endswith('liferation')):
                    rname = "Cell Proliferation"
                if(name.endswith('unction')):
                    rname = "Insulin Secretion"
                result = betaPathwaysPlot(rname, './tmp/'+file_name)
            if(type_==1):
                # cell death
                result = deathPathwaysPlot(name, './tmp/'+file_name)
            if(type_==2):
                # specific
                result = specificPathwaysPlot(name.replace('"',''), './tmp/'+file_name)
            if(type_==3):
                input_data = format_input_correlation(name)
                result = customGSEA(input_data, './tmp/'+file_name+'.csv', './tmp/'+file_name)
            if(result[0]):
                png_bytes = pdf_to_png_bytes('../tmp/'+file_name)
                data = {'middle': binToBase64(png_bytes)}
                response_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
                status = 200
            else:
                status = 400
                error_msg = binary_to_str(result[1])
                if(error_msg==''):
                    error_msg = 'Unknown error'
                response_body = json.dumps({'error': error_msg}, ensure_ascii=False).encode('utf-8')     
        request.send_response(status)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        request.send_header('Content-Length', len(response_body))
        request.end_headers()
        request.finish_log(status, 'api', len(response_body))
        request.wfile.write(response_body)
        request.wfile.flush()
        return
    if (path.startswith('/api/aa/')):
        path = path[len('/api/aa/'):]
        print(f'API received: aa, {hexToStr(path)}')
        data = format_input_correlation(hexToStr(path))
        file_name = f'tmp-{randint(100000000000, 999999999999)}.pdf'
        result = correlationAnalysis(data, 0, 0.1, './tmp/'+file_name+'.csv', './tmp/'+file_name)
        if(result[0]):
            png_bytes = pdf_to_png_bytes('../tmp/'+file_name)
            data = {'middle': binToBase64(png_bytes)}
            response_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            status = 200
        else:
            status = 400
            error_msg = binary_to_str(result[1])
            if(error_msg==''):
                error_msg = 'Unknown error'
            response_body = json.dumps({'error': error_msg}, ensure_ascii=False).encode('utf-8')
        request.send_response(status)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        request.send_header('Content-Length', len(response_body))
        request.end_headers()
        request.finish_log(status, 'api', len(response_body))
        request.wfile.write(response_body)
        request.wfile.flush()
        return
    if (path.startswith('/api/dexp/')):
        path = path[len('/api/dexp/'):]
        print(f'API received: dexp, {hexToStr(path)}')
        json_data = json.loads(hexToStr(path))
        pvalue = json_data['pvalue']
        fc = json_data['fc']
        chemical = json_data['chemical']
        control = HORMONES_TO_CONTROL[chemical]
        file_name = f'tmp-{randint(100000000000, 999999999999)}.pdf'
        result = degAnalysis(chemical, control, float(pvalue), float(fc), './tmp/'+file_name+'.csv', './tmp/'+file_name)
        if(result[0]):
            png_bytes = pdf_to_png_bytes('../tmp/'+file_name)
            data = {'left': binToBase64(png_bytes), 'right': BLANK_PNG}
            response_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            status = 200
        else:
            status = 400
            if(result[1].find(b"'from' must be")!=-1):
                result = [False, b'']
                result[1] = b'No data found. Try making p-value larger or FC smaller.'
            error_msg = binary_to_str(result[1])
            if(error_msg==''):
                error_msg = 'Unknown error'
            response_body = json.dumps({'error': error_msg}, ensure_ascii=False).encode('utf-8')
        request.send_response(status)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        request.send_header('Content-Length', len(response_body))
        request.end_headers()
        request.finish_log(status, 'api', len(response_body))
        request.wfile.write(response_body)
        request.wfile.flush()
        return
    pass


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


server = ThreadingHTTPServer(('0.0.0.0', PORT), Request)
start_new_thread(server.serve_forever, ())
start_new_thread(write_logs, ())
start_new_thread(remove_tmp_files, ())
while True:
    sleep(10)

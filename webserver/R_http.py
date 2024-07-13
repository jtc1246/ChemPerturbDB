from myHttp import http  # pip install myHttp
from mySecrets import toHex  # pip install mySecrets
import json
from copy import deepcopy
import subprocess
from time import sleep

__all__ = [
    'violinPlotsingle',
    'dotPlotMulti',
    'betaPathwaysPlot',
    'deathPathwaysPlot',
    'specificPathwaysPlot',
    'customGSEA',
    'degAnalysis',
    'correlationAnalysis'
]


BASE_URL = 'http://127.0.0.1:2000'
# BASE_URL = 'http://jtc1246.com:9020'
RUN_R_LOCALLY = True

command = '''
cd ..
Rscript functions_0607.R
'''


if RUN_R_LOCALLY:
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    output = ''
    while (True):
        a = process.stdout.read(10)
        if(len(a)!=0):
            output += a.decode('utf-8')
            if(output.find('Server started on')!=-1):
                break
    print("R start successfully")



json_data = {
    'f': 0,
    'p1': '',
    'p2': '',
    'p3': '',
    'p4': '',
    'p5': '',
    'p6': ''
}


def violinPlotsingle(name, path):
    # 只有 INS 能运行, 别的都 ERROR: missing value where TRUE/FALSE needed
    data = deepcopy(json_data)
    data['f'] = 1
    data['p1'] = name
    data['p6'] = path
    url = toHex(json.dumps(data))
    url = BASE_URL + '/' + url
    response = http(url, Timeout=3600000, Decode=False)
    if(response['status']<0):
        return (False, b'')
    if(response['code']==200):
        return (True, b'')
    if(response['code']==500):
        return (False, response['text'])
    return (False, b'')


def dotPlotMulti(name, path):
    # 经过简单测试没问题, 更换了一些其它的 gene 测试, 1个 2个 多个 也都测试过
    data = deepcopy(json_data)
    data['f'] = 2
    data['p1'] = name
    data['p6'] = path
    url = toHex(json.dumps(data))
    url = BASE_URL + '/' + url
    response = http(url, Timeout=3600000, Decode=False)
    if(response['status']<0):
        return (False, b'')
    if(response['code']==200):
        return (True, b'')
    if(response['code']==500):
        return (False, response['text'])
    return (False, b'')


def betaPathwaysPlot(name, path):
    # 可选值有 "Beta Cell Identity" "Insulin Secretion"  "Cell Proliferation", 区分大小写
    # 经测试没问题
    data = deepcopy(json_data)
    data['f'] = 3
    data['p1'] = name
    data['p6'] = path
    url = toHex(json.dumps(data))
    url = BASE_URL + '/' + url
    response = http(url, Timeout=3600000, Decode=False)
    if(response['status']<0):
        return (False, b'')
    if(response['code']==200):
        return (True, b'')
    if(response['code']==500):
        return (False, response['text'])
    return (False, b'')


def deathPathwaysPlot(name, path):
    # 可选值有 5 个, 测试了都没问题
    data = deepcopy(json_data)
    data['f'] = 4
    data['p1'] = name
    data['p6'] = path
    url = toHex(json.dumps(data))
    url = BASE_URL + '/' + url
    response = http(url, Timeout=3600000, Decode=False)
    if(response['status']<0):
        return (False, b'')
    if(response['code']==200):
        return (True, b'')
    if(response['code']==500):
        return (False, response['text'])
    return (False, b'')


def specificPathwaysPlot(name, path):
    # 有 60 个可选值, 需要去掉引号,
    # 随机测试了几个, 部分会失败, 概率应该在 20% 以内,  ERROR: \x1b[1m\x1b[22mFaceting variables must have at least one value.
    data = deepcopy(json_data)
    data['f'] = 5
    data['p1'] = name
    data['p6'] = path
    url = toHex(json.dumps(data))
    url = BASE_URL + '/' + url
    response = http(url, Timeout=3600000, Decode=False)
    if(response['status']<0):
        return (False, b'')
    if(response['code']==200):
        return (True, b'')
    if(response['code']==500):
        return (False, response['text'])
    return (False, b'')


def customGSEA(name, csv_path, path):
    data = deepcopy(json_data)
    data['f'] = 6
    data['p1'] = name
    data['p2'] = csv_path
    data['p6'] = path
    url = toHex(json.dumps(data))
    url = BASE_URL + '/' + url
    response = http(url, Timeout=3600000, Decode=False)
    if(response['status']<0):
        return (False, b'')
    if(response['code']==200):
        return (True, b'')
    if(response['code']==500):
        return (False, response['text'])
    return (False, b'')


def degAnalysis(name1, name2, p_value, fc, csv_path, path):
    # 测试了额外 3 个, 2 个可以, 1 个不行 (严格来说是3组, 每组control对应的两个hormone都测试了)
    # 随机更换了一些 p_value 和 fc, 没问题
    # ERROR: 'from' must be a finite number
    data = deepcopy(json_data)
    data['f'] = 7
    data['p1'] = name1
    data['p2'] = name2
    data['p3'] = p_value
    data['p4'] = fc
    data['p5'] = csv_path
    data['p6'] = path
    url = toHex(json.dumps(data))
    url = BASE_URL + '/' + url
    response = http(url, Timeout=3600000, Decode=False)
    if(response['status']<0):
        return (False, b'')
    if(response['code']==200):
        return (True, b'')
    if(response['code']==500):
        return (False, response['text'])
    return (False, b'')


def correlationAnalysis(gene_list, fc, p_value, csv_path, path):
    # gene_list 输入 python 的 list 就行, fc 和 p_value 随机更换了一些测试, 没问题
    # gene_list 应该对输入长度有要求, 但是具体规则不是很明确, 有的时候 2 个可以, 有的时候 3个 4个 都不行
    # ERROR: You should have at least two distinct break values.
    data = deepcopy(json_data)
    data['f'] = 8
    data['p1'] = gene_list
    data['p2'] = fc
    data['p3'] = p_value
    data['p4'] = csv_path
    data['p6'] = path
    url = toHex(json.dumps(data))
    url = BASE_URL + '/' + url
    response = http(url, Timeout=3600000, Decode=False)
    if(response['status']<0):
        return (False, b'')
    if(response['code']==200):
        return (True, b'')
    if(response['code']==500):
        return (False, response['text'])
    return (False, b'')

# 所有的, 都是 http 200 可以认为成功, 500 失败
# 如果 500, body 有基本的报错信息


if __name__ == '__main__':
    print("test started")
    x1 = violinPlotsingle('INS', './test01.pdf')
    x2 = dotPlotMulti("AC245140.1,CT45A1,INS,CT45A2,AC010889.1,PRY2,MT-ATP6,myB22", './test02.pdf')
    x3 = betaPathwaysPlot("Cell Proliferation", './test03.pdf')
    x4 = deathPathwaysPlot("Pyroptosis Signaling Pathway", './test04.pdf')
    x5 = specificPathwaysPlot("UVB-Induced MAPK Signaling", './test05.pdf')
    x6 = customGSEA(["ERO1B","STX1A","EXOC1","PTPRN","EXOC2","PCSK1","PTPRN2","PCSK2","ACVR1C","FFAR1","PCSK1N","RAB27A","P4HB","RAB11B","RIMS2","TMEM27","RAF1","SLC30A5"],'tmp01.csv', './test06.pdf')
    x7 = degAnalysis("Ghrelin", "endoc3BC17", 0.8, 0.67, "./tmp01.csv", './test07.pdf')
    x8 = correlationAnalysis(['SLC2A7', 'AC007996.1', 'CDH2', 'DSG3', 'CELF4'], 0.7, 0.45, "./tmp01.csv", './test08.pdf')
    print("test finished")

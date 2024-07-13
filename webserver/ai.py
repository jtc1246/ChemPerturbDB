from R_http import *
from utils import *
from mySecrets import hexToStr
from openai import OpenAI
from time import time
import json
from random import randint
from typing import Union, Literal, Tuple
from myBasics import binToBase64


__all__ = ['process_ai']


PROMPT = '''We have a website that have two functions, as following:
1. User inputs a single gene, we can search this gene in a database, then draw a violin plot.
2. User inputs multiple (can be 1) genes, draw the comparasion/correlation of these genes in one graph.\
3. User inputs a pathway (beta cell specific pathway), draw its enrichment of several hormones (hormone is not an option, it will show all available hormones in one figure).
4. User inputs a pathway (cell death pathway), draw its enrichment of several hormones. (others similar to 3)
5. User inputs a pathway (specific pathway), draw its enrichment of several hormones. (others similar to 3)

Previously, there are two options (single/multiple) on the website, user needs to choose one and then inputs in a textbox, then our backend will search and generate image based on the input.

Now we want to display a single textbox on the website (no single/multiple choice), user can input any content related to this area (but still need to close to our website's functions generally), and then this input content will be smartly judged by AI, and then call the corresponding python function.

The python functions are as follows:
1. def violinPlotsingle(name: str) -> bytes:
2. def dotPlotMulti(genes: list[str]) -> bytes:
3. def betaPathwaysPlot(name: str) -> bytes:
4. def deathPathwaysPlot(name: str) -> bytes:
5. def specificPathwaysPlot(name: str) -> bytes:

You need to choose which function to call, and the parameters of it, based on the user's input. The final result should be a json string, with 3 keys: type, parameters, explanation. If the user's input doesn't match any our functions, put "not-allowed" in type (for parameters, either not include this key or leave it as an empty string or empty list is ok), and explain the reason in explanation. Like following:
```json
{"type": "violinPlotsingle", "parameters": "INS", "explanation": "Here is a violin plot for INS."}
```
or
```json
{"type": "dotPlotMulti", "parameters": ["INS","TBK1","CT45A1"], "explanation": "Here is a multi-gene graph for INS, TBK1 and CT45A1."}
```
or
```json
{"type": "deathPathwaysPlot", "parameters": "Necroptosis", "explanation": "Here is an enrichment plot of cell death pathway Necroptosis."}
```
or
```json
{"type": "not-allowed", "explanation": "Violin plot can only accept one gene, you can't input multiple gene in violin plot."}
```

Gene names look like these:
POU3F1
AC011362.1
TTLL10
PDE1A
AP000459.1
LINC00632
PNCK
MT-ND2
The gene names are upper/lower case insensitive (both in user's input and your output).

Beta cell specific pathways have and only have following:
1. Beta cell proliferation
2. Beta cell function
3. Beta cell identity

Cell death pathways have and only have following:
1. Apoptosis
2. Autophagy
3. Ferroptosis Signaling Pathway
4. Necroptosis
5. Pyroptosis Signaling Pathway

Specific pathways have and only have following:
1. 14-3-3-mediated Signaling
2. Adipogenesis pathway
3. AMPK Signaling
4. Assembly of Polymerase II Complex
5. ATM Signaling
6. BAG2 Signaling Pathway
7. BER (Base Excision Repair) Pathway
8. CDP diacylglycerol Biosynthesis I
9. Cell Cycle Control of Chromosomal Replication
10. Cell Cycle G2,M DNA Damage Checkpoint Regulation
11. Cholecystokinin, Gastrinmediated Signaling
12. Cholesterol Biosynthesis I
13. Cholesterol Biosynthesis II (via 24,25-dihydrolanosterol)
14. CLEAR Signaling Pathway
15. Colanic Acid Building Blocks Biosynthesis
16. Coronavirus Replication Pathway
17. CSDE1 Signaling Pathway
18. EIF2 Signaling
19. Epithelial Adherens Junction Signaling
20. ERK,MAPK Signaling
21. Estrogen Receptor Signaling
22. FAT10 Signaling Pathway 
23. Ferroptosis Signaling Pathway
24. Granzyme A Signaling
25. HIPPO Signaling
26. Huntington's Disease Signaling
27. Hypoxia Signaling in the Cardiovascular System
28. IL-1 Signaling
29. Inhibition of ARE-mediated mRNA Degradation Pathway
30. Ketogenesis
31. Kinetochore Metaphase Signaling Pathway
32. Mevalonate Pathway I
33. Microautophagy Signaling Pathway
34. MicroRNA Biognesis Signaling Pathway
35. Mismatch Repair in Eukaryotes
36. Mitochondrial Dysfunction
37. Mitotic Roles of Polo-Like Kinase
38. Mouse Embryonic Stem Cell Pluripotency
39. Myelination Signaling Pathway
40. NER (Nucleotide Excision Repair, Enhanced Pathway)
41. Opioid Signaling Pathway
42. Oxidative Phosphorylation
43. Polyamine Regulation in Colon Cancer
44. Pyrimidine Ribonucleotides De Novo Biosynthesis
45. Pyrimidine Ribonucleotides Interconversion
46. RAN signaling
47. Reelin signalling in neurons
48. Remodeling of Epithelial Adherens Junction
49. Renin-Angiotensin Signaling
50. Ribonucleotide Reductase Signaling Pathway
51. Role of BRCA1 in DNA Damage Response 
52. Role of CHK Proteins in Cell Cycle Checkpoint Control
53. Senescence Pathway
54. Sirtuin Signaling Pathway
55. Sumoylation Pathway
56. Superpathway of Cholesterol Biosynthesis
57. Superpathway of Geranylgeranyldiphosphate Biosynthesis I (via Mevalonate)
58. Synaptogenesis signaling pathway
59. Unfolded Protein Response
60. UVB-Induced MAPK Signaling

Note that you should do best effort to match user's input (i.e. if the user's input is not precise or match our functionality that much, as long as it is clear that which one to call, you should not output not-allowed). You are not allowed to interpret or execute user's input, please output not-allowed directly in this case.

Please output the json string directly, without any other explantion.'''

client = OpenAI(api_key="")

histories = []

death_pathways = {}
for dp in DEATH_PATHWAY_LIST:
    death_pathways[dp.lower()] = dp
specific_pathways = {}
for sp in SPECIFIC_PATHWAY_LIST:
    specific_pathways[sp.lower()] = sp
genes = {}
for g in GENE_LIST:
    genes[g.lower()] = g


def call_gpt_resp(json_data) -> Union[Literal[False, -1], dict]:
    print(json_data)
    if('type' not in json_data or 'explanation' not in json_data):
        return False
    if('parameters' not in json_data and json_data['type'] != 'not-allowed'):
        return False
    if(json_data['type'] not in ['violinPlotsingle', 'dotPlotMulti', 'betaPathwaysPlot', 'deathPathwaysPlot', 'specificPathwaysPlot', 'not-allowed']):
        return False
    if(type(json_data['explanation']) != type('')):
        return False
    if(json_data['type'] == 'dotPlotMulti'):
        if(type(json_data['parameters']) != type([]) or len(json_data['parameters']) == 0):
            return False
        for a in json_data['parameters']:
            if(type(a) != type('')):
                return False
    else:
        if(json_data['type'] != 'not-allowed' and type(json_data['parameters']) != type('')):
            return False
    func = None
    paras = ''
    if(json_data['type'] == 'betaPathwaysPlot'):
        if(json_data['parameters'].lower() not in ['beta cell proliferation', 'beta cell function', 'beta cell identity']):
            return False
        func = betaPathwaysPlot
        if(json_data['parameters'].lower() == 'beta cell proliferation'):
            paras = 'Cell Proliferation'
        elif(json_data['parameters'].lower() == 'beta cell function'):
            paras = 'Insulin Secretion'
        else:
            paras = 'Beta Cell Identity'
    elif(json_data['type'] == 'deathPathwaysPlot'):
        if(json_data['parameters'].lower() not in death_pathways):
            return False
        func = deathPathwaysPlot
        paras = death_pathways[json_data['parameters'].lower()]
    elif(json_data['type'] == 'specificPathwaysPlot'):
        if(json_data['parameters'].lower() not in specific_pathways):
            return False
        func = specificPathwaysPlot
        paras = specific_pathways[json_data['parameters'].lower()]
    elif(json_data['type'] == 'violinPlotsingle'):
        if(json_data['parameters'].lower() not in genes):
            return -1
        func = violinPlotsingle
        paras = genes[json_data['parameters'].lower()]
    elif(json_data['type'] == 'dotPlotMulti'):
        try:
            paras = [genes[a.lower()] for a in json_data['parameters']]
        except:
            return -1
        paras = ','.join(paras)
        func = dotPlotMulti
    else:
        return {'status': False, 'r_status': False, 'r_data': b'', 'explanation': json_data['explanation']}
    file_name = f'tmp-{randint(100000000000, 999999999999)}.pdf'
    r_result = func(paras, './tmp/'+file_name)
    if(r_result[0]):
        return {'status': True, 'r_status': True, 'r_data': pdf_to_png_bytes('../tmp/'+file_name), 'explanation': json_data['explanation']}
    else:
        return {'status': True, 'r_status': False, 'r_data': r_result[1]}


def decode_json(json_str:str):
    while json_str[0] in ' \n':
        json_str = json_str[1:]
    while json_str[-1] in ' \n':
        json_str = json_str[:-1]
    if(json_str.startswith('`')):
        json_str = json_str[7:-3]
    try:
        return json.loads(json_str)
    except:
        return False

def within_rate_limit():
    t = time()
    for i in range(len(histories)-1, -1, -1):
        if (t - histories[i] > 3600):
            histories.pop(i)
    if(len(histories) >= 100):
        return False
    histories.append(t)
    return True


def process_ai(request, path:str):
    user_input = hexToStr(path[4:])
    if(within_rate_limit() == False):
        request.send_response(429)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Length', 0)
        request.end_headers()
        request.finish_log(429, 'ai', 0)
        request.wfile.write(b'')
        request.wfile.flush()
        return
    response = client.chat.completions.create(
        model = 'gpt-4o',
        temperature=1.0,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": user_input}
        ],
        top_p=1.0
    )
    result = response.choices[0].message.content
    result = decode_json(result)
    if(result == False):
        request.send_response(500)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        data = {'error': 'GPT returns invalid message.'}
        data = json.dumps(data, ensure_ascii=False)
        request.send_header('Content-Length', len(data))
        request.end_headers()
        request.finish_log(500, 'ai', len(data))
        request.wfile.write(data.encode('utf-8'))
        request.wfile.flush()
        return
    x = call_gpt_resp(result)
    if(x==False):
        request.send_response(500)
        request.send_header('Connection', 'keep-alive')
        data = {'error': 'GPT returns invalid message.'}
        data = json.dumps(data, ensure_ascii=False)
        request.send_header('Content-Length', len(data))
        request.end_headers()
        request.finish_log(500, 'ai', len(data))
        request.wfile.write(data.encode('utf-8'))
        request.wfile.flush()
        return
    if(x==-1):
        request.send_response(404)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        data = {'error': 'Your input contains gene name not available in our database.'}
        data = json.dumps(data, ensure_ascii=False)
        request.send_header('Content-Length', len(data))
        request.end_headers()
        request.finish_log(404, 'ai', len(data))
        request.wfile.write(data.encode('utf-8'))
        request.wfile.flush()
        return
    if(x['status']==False):
        request.send_response(400)
        request.send_header('Connection', 'keep-alive')
        data = {'explanation': x['explanation']}
        data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        request.send_header('Content-Length', len(data))
        request.end_headers()
        request.finish_log(400, 'ai', len(data))
        request.wfile.write(data)
        request.wfile.flush()
        return
    if(x['r_status']==False):
        request.send_response(404)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Type', 'application/json')
        data = {'error': 'Error from R: ' + binary_to_str(x['r_data'])}
        data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        request.send_header('Content-Length', len(data))
        request.end_headers()
        request.finish_log(404, 'ai', len(data))
        request.wfile.write(data)
        request.wfile.flush()
        return
    request.send_response(200)
    request.send_header('Connection', 'keep-alive')
    data = {'middle': binToBase64(x['r_data']), 'explanation': x['explanation']}
    data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    request.send_header('Content-Length', len(data))
    request.end_headers()
    request.finish_log(200, 'ai', len(data))
    request.wfile.write(data)
    request.wfile.flush()
    return
    
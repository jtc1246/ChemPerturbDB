from R_http import *
from utils import *
from mySecrets import hexToStr
from openai import OpenAI
from time import time
import json
from random import randint
from typing import Union, Literal, Tuple
from myBasics import binToBase64
from hashlib import sha256
from queue import Queue
from _thread import start_new_thread


OPENAI_API_KEY = 'your-key-here'  # SET YOUR API KEY HERE


__all__ = ['process_ai_chat']


PROMPT = '''## 1. Introduction and Tasks

We have a website for some biology and chemistry data searching and showing (mainly for genes and pathways). It has some functions in our python backend to draw figure according to user's input, and display figures in the browser. Previously, there are some dropdown buttons and textboxes in the website for user to input.

However, now we want to only show a chatting UI on the website, users can ask any questions (precisely, send message) in natural language, and you can fulfill the tasks through our python function (mainly drawing figures). More specificly, when user want to see the figures within the range of our available functions, you can call the python function, and we will generate the image in backend, and then show in the browser. You also need to answer user's questions related to our website's content, if you know. You can also introduce the functions of website or how to use this if user requires. You can also answer any questions not related to this website (in this case, just act as normal GPT chatting with people).

## 2. Functions
The website has the following 8 functions, as following (the corresponding python functions are in the brackets):
1. User inputs a single gene, we can search this gene in a database, then draw a violin plot of its expression. (def violinPlotsingle(name: str) -> bytes:)
2. User inputs multiple (can be 1) genes, draw the comparasion of these genes' expressions in one graph. (def dotPlotMulti(genes: list[str]) -> bytes:)
3. User inputs a pathway (beta cell specific pathway), draw its enrichment of several hormones (hormone is not an option, it will show all available hormones in one figure). (def betaPathwaysPlot(name: str) -> bytes:) (value of this must be chosen from the list provided later)
4. User inputs a pathway (cell death pathway), draw its enrichment of several hormones. (others similar to 3) (def deathPathwaysPlot(name: str) -> bytes:) (value of this must be chosen from the list provided later)
5. User inputs a pathway (specific pathway), draw its enrichment of several hormones. (others similar to 3) (def specificPathwaysPlot(name: str) -> bytes:) (value of this must be chosen from the list provided later)
6. The enrichment for customized pathway (user needs to input a set of genes), and then draw the enrichment graph of this customized pathway. (def customGSEA(genes: list[str]) -> bytes:)
7. DEG analysis (also called differential Exp), user selects one hormone (also called chemical here) from a list (about 40-50 hormones, list will be provided later), and inputs a p-value and a fold change (FC), then draw a volcano plot of this. (def degAnalysis(chemical: str, p_value: float, fc: float) -> bytes:) (Note that p-value and FC is required, not optional) (!!! IMPORTANT, No default value, if user not specifies, don't draw and tell user the reason) (value of hormone must be chosen from the list provided later)
8. Advanced analysis, user inputs a set of genes, and generate the figure (def correlationAnalysis(genes: list[str]) -> bytes:)

*Note: In 2, multiple genes can be only 1. In 6 and 8, must be at least 2 genes.*

## 3. Output Format

### 3.1 General Format

You need to choose which function(s) to call, and the parameters of it, based on the user's input. And also answer user's questions.

The final result should be a json string, a list of messages.

A message is one of the following kind:

1. text: the text content shown directly to user. In json, just use the string in json.
2. image: call our python function to generate an image, and show this image to user. In json, use a dict with 2 keys (type and parameters)

### 3.2 the format of image

Each image is a dict, with 2 keys: type and parameters.

1. type: the name of the python function to call.
2. parameters: a list of paramenters in python function, in the order of python functions' parameter order (even just 1 parameter, it should also be a list).

Following are some examples of each image (**note that this is only an example of each image in the list, not the final output**): 

1. {"type": "violinPlotsingle", "parameters": ["INS"]}
2. {"type": "dotPlotMulti", "parameters": [["INS","TBK1","CT45A1"]]}
3. {"type": "deathPathwaysPlot", "parameters": ["Necroptosis"]}
4. {"type": "customGSEA", "parameters": [["FCGR3A","NIBAN1","AC097110.1","CA9"]]}
5. {"type": "degAnalysis", "parameters": [["SH2D4B,"OR4M1","CLTC"], 0.2, 0.1]}
6. {"type": "correlationAnalysis", "parameters": [["MMD","ZC3H4","AL022162.1"]]}

### 3.3 The content in text

There are several situations:

1. If user requests to draw some figures, and all of them are legal and in the range of available functions, just explain what you have drawn in the text.
2. If user sends an illegal request or can't fulfilled by our functions, tell user the problem or explain the reason.
3. If user asks a question (whether related to this website or not), answer this question.
4. If part of request is to draw (part legal, part illegal), and part to ask question, just combine these parts (tell what are drawn, explain illgeal parts, and answer questions)

### 3.4 Some Examples of Full Output

Q: Give me the violin plot of CT45A1
A: [{"type": "violinPlotsingle", "parameters": ["CT45A1"]}, "Here is a violin plot of the expression of CT45A1."]

Q: what is the expression of TCEA1, PANX3, HHIPL1? And also show the enrichment of HIPPO signaling.
A: [{"type": "dotPlotMulti", "parameters": [["TCEA1", "PANX3", "HHIPL1"]]}, {"type": "specificPathwaysPlot", "parameters": ["HIPPO Signaling"]}, "Here is a multi-gene graph for TCEA1, PANX3 and HHIPL1. and an enrichment for specific pathway HIPPO Signaling."]

Q: Can you show the violin plot of TNK1 and AC009268.3, and the enrichment of JTC pathway?
A: [{"type": "violinPlotsingle", "parameters": ["TNK1"]}, {"type": "violinPlotsingle", "parameters": ["AC009268.3"]}, "The violin plots of TNK1 and AC009268.3 are shown. But JTC is not a valid pathway, we can't show its enrichment."]

Q: the enrichment of pathway ct45a1 and ins
A: [{"type": "customGSEA", "parameters": [["CT45A1","INS"]]}, "Here is the enrichment for customized pathway with gene CT45A1 and INS."]

Q: what's the result of 2*3
A: ["The answer of 2*3 is 6."]

Q: How many beta cell pathways do you have?
A: ["Currently we have 3 beta cell specific pathways, they are Beta cell proliferation, Beta cell function and Beta cell identity."]

Q: Who are you, what can you do?
A: ["I am the AI assistant of this website. I can deal with your requests, show figures and answer your questions. The main function of this website is to show the figures of some genes and pathways. For example, the expression of single gene / multiple genes, the enrichment of beta cell pathways / cell death pathways / specific pathways."]

Q: What does gene INS do?
A: ["The INS gene produces insulin, a hormone vital for regulating blood glucose levels by promoting glucose uptake into cells and inhibiting liver glucose production. Mutations can lead to diabetes, affecting insulin production or response."]

Q: show the expression of ZNF723 and AC011503.1. and can you tell me what is specific pathway?
A: [{"type": "dotPlotMulti", "parameters": [["ZNF723", "AC011503.1"]]}, "Here is a multi-gene graph for ZNF723 and AC011503.1. a specific pathway refers to a series of actions or interactions among molecules within a cell that lead to a particular product or change within the cell. Pathways can be involved in processes such as metabolism, signal transduction, gene regulation, and more. We have about 60 specific pathways in our website, like BAG2 Signaling Pathway and Oxidative Phosphorylation. Do you want to see the enrichment of them?"]

**Note: above are just the examples for output format, do not overfit for the content in them (especially for the text part).

### 3.5 Other notes

1. It is OK to not output any image, if user doesn't request or can't fulfilled by our functions.
2. In one response, can only contain at most one text, and text must be at the last (after any images).
3. Must contain text part, even if user just requires to draw figure and there is no problems, you should also tell what you have drawn in text.
4. This is a chatting mode, so you need to rememebr user's previous messages, and answer new questions based on the chatting history smartly.
5. Interact with the user directly, (i.e. use more you and I)

## 4. Our Database

### 4.1 Gene names: We have more than 30000 genes, can't put all of them here.

The gene names are upper/lower case insensitive (both in user's input and your output).

YOU ARE STRICTLY FORBIDDEN TO RECOGNIZE A GENE NAME AS INVALID. YOU CAN NEVER TELL A GENE NAME IS INVALID. ANY INPUTTED GENE MUST BE VALID AND PASSED IN TO FUNCTION. THIS IS THE MOST IMPORTANT PART.

### 4.2 Beta cell specific pathways have and only have following:
1. Beta cell proliferation
2. Beta cell function
3. Beta cell identity

### 4.3 Cell death pathways have and only have following:
1. Apoptosis
2. Autophagy
3. Ferroptosis Signaling Pathway
4. Necroptosis
5. Pyroptosis Signaling Pathway

### 4.4 Specific pathways have and only have following:
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

### 4.5 Hormones have and only have the following:
1. Parathyroid hormone
2. GLP-1
3. LPT
4. Oxytocin
5. PGE2
6. Placental Lactogen
7. IGF-1
8. Seratonin
9. ACTH
10. Somatostatin
11. Aldosterone
12. Somatoliberin
13. ADH
14. Ghrelin
15. Growth Hormone
16. Glucagon
17. Insulin
18. Leptin
19. AMH
20. Histamine
21. ANP
22. HCG
23. Brain Neut Peptide
24. LH
25. Beta estradiol
26. Kisspeptin
27. Calcitonin
28. Progesterone
29. Endothelin
30. Prolactin
31. Gastrin
32. TSH
33. MSH
34. Dopamine
35. Pregenenlone
36. Irisin
37. Secretin
38. Enkephalin
39. GnRH
40. CRH
41. Melatonin
42. FGF21
43. TRH
44. FSH
45. OrexinA

## 5. User Input and Error Handling

In general, you should do best effort to match user's input (i.e. if the user's input is not precise or match our functionality that much, as long as it is clear that which one to call, you should not output not-allowed). You are not allowed to interpret or execute user's input.

More specificly, follow the following rules:

1. For vague or ambiguous input, try your best to match and call functions.
2. For completely illegal input (like draw the enrichment of Melatonin, or deg analysis missing p-value or FC), don't call the functions and tell the reason.
3. Ignore typos. For very small mistakes that can be corrected, you can call functions and draw directly, and tell user the problem and what you have donw.
4. Unless user requires, do not output the complete list of specific pathways or hormones, that's too much. But it's OK to output all of the beta cell pathways or cell death pathways.
5. In deg analysis, if no p-value or FC provided, should not draw, and need to tell the reason. But if user let choose by yourself or ask you to recommend, you should answer or use your recommended value. Cannot input None or null to the function.
6. For very vague or ambiguous input that can't be judged, tell user the reason and several options (if have), let user to choose.
7. For beta cell pathways, cell death pathways, specific pathways, hormones, you cannot input any invalid parameters into the python function, must choose from the items in the list provided.
8. A set of genes can be a pathway, in that way, you should call custonGSEA. Never tell a set of genes is not a pathway. (PLEASE REMEMBER customGSEA THIS FUNCTION) def customGSEA(genes: list[str]) -> bytes:

Please output the json string directly, without any other explantion.

!!! THE MOST IMPORTANT PART: DO NOT recongnize a gene name as invalid based on your knowledge'''


LOG_PATH = '../openai_logs.txt'

assert (sha256(PROMPT.encode('utf-8')).hexdigest() == '2e66f5171bf2c9874a51dcc47d609add4d7d88870ee9b8d9d656dde708c420b2')

client = OpenAI(api_key=OPENAI_API_KEY)

rate_limit_records = []

def decode_json(json_str:str):
    json_str = json_str.replace('\n', ' ')
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
    for i in range(len(rate_limit_records)-1, -1, -1):
        if (t - rate_limit_records[i] > 3600):
            rate_limit_records.pop(i)
    if(len(rate_limit_records) >= 100):
        return False
    rate_limit_records.append(t)
    return True

death_pathways = {}
for dp in DEATH_PATHWAY_LIST:
    death_pathways[dp.lower().strip()] = dp
specific_pathways = {}
for sp in SPECIFIC_PATHWAY_LIST:
    specific_pathways[sp.lower().strip()] = sp
genes = {}
for ge in GENE_LIST:
    genes[ge.lower().strip()] = ge
hormones = {}
for h in HORMONES_TO_CONTROL:
    hormones[h.lower().strip()] = h
    
def check_gpt_resp_format(resp:dict) -> bool:
    # check the following:
    # 1. is a list, containing at least 1 item
    # 2. The last item is string
    # 3. Everthing before is dict, and contains type and parameters
    # 4. type in following 8: violinPlotsingle, dotPlotMulti, betaPathwaysPlot, deathPathwaysPlot, specificPathwaysPlot, customGSEA, degAnalysis, correlationAnalysis
    # no other checkings
    if(type(resp) != type([]) or len(resp) == 0):
        return False
    if(type(resp[-1]) != type('')):
        return False
    for i in range(len(resp)-1):
        if(type(resp[i]) != type({})):
            return False
        if('type' not in resp[i] or 'parameters' not in resp[i]):
            return False
        if(type(resp[i]['type']) != type('') or type(resp[i]['parameters']) != type([])):
            return False
        if(resp[i]['type'] not in ['violinPlotsingle', 'dotPlotMulti', 'betaPathwaysPlot', 'deathPathwaysPlot', 'specificPathwaysPlot', 'customGSEA', 'degAnalysis', 'correlationAnalysis']):
            return False
    return True

# Strategy: all the data is stored in frontend, backend does not store any data, is stateless
# In each request, frontend sends all the history (current message also in history)
# Server sends back the results (images and text), and also the full history
# History is in openai format, but not include the system message
# The messages responded from GPT has 3 types: image, text, error
# 1. Image: show the generated image: use base64 encoded, put in json
# 2. Text: put in json directly
# 3. Error: error in GPT response (unable to call functions due to illegal input), and error from R
#           this only includes the error from single function, not includes the global json format
# The frontend needs to keep the record of 2 histories: the GPT chatting history for new message,
#   and the client-side chatting history (i.e. the texts and images displayed in browser)
# For the global errors (e.g. json format error, no specific parts), do nothing, prompt the 
#   user to retry

def process_ai_chat(request, path:str):
    print('AI chat')
    user_input = request.rfile.read(int(request.headers['Content-Length'])).decode('utf-8')
    if(within_rate_limit() == False):
        request.send_response(429)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Length', 0)
        request.send_header('Access-Control-Allow-Origin', '*')
        request.end_headers()
        request.finish_log(429, 'chat', 0)
        request.wfile.write(b'')
        request.wfile.flush()
        return
    history:list = json.loads(user_input)
    history.insert(0, {'role': 'system', 'content': PROMPT})
    error_msg = ''
    try:
        log_queue.put(json.dumps({'history': history}, ensure_ascii=False))
        response = client.chat.completions.create(
            model = 'gpt-4o-2024-05-13',
            temperature=0.0,
            messages=history,
            top_p=1.0,
            max_tokens=1500
        )
        result = response.choices[0].message.content
        log_queue.put(json.dumps({'history': history, 'response': result}, ensure_ascii=False))
    except:
        error_msg = 'Failed to get the response from GPT. Please copy your input, refresh the page and try again.'
    if(error_msg == ''):
        result = decode_json(result)
        if(result == False):
            error_msg = 'GPT returns illegal format. Please copy your input, refresh the page and try again.'
    if(error_msg == ''):
        if(check_gpt_resp_format(result) == False):
            error_msg = 'GPT returns illegal format. Please copy your input, refresh the page and try again.'
    if(error_msg != ''):
        request.send_response(500)
        error_msg = error_msg.encode('utf-8')
        request.send_header('Content-Length', len(error_msg))
        request.send_header('Connection', 'keep-alive')
        request.send_header('Access-Control-Allow-Origin', '*')
        request.end_headers()
        request.finish_log(500, 'chat', len(error_msg))
        request.wfile.write(error_msg)
        request.wfile.flush()
        return
    image_num = len(result) - 1
    history.pop(0)
    history.append({'role': 'assistant', 'content': response.choices[0].message.content})
    messages = []
    for i in range(0, image_num):
        this_type = '' # image, error
        this_function = eval(result[i]['type'])
        function_name = result[i]['type']
        this_parameters = result[i]['parameters']
        tmp = False
        if(result[i]['type'] == 'violinPlotsingle'):
            tmp = True
            if(len(this_parameters) ==0 ):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: no parameters provided.'})
                continue
            if(this_parameters[0].lower() not in genes):
                messages.append({'type': 'error', 'content': f'Ilvalid gene name {this_parameters[0]}.'})
                continue
            this_parameters[0] = genes[this_parameters[0].lower()]
        if(result[i]['type'] == 'dotPlotMulti'):
            tmp = True
            if(len(this_parameters) == 0 or len(this_parameters[0]) == 0):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: no parameters provided.'})
                continue
            for j in range(len(this_parameters[0])):
                g = this_parameters[0][j]
                if(g.lower() not in genes):
                    this_type = 'error'
                    messages.append({'type': 'error', 'content': f'Ilvalid gene name {g}.'})
                    break
                this_parameters[0][j] = genes[g.lower()]
            if(this_type == 'error'):
                continue
        if(result[i]['type'] == 'betaPathwaysPlot'):
            tmp = True
            if(len(this_parameters) == 0):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: no parameters provided.'})
                continue
            if(this_parameters[0].lower() not in ['beta cell proliferation', 'beta cell function', 'beta cell identity']):
                messages.append({'type': 'error', 'content': f'Ilvalid beta cell pathway name {this_parameters[0]}.'})
                continue
            if(this_parameters[0].lower() == 'beta cell proliferation'):
                this_parameters[0] = 'Cell Proliferation'
            elif(this_parameters[0].lower() == 'beta cell function'):
                this_parameters[0] = 'Insulin Secretion'
            else:
                this_parameters[0] = 'Beta Cell Identity'
        if(result[i]['type'] == 'deathPathwaysPlot'):
            tmp = True
            if(len(this_parameters) == 0):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: no parameters provided.'})
                continue
            if(this_parameters[0].lower() not in death_pathways):
                messages.append({'type': 'error', 'content': f'Ilvalid cell death pathway name {this_parameters[0]}.'})
                continue
            this_parameters[0] = death_pathways[this_parameters[0].lower()]
        if(result[i]['type'] == 'specificPathwaysPlot'):
            tmp = True
            if(len(this_parameters) == 0):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: no parameters provided.'})
                continue
            if(this_parameters[0].lower() not in specific_pathways):
                messages.append({'type': 'error', 'content': f'Ilvalid specific pathway name {this_parameters[0]}.'})
                continue
            this_parameters[0] = specific_pathways[this_parameters[0].lower()]
        if(result[i]['type'] == 'customGSEA'):
            tmp = True
            if(len(this_parameters) == 0):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: no parameters provided.'})
                continue
            if( len(this_parameters[0]) < 2):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: at least 2 genes are required in customGSEA.'})
                continue
            for j in range(len(this_parameters[0])):
                g = this_parameters[0][j]
                if(g.lower() not in genes):
                    this_type = 'error'
                    messages.append({'type': 'error', 'content': f'Ilvalid gene name {g}.'})
                    break
                this_parameters[0][j] = genes[g.lower()]
            if(this_type == 'error'):
                continue
        if(result[i]['type'] == 'degAnalysis'):
            tmp = True
            if(len(this_parameters) <= 2):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: number of parameters incorrect, degAnalysis requires 3 parameters.'})
                continue
            if(this_parameters[0].lower() not in hormones):
                messages.append({'type': 'error', 'content': f'Ilvalid hormone name {this_parameters[0]}.'})
                continue
            this_parameters[0] = hormones[this_parameters[0].lower()]
            if(type(this_parameters[1]) not in [type(0.1), type(0)]):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: p-value is not a number.'})
                continue
            if(type(this_parameters[2]) not in [type(0.1), type(0)]):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: fold change is not a number.'})
                continue
        if(result[i]['type'] == 'correlationAnalysis'):
            tmp = True
            if(len(this_parameters) == 0):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: no parameters provided.'})
                continue
            if(len(this_parameters[0]) < 2):
                messages.append({'type': 'error', 'content': 'Error in GPT\'s function calling: at least 2 genes are required in correlationAnalysis.'})
                continue
            for j in range(len(this_parameters[0])):
                g = this_parameters[0][j]
                if(g.lower() not in genes):
                    this_type = 'error'
                    messages.append({'type': 'error', 'content': f'Ilvalid gene name {g}.'})
                    break
                this_parameters[0][j] = genes[g.lower()]
            if(this_type == 'error'):
                continue
        assert(tmp), "Internal error, haven't gone into parameters checking" # only to check typo in function name
        file_name = f'tmp-{randint(100000000000, 999999999999)}.pdf'
        if(function_name == 'dotPlotMulti'):
            this_parameters[0] = ','.join(this_parameters[0])
            # print(this_parameters[0])
        # if(function_name == 'customGSEA'):
        #     this_parameters[0] = ','.join(this_parameters[0])
        r_result = None
        if(function_name in ['violinPlotsingle', 'dotPlotMulti', 'betaPathwaysPlot', 'deathPathwaysPlot', 'specificPathwaysPlot']):
            r_result = this_function(this_parameters[0], './tmp/'+file_name)
        if(function_name == 'customGSEA'):
            r_result = this_function(this_parameters[0], './tmp/'+file_name+'.csv', './tmp/'+file_name)
        if(function_name == 'degAnalysis'):
            r_result = this_function(this_parameters[0], HORMONES_TO_CONTROL[this_parameters[0]], this_parameters[1], this_parameters[2], './tmp/'+file_name+'.csv', './tmp/'+file_name)
        if(function_name == 'correlationAnalysis'):
            r_result = this_function(this_parameters[0], 0, 0.1, './tmp/'+file_name+'.csv', './tmp/'+file_name)
        assert(r_result != None), "Internal error, R functions not called" # only to check typo in function name
        if(r_result[0] == False):
            messages.append({'type': 'error', 'content': f'Error from R function: {binary_to_str(r_result[1])}'})
            continue
        png_bytes = pdf_to_png_bytes('../tmp/'+file_name)
        png_base64 = binToBase64(png_bytes)
        messages.append({'type': 'image', 'content': png_base64})
    messages.append({'type': 'text', 'content': result[-1]})
    request.send_response(200)
    resp_data = json.dumps({'history': history, 'messages': messages}, ensure_ascii=False)
    resp_data = resp_data.encode('utf-8')
    request.send_header('Content-Length', len(resp_data))
    request.send_header('Connection', 'keep-alive')
    request.send_header('Access-Control-Allow-Origin', '*')
    request.end_headers()
    request.finish_log(200, 'chat', len(resp_data))
    request.wfile.write(resp_data)
    request.wfile.flush()
    return

log_file = None
log_queue = Queue()

try:
    f = open(LOG_PATH, 'r')
except:
    log_file = open(LOG_PATH, 'w')
if (log_file == None):
    f.close()
    log_file = open(LOG_PATH, 'a')
    log_file.write('\n\n')


def write_logs():
    log_file.write(format(time() * 1000, '.3f') + ': Server started\n')
    log_file.flush()
    while True:
        l = log_queue.get()
        current_time = format(time() * 1000, '.3f')
        l = current_time + ': ' + l + '\n'
        log_file.write(l)
        log_file.flush()

start_new_thread(write_logs, ())

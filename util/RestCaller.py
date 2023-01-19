import requests
import json


def callHeidelTimeService(parameters):
    dct = parameters.get("dct")
    text = parameters.get("text")

    data = {"input":text, "dct": dct}

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}


    response = requests.post("http://localhost:5000/annotate", json=data, headers=headers)

    # print(response.content)
    return response.text

def callAllenNlpApi(apiName, string):
    URL = "https://demo.allennlp.org/api/"+apiName+"/predict"
    #URL = "http://localhost:8080/api/"+apiName+"/predict"

    PARAMS = {"Content-Type": "application/json"}
    #PARAMS = {"Content-Type": "text/plain;charset=UTF-8", "Host": "localhost:8080"}
    payload = {"sentence":string}

    #payload = {"document":string}
    
    r = requests.post(URL, headers=PARAMS, data=json.dumps(payload))

    #r = requests.post(URL, headers=PARAMS, data=payload)

    #return print(r.text)

    return json.loads(r.text)

ss = """

The biggest U.S. stock market index, the Dow Jones, plunged by more than 416 points by the closing bell on Tuesday, the worst single-day decline since the re-opening of the markets following the September 11th terrorist attacks.
"""
res_srl = callAllenNlpApi("semantic-role-labeling", ss)
#res_srl = callAllenNlpApi("coreference-resolution", ss)


print(res_srl)

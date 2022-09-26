import requests
import json


def callAllenNlpCoref(apiName, string):
    URL = "https://demo.allennlp.org/api/"+apiName+"/predict"
    #URL = "http://localhost:8080/api/"+apiName+"/predict"
    #URL = "http://localhost:8000/api/predict"

    PARAMS = {"Content-Type": "application/json"}
    #PARAMS = {"Content-Type": "text/plain;charset=UTF-8", "Host": "localhost:8080"}
    #payload = {"sentence":string}

    payload = {"document":string}
    
    r = requests.post(URL, headers=PARAMS, data=json.dumps(payload))

    #r = requests.post(URL, headers=PARAMS, data=payload)

    #return print(r.text)

    return json.loads(r.text)

ss = "john bought a new 4-wheel car. He drives the car very fast."
#res_srl = callAllenNlpApi("semantic-role-labeling", ss)
res_srl = callAllenNlpCoref("coreference-resolution", ss)

print(res_srl)

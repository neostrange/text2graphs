import requests
import json


def callAllenNlpApi(apiName, string):
    URL = "https://demo.allennlp.org/api/"+apiName+"/predict"

    PARAMS = {"Content-Type": "application/json"}

    payload = {"sentence":string}
    
    r = requests.post(URL, headers=PARAMS, data=json.dumps(payload))

    print(r.text)

    return json.loads(r.text)

#ss = "Explore the different contribution of words and images to meaning in stories and informative texts."
#res_srl = callAllenNlpApi("semantic-role-labeling", ss)

#print(res_srl)

import requests
import json

def amuse_wsd_api_call2(api_endpoint, sentence):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {"text": sentence, "lang": "EN"}
    data_json = "[" + ",".join([f'{{"text": "{item["text"]}", "lang": "{item["lang"]}"}}' for item in data]) + "]"

    try:
        response = requests.post(api_endpoint, data=data_json, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error while calling AMuSE-WSD API: {e}")
        return None
    
def amuse_wsd_api_call(api_endpoint, sentences):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    data = [{"text": sentence, "lang": "EN"} for sentence in sentences]

    try:
        response = requests.post(api_endpoint, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error while calling AMuSE-WSD API: {e}")
        return None
    
def callHeidelTimeService(parameters):
    dct = parameters.get("dct")
    text = parameters.get("text")

    data = {"input":text, "dct": dct}

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}


    response = requests.post("http://localhost:5000/annotate", json=data, headers=headers)

    # print(response.content)
    return response.text

def callAllenNlpApi(apiName, string):
    #URL = "https://35.247.6.38/api/"+apiName+"/predict"
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

	LemonDuck's activities were first spotted in China in May 2019, before it began adopting COVID_19_themed lures in email attacks in 2020 and even the recently addressed ""ProxyLogon"" Exchange Server flaws to gain access to unpatched systems.
"""
res_srl = callAllenNlpApi("semantic-role-labeling", ss)
#res_srl = callAllenNlpApi("coreference-resolution", ss)


print(res_srl)

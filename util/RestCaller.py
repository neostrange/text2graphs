import requests
import re
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
    
# this method has been implemented just for preprocessing input for AMUSE-WSD 
# it will replace the hyphens being used as infixes with underscores
# it appears that AMUSE-WSD consider underscores for multi-words expressions
        
def replace_hyphens_to_underscores(sentence):
    # Define a regular expression pattern to match hyphens used as infixes
    pattern = re.compile(r'(?<=\w)-(?=\w)')

    # Replace hyphens with underscores
    replaced_sentence = re.sub(pattern, '_', sentence)

    return replaced_sentence


def amuse_wsd_api_call(api_endpoint, sentences):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    # Apply replace_hyphens to each sentence in the collection
    # NOTE: its just a workaround for AMUSE-WSD as it does not consider hyphens for multiwords expressions
    updated_sentences = [replace_hyphens_to_underscores(sentence) for sentence in sentences]
    
    data = [{"text": sentence, "lang": "EN"} for sentence in updated_sentences]

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
    #URL = "https://demo.allennlp.org/api/"+apiName+"/predict"
    URL = "http://localhost:8000/predict"
    #URL = "http://10.1.50.92:8000/predict"
    #URL = "http://localhost:8080/api/"+apiName+"/predict"

    PARAMS = {"Content-Type": "application/json"}
    #PARAMS = {"Content-Type": "text/plain;charset=UTF-8", "Host": "localhost:8080"}
    


    payload = ""
    if apiName == 'semantic-role-labeling':

        # for testing Allennlp for Semantic Role Labeling
        payload = {"sentence":string}
    else:
        # for testing Allennlp for coreferencing
        payload = {"document":string}
    
    r = requests.post(URL, headers=PARAMS, data=json.dumps(payload))

    #r = requests.post(URL, headers=PARAMS, data=payload)

    #return print(r.text)

    return json.loads(r.text)

#ss = """LemonDuck's activities were first spotted in China in May 2019, before it began adopting COVID_19_themed lures in email attacks in 2020 and even the recently addressed ""ProxyLogon"" Exchange Server flaws to gain access to unpatched systems.""""
#ss = """Deutsche Bank of Germany lost almost $3.5 billion in share value, forcing the government to organize a bail_out."""
#ss = """The Federal Reserve met this week, but decided to maintain its target rate of 5.25%, although on Friday the federal funds rate was hovering around 6%, indicating a drop in liquidity."""
ss= """Now, lenders are in a quagmire from millions of people who are unable to repay loans after taking adjustable rate mortgages, teaser rates, interest-only mortgages, or piggyback rates."""
res_srl = callAllenNlpApi("semantic-role-labeling", ss)
#res_srl = callAllenNlpApi("coreference-resolution", ss)


print(res_srl)

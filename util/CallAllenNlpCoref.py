import requests
import json


def callAllenNlpCoref(apiName, string):
    #URL = "https://demo.allennlp.org/api/"+apiName+"/predict"
    #URL = "http://localhost:8080/api/"+apiName+"/predict"
    #URL = "http://localhost:8000/predict"

    # to integrate spacy-experimental-coref
    URL = "http://localhost:9999/coreference_resolution"

    PARAMS = {"Content-Type": "application/json"}
    #PARAMS = {"Content-Type": "text/plain;charset=UTF-8", "Host": "localhost:8080"}
    #payload = {"sentence":string}

    payload = ''

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

ss = """The Bank of America Corporation, the second-largest bank in the United States, has announced that it lost US$2.24 billion in the third quarter of this year, mainly due to increases in loan losses.

According to the bank, the losses are equal to 26 cents per share, worse than most economic analysts had forecast. In the same period a year earlier, Bank of America had gained $704 million, or fifteen cents per share.

The bank's CEO, Ken Lewis, said in a statement that "[...] credit costs remain high, and that is our major financial challenge going forward. However, we are heartened by early positive signs, such as the leveling of delinquencies among our credit card numbers."

Lewis said that losses from loans would probably continue to increase. In a conference call with analysts, he said that "based on [the] economic scenario, results in the fourth quarter are expected to continue to be challenging as we close the year."
"""
#res_srl = callAllenNlpApi("semantic-role-labeling", ss)

text2 = """Global stock markets fell today, in a mass sell-off stemming from the sub-prime mortgage crisis in the United States. The Dow Jones Industrial Average rebounded late in the day after falling more than 250 points, ending the day down about 31 points. The UK's FTSE-100 index fell 232.90 points to 6038.30, and Japan's Nikkei 225 fell 406.51 points to 16764.09. """
res_srl = callAllenNlpCoref("semantic-role-labeling", text2)

print(res_srl)

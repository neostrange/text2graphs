import json
from tokenize import String
import requests
#from allennlp.predictors.predictor import Predictor
#from allennlp_models import pretrained
#import allennlp_models.tagging
from spacy import Language
import GPUtil
import spacy
from spacy.matcher import Matcher, DependencyMatcher
from spacy.tokens import Doc, Token, Span
from spacy.language import Language
import textwrap
from transformers import logging
import re

#from gpml.util.RestCaller import callAllenNlpApi

logging.set_verbosity_error()

from py2neo import Graph
from py2neo import *

#graph = Graph("bolt://10.1.48.224:7687", auth=("neo4j", "neo123"))

#try:
#    dd.set_extension("SRL", default=dict())
#except:
#    pass

try:
    Token.set_extension("SRL", default=dict())
except:
    pass

#this is specific to spacy v3 
#configuring and importing spacy custom plugin for srl
if spacy.Language.has_factory("srl") is False:
    @spacy.Language.factory("srl", 
                    assigns=["token._.SRL"],
                    requires=["token.tag"],
                    retokenizes = False)
    def srl(nlp, name):
        return SemanticRoleLabel()

class SemanticRoleLabel:

    list_exceptions = []

    def __init__(self, ):
        self.apiName = "semantic-role-labeling"


    # this method is just to accomodate long text documents. the reason is allennlp couldn't deal with such long docs
    # the idea here is to partition the docs into half. each partition contains half number of sentences.
    # The result produced by allennlp is retrieved for both of the partitions and integrated by adding paddings of 'O's 



    def get_sent_wise_res_srl(self, doc):

        res_srl_list = list()
        sentences = list()

        for s in doc.sents:
            sentences.append(s.text)

    
        # Apply replace_hyphens to each sentence in the collection
        # NOTE: its just a workaround for AMUSE-WSD as it does not consider hyphens for multiwords expressions
        updated_sentences = [self.replace_hyphens_to_underscores(sentence) for sentence in sentences]

        for sent in updated_sentences:
            res_srl_sent = self.callAllenNlpApi("semantic-role-labeling", sent)
            res_srl_list.append(res_srl_sent)

        return res_srl_list



    def replace_hyphens_to_underscores(self, sentence):
        # Define a regular expression pattern to match hyphens used as infixes
        pattern = re.compile(r'(?<=\w)-(?=\w)')

        # Replace hyphens with underscores
        replaced_sentence = re.sub(pattern, '_', sentence)

        return replaced_sentence



    
    def __call__(self, doc):
        res_srl_list = self.get_sent_wise_res_srl(doc)

        senti = -1
        for sent in doc.sents:
            senti += 1
            temp = sent.text
            res_srl = res_srl_list[senti]
            for tok in sent:
                if tok.pos_ in ["VERB", "AUX"]:
                    ii = tok.i
                    try:
                        if senti == 0:
                            sent_delta = 0
                        else:
                            sent_delta = sent.start

                        srl_tags = self.extract_srl(res_srl["verbs"], ii - sent_delta, sent.start)
                        if srl_tags:
                            tok._.SRL = srl_tags
                    except Exception as e:
                        self.list_exceptions.append("EXCEPTION:" + doc.text + "|||" + tok.text)
        return doc

    def extract_srl(self, verbs, index, sent_start):
        srl_tags = {}
        for verb in verbs:
            if verb["tags"][index] == "B-V":
                frame_verb = verb
                tags = frame_verb["tags"]
                dict_args = {}
                current_role = None

                for jj in range(len(tags)):
                    if current_role is None:
                        if tags[jj] == "O":
                            pass
                        else:
                            if tags[jj][0] == "B":
                                key = tags[jj][tags[jj].find("-") + 1:]
                                current_role = {"role": key, "indices": [jj + sent_start]}
                            else:
                                raise Exception("Cannot be {} after O".format(tags[jj]))
                    else:
                        if tags[jj] == "O":
                            if current_role["role"] not in dict_args:
                                dict_args[current_role["role"]] = []
                            dict_args[current_role["role"]].append(current_role["indices"])
                            current_role = None
                        elif tags[jj][0] == "I":
                            current_role["indices"].append(jj + sent_start)
                        elif tags[jj][0] == "B":
                            if current_role["role"] not in dict_args:
                                dict_args[current_role["role"]] = []
                            dict_args[current_role["role"]].append(current_role["indices"])
                            key = tags[jj][tags[jj].find("-") + 1:]
                            current_role = {"role": key, "indices": [jj + sent_start]}

                if current_role:
                    if current_role["role"] not in dict_args:
                        dict_args[current_role["role"]] = []
                    dict_args[current_role["role"]].append(current_role["indices"])

                for key, value in dict_args.items():
                    if key in srl_tags:
                        srl_tags[key].extend(value)
                    else:
                        srl_tags[key] = value

        return srl_tags


    # Existing code ...



    def srl_doc(self, ss):
        res_srl = self.callAllenNlpApi(self.apiName, ss)
        #res_srl.replace('"',"'")
        #res_srl= json.loads(res_srl)
        return res_srl

    def post_process_verbframe(self,frame_verb):
        tags = frame_verb["tags"]
        dict_args = {}
        current_role = None

        for jj in range(len(tags)):
            if current_role is None:
                if tags[jj] == "O":
                    pass
                else:
                    #begin a tag here
                    if tags[jj][0] == "B":
                        #may have one or multiple dashes (B-ARG1, B-ARGM-DIR) 
                        key = tags[jj][ tags[jj].find("-")+1:]
                        current_role = {key: [jj]}
                    else:
                        raise Exception("cannot be {} after O".format(tags[jj])) 
            else:
                if tags[jj] == "O":
                    #a role is ended
                    dict_args.update(current_role)
                    current_role = None
                elif tags[jj][0] == "I":
                    #continue the current role
                    current_role[list(current_role.keys())[0]].append(jj)
                elif tags[jj][0] == "B":
                    #a new tag follows immediately the previous tag (without any O in-between)
                    dict_args.update(current_role)
                    key = tags[jj][ tags[jj].find("-")+1:]
                    current_role = {key: [jj]}

        return dict_args

    def callAllenNlpApi(self, apiName, string):

        #URL = "http://localhost:8080/api/"+apiName+"/predict"
        URL = "http://localhost:8000/predict"
        
        payload = ""
        
        if apiName == 'semantic-role-labeling':

            # for testing Allennlp for Semantic Role Labeling
            payload = {"sentence":string}
        else:
            # for testing Allennlp for coreferencing
            payload = {"document":string}
        
        

        PARAMS = {"Content-Type": "application/json"}

        #payload = {"sentence":string}
        
        r = requests.post(URL, headers=PARAMS, data=json.dumps(payload))

        print(r.text)

        return json.loads(r.text)
# end of class: SemanticRoleLabel

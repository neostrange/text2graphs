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
    
    def get_customized_res_srl(self, doc):

        text_segment1 = ""
        text_segment2 = ""

        num_sent = len(list(doc.sents))

        partition = num_sent/2

        
        i = 0

        for sent in doc.sents:
            if (i<partition):
                text_segment1 = text_segment1 + sent.text
                i+=1
            else: 
                text_segment2 = text_segment2 + sent.text
                i+=1


        if (text_segment2 == ""):
            return self.srl_doc(doc)
            
        
        res_srl_sent1 = self.callAllenNlpApi("semantic-role-labeling", text_segment1)
        res_srl_sent2 = self.callAllenNlpApi("semantic-role-labeling", text_segment2)

        length_sent1 = len(list(res_srl_sent1["verbs"][0]["tags"]))
        length_sent2 = len(list(res_srl_sent2["verbs"][0]["tags"]))

        i1 = 0
        i2 = 0

        for dict in res_srl_sent1["verbs"]:
            for jj in range(length_sent2):
                #list(dict["tags"]).append("O")
                res_srl_sent1["verbs"][i1]["tags"].append("O")
            i1+=1

        for dict in res_srl_sent2["verbs"]:
            for jj in range(length_sent1):
                #list(dict["tags"]).append("O")
                res_srl_sent2["verbs"][i2]["tags"].insert(0,"O")
            #res_srl_sent2["verbs"][i2]["tags"].reverse()    
            i2+=1



        print("sent1", res_srl_sent1)
        print("sent2", res_srl_sent2)

        joint_res_srl_verbs_list = res_srl_sent1["verbs"] + res_srl_sent2["verbs"]


        print (joint_res_srl_verbs_list)

        dict_of_list = {"verbs": joint_res_srl_verbs_list}

        print(dict_of_list)

        return dict_of_list


    def get_sent_wise_res_srl(self, doc):

        res_srl_list = list()

        for sent in doc.sents:
            res_srl_sent = self.callAllenNlpApi("semantic-role-labeling", sent.text)
            res_srl_list.append(res_srl_sent)

        return res_srl_list

    def __call__(self, doc):
        #res_srl = self.srl_doc(ss = doc.text)
        res_srl_list = self.get_sent_wise_res_srl(doc)

        senti = -1
        # for each token in doc
        for sent in doc.sents:
            senti+=1
            res_srl = res_srl_list[senti]
            for tok in sent:
                if tok.pos_ in ["VERB", "AUX"]:
                    ii = tok.i  # index of token within the parent document
                    try:
                        #search for the frame that is centered on this verb
                        if senti > 0:
                            next_sent_start_i = sent.start
                        else:
                            next_sent_start_i = 0


                        for el in res_srl["verbs"]:
                            if el["tags"][ii - next_sent_start_i] == "B-V":
                                frame_verb = el

                        #frame_verb = [el for el in res_srl.get["verbs"] if el["tags"][ii] == "B-V"][0]
                        dict_args = self.post_process_verbframe(frame_verb) 

                        # add sent.start to each value of index
                        # updated list dict_el_list
                        # the idea here is to add the sentence start index to each index of arg value so that it can corresponds to a doc 
                        # rather than a sentence. 
                        dict_el_list = list()
                        updated_dict = {}

                        for arg in dict_args:
                            
                            dict_el_list.clear()
                            
                            for el_val in dict_args[arg]:
                                updated_val = el_val + sent.start
                                dict_el_list.append(updated_val)
                            
                            value_list = dict_el_list
                            updated_dict[arg] = value_list.copy()


                        #skip cases of {'V': [8]}  
                        if len(list(dict_args.keys())) > 1:
                            #tok._.SRL = dict_args
                            tok._.SRL = updated_dict
                    except Exception as e:
                        self.list_exceptions.append("EXCEPTION:" + doc.text + "|||" + tok.text)
        return doc

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
        URL = "https://demo.allennlp.org/api/"+apiName+"/predict"

        PARAMS = {"Content-Type": "application/json"}

        payload = {"sentence":string}
        
        r = requests.post(URL, headers=PARAMS, data=json.dumps(payload))

        print(r.text)

        return json.loads(r.text)
# end of class: SemanticRoleLabel

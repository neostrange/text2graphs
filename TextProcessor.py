from cgitb import text
import requests
from distutils.command.config import config
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import json
from tokenize import String
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
from util.RestCaller import callAllenNlpApi
from util.RestCaller import amuse_wsd_api_call
from transformers import logging
logging.set_verbosity_error()
from py2neo import Graph
from py2neo import *
import configparser
import os
from util.RestCaller import callAllenNlpApi
from util.CallAllenNlpCoref import callAllenNlpCoref
import traceback
from nltk.corpus import wordnet31 as wn
from nltk.corpus.reader.wordnet import WordNetError as wn_error



from functools import reduce  # Import reduce function






class TextProcessor(object):

    uri=""
    username =""
    password =""
    graph=""
    
    
    
    def __init__(self, nlp, driver):
        self.nlp = nlp
        self._driver = driver
        self.uri=""
        self.username =""
        self.password =""
        config = configparser.ConfigParser()
        #config_file = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
        config.read(config_file)
        py2neo_params = config['py2neo']
        self.uri = py2neo_params.get('uri')
        self.username = py2neo_params.get('username')
        self.password = py2neo_params.get('password')
        #self.graph = Graph(self.uri, auth=(self.username, self.password))


    def do_coref2(self, doc, textId):
        graph = Graph(self.uri, auth=(self.username, self.password))
        result = callAllenNlpCoref("coreference-resolution", doc.text )


        print("Coref Result: ", result)
        sg=""
        PARTICIPANT = Relationship.type("PARTICIPANT")
        PARTICIPATES_IN = Relationship.type("PARTICIPATES_IN")
        MENTIONS = Relationship.type("MENTIONS")
        COREF = Relationship.type("COREF")

        #print("clusters: " , result["clusters"])
        # storing the coreference mentions as graph nodes linked with antecedent via mentions edges
                # steps
                # 1. get the coref-mention and antedent pair
        coref = []
        for cluster in result["clusters"]:
            i=0
            antecedent_span = ""
            cag="" # coreferents - antecedent relationships sub-graph
            
            for span_token_indexes in cluster:
                if i == 0:
                    i+=1
                    # the first span will be the antecedent for all other references
                    antecedent_span = doc[span_token_indexes[0]:span_token_indexes[-1]] #updated for index
                    antecedent_node = {'start_index': span_token_indexes[0], 'end_index': span_token_indexes[-1], 'text': antecedent_span.text} # updated for -1 index
                    antecendent_node = Node("Antecedent", text= antecedent_span.text, startIndex=span_token_indexes[0], endIndex=span_token_indexes[-1]) # updated for -1 index
                    antecedent_node_start_index = span_token_indexes[0]
                    # connect the antecedentNode node with all the participating tagOccurrences
                    index_range = range(span_token_indexes[0], span_token_indexes[-1])
                    atg=""
                    for index in index_range:
                        query = "match (x:TagOccurrence {tok_index_doc:" + str(index) + "})-[:HAS_TOKEN]-()-[:CONTAINS_SENTENCE]-(:AnnotatedText {id:"+str(doc._.text_id)+"}) return x"
                        token_node = graph.evaluate(query)
                        if token_node is None:
                            #sga= antecendent_node
                            #graph.create(sga)
                            continue
                        token_mention_rel = PARTICIPATES_IN(token_node,antecendent_node)
                        if atg == "":
                            atg = token_mention_rel
                        else:
                            atg = atg | token_mention_rel
                    graph.create(atg)
                    # antecedent-tagOccurrences sub-graph creation end. 
                    continue

                coref_mention_span = doc[span_token_indexes[0]:span_token_indexes[-1]] #updated index
                coref_mention_node = {'start_index': span_token_indexes[0], 'end_index': span_token_indexes[-1], 'text': coref_mention_span.text} #updated index
                corefMention_node = Node("CorefMention", text= coref_mention_span.text, startIndex=span_token_indexes[0], endIndex=span_token_indexes[-1]) #updated index
                #mention = {'from_index': span[-1], 'to_index': antecedent}
                #mention = { 'referent': coref_mention_span, 'antecedent': antecedent_span}
                mention = { 'referent': coref_mention_node, 'antecedent': antecedent_node}
                
                # connect the corefMention node with all the participating tagOccurrences
                index_range = range(span_token_indexes[0], span_token_indexes[-1]) #updated index
                ctg=""
                for index in index_range:
                    query = "match (x:TagOccurrence {tok_index_doc:" + str(index) + "})-[:HAS_TOKEN]-()-[:CONTAINS_SENTENCE]-(:AnnotatedText {id:"+str(doc._.text_id)+"}) return x"
                    token_node = graph.evaluate(query)
                    if token_node is None:
                        #sgc= corefMention_node
                        #graph.create(sgc)
                        continue
                    token_mention_rel = PARTICIPATES_IN(token_node,corefMention_node)
                    if ctg == "":
                        ctg = token_mention_rel
                    else:
                        ctg = ctg | token_mention_rel
                    graph.create(ctg)
                # corefMention - TagOccurrence subgraph ends. 


                coref_rel = COREF(corefMention_node,antecendent_node)
                if cag == "":
                    cag = coref_rel
                else:
                    cag = cag | coref_rel
                
                coref.append(mention)

                # connect the corefMention node with the antecdent namedEntity. 
                # np_query = "MATCH (document:AnnotatedText {id:"+ str(doc._.text_id) +"})-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NamedEntity) WHERE np.index = " + str(antecedent_node_start_index) + " RETURN end"
                # np_node = graph.evaluate(np_query)
                # if np_node is None:
                #     """ try:
                #         #graph.create(sg)
                #     except BaseException as err:
                #         print(f"Unexpected {err=}, {type(err)=}") """
                    
                #     continue
                
                # coref_mention_np_rel = MENTIONS(corefMention_node,np_node)
                
                # cag = cag |coref_mention_np_rel  

            graph.create(cag)
        
           
        #TODO: this query need to be tested and should be made more specific other wise it may result it false positives
        # graph.evaluate("""match (ne:NamedEntity)<-[:PARTICIPATES_IN]-(tago:TagOccurrence)-[:PARTICIPATES_IN]->(ant:Antecedent)<-[:COREF]-(corefm:CorefMention) 
        # where tago.index = ne.index and tago.tok_index_doc = ant.startIndex
        # merge (corefm)-[:MENTIONS]->(ne)""")    
        
        print(coref)
        #self.store_coref_mentions(doc, coref)

        

        # create the referrant span , attaches it with the tagOccurrences
        # identify the namedEntity that belongs to the antecedent
        # 

        



    def do_coref(self, doc, textId):
        
        result = callAllenNlpCoref("coreference-resolution", doc.text )

        #print("clusters: " , result["clusters"])
        # storing the coreference mentions as graph nodes linked with antecedent via mentions edges
                # steps
                # 1. get the coref-mention and antedent pair
        coref = []
        for cluster in result["clusters"]:
            i=0
            antecedent_span = ""
            for span_token_indexes in cluster:
                if i == 0:
                    i+=1
                    # the first span will be the antecedent for all other references
                    antecedent_span = doc[span_token_indexes[0]:span_token_indexes[-1]+1]
                    antecedent_node = {'start_index': span_token_indexes[0], 'end_index': span_token_indexes[-1]+1, 'text': antecedent_span.text}
                    continue
                coref_mention_span = doc[span_token_indexes[0]:span_token_indexes[-1]+1]
                coref_mention_node = {'start_index': span_token_indexes[0], 'end_index': span_token_indexes[-1]+1, 'text': coref_mention_span.text}
                #mention = {'from_index': span[-1], 'to_index': antecedent}
                #mention = { 'referent': coref_mention_span, 'antecedent': antecedent_span}
                mention = { 'referent': coref_mention_node, 'antecedent': antecedent_node}
                coref.append(mention)
            
        print(coref)
        self.store_coref_mentions(doc, coref)

    def store_coref_mentions(self, doc, mentions):
        graph = Graph(self.uri, auth=(self.username, self.password))

        # create the referrant span , attaches it with the tagOccurrences
        # identify the namedEntity that belongs to the antecedent
        # 

        sg=""
        PARTICIPANT = Relationship.type("PARTICIPANT")
        PARTICIPATES_IN = Relationship.type("PARTICIPATES_IN")
        MENTIONS = Relationship.type("MENTIONS")
        COREF = Relationship.type("COREF")

        for mention in mentions:
            
            
            start_index = mention['referent']['start_index']
            end_index = mention['referent']['end_index']
            start_index_antecedent = mention['antecedent']['start_index']
            end_index_antecedent = mention['antecedent']['end_index']

            sg=""
            sgc=""
            sga=""
            # create a corefMention node
            corefMention_node = Node("CorefMention", text= mention['referent']['text'], startIndex=start_index, endIndex=end_index)
            antecendent_node = Node("Antecedent", text= mention['antecedent']['text'], startIndex=start_index_antecedent, endIndex=end_index_antecedent)

            coref_rel = COREF(corefMention_node,antecendent_node)
            #tx = self.graph.begin()
            graph.create(coref_rel)
            
            #self.graph.commit(tx)
            # connect the corefMention node with all the participating tagOccurrences
            index_range = range(start_index, end_index)
            for index in index_range:
                query = "match (x:TagOccurrence {tok_index_doc:" + str(index) + "})-[:HAS_TOKEN]-()-[:CONTAINS_SENTENCE]-(:AnnotatedText {id:"+str(doc._.text_id)+"}) return x"
                token_node = graph.evaluate(query)
                if token_node is None:
                    sgc= corefMention_node
                    #graph.create(sgc)
                    continue
                token_mention_rel = PARTICIPATES_IN(token_node,corefMention_node)
                if sgc == "":
                    sgc = token_mention_rel
                else:
                    sgc = sgc | token_mention_rel
                graph.create(sgc)

            # connect the antecedentNode node with all the participating tagOccurrences
            index_range = range(start_index_antecedent, end_index_antecedent)
            for index in index_range:
                query = "match (x:TagOccurrence {tok_index_doc:" + str(index) + "})-[:HAS_TOKEN]-()-[:CONTAINS_SENTENCE]-(:AnnotatedText {id:"+str(doc._.text_id)+"}) return x"
                token_node = graph.evaluate(query)
                if token_node is None:
                    sga= antecendent_node
                    #graph.create(sga)
                    continue
                token_mention_rel = PARTICIPATES_IN(token_node,antecendent_node)
                if sga == "":
                    sga = token_mention_rel
                else:
                    sga = sga | token_mention_rel
                graph.create(sga)
            
            
            #graph.create(sg|sga|coref_rel)
            
            # connect the corefMention node with the antecdent namedEntity. 
            np_query = "MATCH (document:AnnotatedText {id:"+ str(doc._.text_id) +"})-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NamedEntity) WHERE np.index = " + str(start_index_antecedent) + " RETURN end"
            np_node = graph.evaluate(np_query)
            if np_node is None:
                """ try:
                    #graph.create(sg)
                except BaseException as err:
                    print(f"Unexpected {err=}, {type(err)=}") """
                
                continue
            
            coref_mention_np_rel = MENTIONS(corefMention_node,np_node)
            
            sg = sg |coref_mention_np_rel 

            try:
                graph.create(sg)
            except BaseException as err:
               print(f"Unexpected {err=}, {type(err)=}") 

        return mention    

        
# this method also includes code to create files for TARSQI toolkit.
# TODO: we need to port this code to another seperate script file outside this project. 
    def get_annotated_text(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = "MATCH (n:AnnotatedText) RETURN n.text, n.id, n.creationtime"
        data= graph.run(query).data()

        annotatedd_text_docs= list()

        for record in data:
            #print(record)
            #print(record.get("n.text"))
            t = (record.get("n.text"), {'text_id': record.get("n.id")})

            dct = str(record.get("n.creationtime"))
            dct = dct[0:10]
            dct= dct.replace('-','')
            # create a file
            filename = """/home/neo/environments/text2graphs/text2graphs/tarsqi-dataset/""" + str(record.get("n.id")) +"_"+ dct + ".xml" 
            if not os.path.exists(filename):
                f = open(filename, "x")
                f.write(record.get("n.text"))
                f.close()
            annotatedd_text_docs.append(t)
        
        return annotatedd_text_docs

   
    

    
    def apply_pipeline_1(self, doc, flag_display=False):
        graph = Graph(self.uri, auth=(self.username, self.password))
        frameDict = {}

        v = None
        sg = None
        tv = None

        PARTICIPANT = Relationship.type("PARTICIPANT")
        PARTICIPATES_IN = Relationship.type("PARTICIPATES_IN")

        for tok in doc:
            sg = None
            v = None
            frameDict = {}

            for x, indices_list in tok._.SRL.items():
                for y in indices_list:
                    span = doc[y[0]: y[len(y) - 1] + 1]

                    if x == "V":
                        v = Node("Frame", text=span.text, startIndex=y[0], endIndex=y[len(y) - 1])
                        for index in y:
                            query = "MATCH (x:TagOccurrence {tok_index_doc:" + str(
                                index) + "})-[:HAS_TOKEN]-()-[:CONTAINS_SENTENCE]-(:AnnotatedText {id:" + str(
                                doc._.text_id) + "}) RETURN x"
                            token_node = graph.evaluate(query)
                            token_verb_rel = PARTICIPATES_IN(token_node, v)
                            graph.create(token_verb_rel)

                        tv = v
                    else:
                        a = Node("FrameArgument", type=x, text=span.text, startIndex=y[0], endIndex=y[len(y) - 1])

                        if a is None:
                            continue

                        for index in y:
                            query = "MATCH (x:TagOccurrence {tok_index_doc:" + str(
                                index) + "})-[:HAS_TOKEN]-()-[:CONTAINS_SENTENCE]-(:AnnotatedText {id:" + str(
                                doc._.text_id) + "}) RETURN x"
                            token_node = graph.evaluate(query)

                            if token_node is None:
                                continue

                            # Create PARTICIPATES_IN relationship between TagOccurrence and FrameArgument
                            token_arg_rel = PARTICIPATES_IN(token_node, a)
                            graph.create(token_arg_rel)

                        if x not in frameDict:
                            frameDict[x] = []
                        frameDict[x].append(a)

            if tv is not None:
                sg = tv

            for i in frameDict:
                if sg is None:
                    break
                for arg_node in frameDict[i]:
                    # Create PARTICIPANT relationship between FrameArgument and Frame
                    r = PARTICIPANT(arg_node, sg)
                    graph.create(r)

            if sg is not None:
                try:
                    graph.create(sg)
                except BaseException as err:
                    print(f"Unexpected {err=}, {type(err)=}")


            #print(x, ": ",y, span.text)
                        

        # print("list pipeline: ", list_pipeline)
        # print("------------------------------------------------")
        # print(tok._.SRL)


    ######################################################################### Token Enrichement with Wordnet ################################################################

    

    # Function to get hypernyms for a synset
    def get_all_hypernyms(self, synset):
        hypernyms = []
        hypernym_synsets = synset.hypernyms()
        for hypernym_synset in hypernym_synsets:
            hypernyms.append(hypernym_synset.name())  # Store hypernym synset name
            hypernyms.extend(self.get_all_hypernyms(hypernym_synset))  # Recursive call to get hypernyms of hypernyms
        return hypernyms

    # Function to get synonyms of a synset
    def get_synonyms(self, synset):
        synonyms = []
        for lemma in synset.lemmas():
            synonyms.append(lemma.name())  # Store synonym
        return synonyms

    # Function to get domain labels for a synset
    """ def get_domain_labels(self, synset):
        domain_labels = []
        topic_domains = synset.topic_domains()
        for domain in topic_domains:
            domain_labels.extend(domain.split("."))
        return domain_labels """
    

    # Function to get domain labels for a synset
    def get_domain_labels(self, synset):
        domain_labels = []
        lexname = synset.lexname()

        # Extract the domain label from the lexical name if present
        if "." in lexname:
            domain_labels.append(lexname.split(".")[0])

        return domain_labels


    # Assuming you have a running Neo4j server and a connected driver instance called 'driver'
    def assign_synset_info_to_tokens(self, doc_id):
        with self._driver.session() as session:
            # Step 1: Retrieve all Sentence nodes for the given AnnotatedText document
            query = """
            MATCH (d:AnnotatedText {id: $doc_id})-[:CONTAINS_SENTENCE]->(s:Sentence)
            RETURN s.id AS sentence_id, s.text AS sentence_text
            """
            params = {"doc_id": doc_id}
            result = self.execute_query3(query, params)

            for record in result:
                sentence_id = record["sentence_id"]
                sentence_text = record["sentence_text"]

                # Step 2: Retrieve the linked Token nodes for each Sentence node
                query = """
                MATCH (s:Sentence {id: $sentence_id})-[:HAS_TOKEN]->(t:TagOccurrence)
                RETURN t.id AS token_id, t.nltkSynset AS nltkSynset, t.wnSynsetOffset AS wnSynsetOffset
                """
                params = {"sentence_id": sentence_id}
                token_result = self.execute_query3(query, params)

                for token_record in token_result:
                    token_id = token_record["token_id"]
                    #wn_synset_offset = token_record["wnSynsetOffset"]
                    nltk_synset = token_record["nltkSynset"]

                    

                    #print(wn_synset_offset)

                    if nltk_synset and nltk_synset != 'O':

                        try:
                            synset = wn.synset(nltk_synset)
                            synset_identifier = synset.name()
                            print(synset_identifier)
                            lemma, pos, sense_num = synset_identifier.split('.')
                            #print("Lemma:", lemma)
                            #print("POS:", pos)
                            #print("Sense Number:", sense_num)

                            wn_synset_offset = synset.offset()
                            wn_synset_offset = str(wn_synset_offset) + pos


                            # Step 3: Get synset information from WordNet
                            synset = wn.synset_from_pos_and_offset(wn_synset_offset[-1], int(wn_synset_offset[:-1]))
                            #synset = wn.synset_from_pos_and_offset(wn_synset_offset[-1], int(wn_synset_offset))

                            # Get hypernyms, synonyms, and domain labels for the synset
                            hypernyms = self.get_all_hypernyms(synset)
                            synonyms = self.get_synonyms(synset)
                            domain_labels = self.get_domain_labels(synset)

                            # Update the Token node in Neo4j with synset-related information
                            update_query = """
                            MATCH (t:TagOccurrence {id: $token_id})
                            SET t.hypernyms = $hypernyms, t.wn31SynsetOffset = $wn31SynsetOffset, t.synonyms = $synonyms, t.domain_labels = $domain_labels
                            """
                            params = {
                                "token_id": token_id,
                                "hypernyms": hypernyms,
                                "synonyms": synonyms,
                                "domain_labels": domain_labels,
                                "wn31SynsetOffset": wn_synset_offset
                            }
                            self.execute_query3(update_query, params)  # Call your existing execute_query method
                        except wn_error:
                            print(f"Synset not found for token_id: {token_id}. Skipping processing.")

                    else:
                        print(f"Synset offset 'O' or empty for token_id: {token_id}. Skipping processing.")










########################################################
   



    #########################################################################################################################################################################

    ######################################################################### Word Sense Disambiguation Code #################################################################
    def amuse_wsd_api_call(self, api_endpoint, sentence):
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        data = [{"text": sentence, "lang": "EN"}]

        try:
            response = requests.post(api_endpoint, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error while calling AMuSE-WSD API: {e}")
            return None
        

    def update_tokens_in_neo4j(self, sentence_id, token_index, token_attrs):
        query = """
            MATCH (s:Sentence {id: $sentence_id})-[:HAS_TOKEN]->(t:TagOccurrence {tok_index_sent: $index})
            SET t.bnSynsetId = $bnSynsetId,
                t.wnSynsetOffset = $wnSynsetOffset,
                t.nltkSynset = $nltkSynset
        """

        params = {
            "sentence_id": sentence_id,
            "index": token_index,
            "bnSynsetId": token_attrs['bnSynsetId'],
            "wnSynsetOffset": token_attrs['wnSynsetOffset'],
            "nltkSynset": token_attrs['nltkSynset']
        }

        self.execute_query(query, params)


    
        
    def perform_wsd(self, document_id):

        amuze_wsd_api_endpoint = "http://localhost:81/api/model"
        
        query = """ MATCH (d:AnnotatedText {id: $doc_id})-[:CONTAINS_SENTENCE]->(s:Sentence) RETURN s.id AS sentence_id, s.text AS text """
        params = {"doc_id": document_id}
        result = self.execute_query3(query, params)


        # amuze_wsd_api_endpoint = "http://localhost:81/api/model"
        
        # query = """MATCH (d:AnnotatedText {id: $doc_id})-[:CONTAINS_SENTENCE]->(s:Sentence) RETURN s.id AS sentence_id, s.text AS text"""
        # params = {"doc_id": document_id}
        # result = self.execute_query(query, params)

        sentences_to_process = []
        sentence_ids = []

        for record in result:
            sentence_id = record["sentence_id"]
            sentence_text = record["text"]

            # Collect sentences to process in batches
            sentences_to_process.append(sentence_text)
            sentence_ids.append(sentence_id)

        # Step 2.1: Call the AMuSE-WSD API with multiple sentences
        api_response = amuse_wsd_api_call(amuze_wsd_api_endpoint, sentences_to_process)

        if api_response:
            for idx, sentence_data in enumerate(api_response):
                sentence_id = sentence_ids[idx]

                # Step 2.2: Update the associated Token nodes in Neo4j with the API response
                for token_data in sentence_data['tokens']:
                    token_index = token_data['index']
                    token_attrs = {
                        'bnSynsetId': token_data['bnSynsetId'],
                        'wnSynsetOffset': token_data['wnSynsetOffset'],
                        'nltkSynset': token_data['nltkSynset']
                    }

                    self.update_tokens_in_neo4j(sentence_id=sentence_id, token_index=token_index, token_attrs=token_attrs)


########################################################## End of Section: Word Sense Disambiguation ################################################################    

 # query = """MERGE (ann:AnnotatedText {id: $id})
       #     RETURN id(ann) as result
        #"""

        
    def create_annotated_text(self, data, content, id):
        #filename = "file://" + filename

        query = """ WITH $data
        AS xmlString 
        WITH apoc.xml.parse(xmlString) AS value
        UNWIND [item in value._children where item._type ="nafHeader"] AS nafHeader
        UNWIND [item in value._children where item._type ="raw"] AS raw
        UNWIND [item in nafHeader._children where item._type = "fileDesc"] AS fileDesc
        UNWIND [item in nafHeader._children where item._type = "public"] AS public
        WITH  fileDesc.author as author, fileDesc.creationtime as creationtime, fileDesc.filename as filename, fileDesc.filetype as filetype, fileDesc.title as title, public.publicId as publicId, public.uri as uri, raw._text as text
        MERGE (at:AnnotatedText {id: $id}) set at.author = author, at.creationtime = creationtime, at.filename = filename, at.filetype = filetype, at.title = title, at.publicId = publicId, at.uri = uri, at.text = $text
        """
        # query = """ CALL apoc.load.xml($filename) 
        # YIELD value
        # UNWIND [item in value._children where item._type ="nafHeader"] AS nafHeader
        # UNWIND [item in value._children where item._type ="raw"] AS raw
        # UNWIND [item in nafHeader._children where item._type = "fileDesc"] AS fileDesc
        # UNWIND [item in nafHeader._children where item._type = "public"] AS public
        # WITH  fileDesc.author as author, fileDesc.creationtime as creationtime, fileDesc.filename as filename, fileDesc.filetype as filetype, fileDesc.title as title, public.publicId as publicId, public.uri as uri, raw._text as text
        # MERGE (at:AnnotatedText {id: $id}) set at.author = author, at.creationtime = creationtime, at.filename = filename, at.filetype = filetype, at.title = title, at.publicId = publicId, at.uri = uri, at.text = $text
        # """
        params = {"id": id, "data":data, "text": content}
        #params = {"id": id, "filename":data}
        print(query)
        results = self.execute_query(query, params)
        #return results[0]
#replace(text,"  "," ")
    def add_temporal_metadata(self, filename, id):
        
        return ""

    def process_sentences(self, annotated_text, doc, storeTag, text_id):
        i = 0
        for sentence in doc.sents:
            sentence_id = self.store_sentence(sentence, annotated_text, text_id, i, storeTag)
            #spans = list(doc.ents) + list(doc.noun_chunks) - just removed so that only entities get stored.
            #spans = list(doc.ents) - just disabled it as testing dbpedia spotlight
            spans = ''
            if doc.spans.get('ents_original') != None:
                spans = list(doc.ents) + list(doc.spans['ents_original'])
            else:
                spans = list(doc.ents)
            #spans = filter_spans(spans) - just disabled it as testing dbpedia spotlight
            i += 1
        return spans

    def store_sentence(self, sentence, annotated_text, text_id, sentence_id, storeTag):
        # sentence_query = """MATCH (ann:AnnotatedText) WHERE id(ann) = $ann_id
        #     MERGE (sentence:Sentence {id: $sentence_unique_id})
        #     SET sentence.text = $text
        #     MERGE (ann)-[:CONTAINS_SENTENCE]->(sentence)
        #     RETURN id(sentence) as result
        # """


        sentence_query = """MATCH (ann:AnnotatedText) WHERE ann.id = $ann_id
            MERGE (sentence:Sentence {id: $sentence_unique_id})
            SET sentence.text = $text
            MERGE (ann)-[:CONTAINS_SENTENCE]->(sentence)
            RETURN id(sentence) as result
        """

        tag_occurrence_query = """MATCH (sentence:Sentence) WHERE id(sentence) = $sentence_id
            WITH sentence, $tag_occurrences as tags
            FOREACH ( idx IN range(0,size(tags)-2) |
            MERGE (tagOccurrence1:TagOccurrence {id: tags[idx].id})
            SET tagOccurrence1 = tags[idx]
            MERGE (sentence)-[:HAS_TOKEN]->(tagOccurrence1)
            MERGE (tagOccurrence2:TagOccurrence {id: tags[idx + 1].id})
            SET tagOccurrence2 = tags[idx + 1]
            MERGE (sentence)-[:HAS_TOKEN]->(tagOccurrence2)
            MERGE (tagOccurrence1)-[r:HAS_NEXT {sentence: sentence.id}]->(tagOccurrence2))
            RETURN id(sentence) as result
        """

        tag_occurrence_with_tag_query = """MATCH (sentence:Sentence) WHERE id(sentence) = $sentence_id
            WITH sentence, $tag_occurrences as tags
            FOREACH ( idx IN range(0,size(tags)-2) |
            MERGE (tagOccurrence1:TagOccurrence {id: tags[idx].id})
            SET tagOccurrence1 = tags[idx]
            MERGE (sentence)-[:HAS_TOKEN]->(tagOccurrence1)
            MERGE (tagOccurrence2:TagOccurrence {id: tags[idx + 1].id})
            SET tagOccurrence2 = tags[idx + 1]
            MERGE (sentence)-[:HAS_TOKEN]->(tagOccurrence2)
            MERGE (tagOccurrence1)-[r:HAS_NEXT {sentence: sentence.id}]->(tagOccurrence2))
            FOREACH (tagItem in [tag_occurrence IN $tag_occurrences WHERE tag_occurrence.is_stop = False] | 
            MERGE (tag:Tag {id: tagItem.lemma}) MERGE (tagOccurrence:TagOccurrence {id: tagItem.id}) MERGE (tag)<-[:REFERS_TO]-(tagOccurrence))
            RETURN id(sentence) as result
        """

        params = {"ann_id": annotated_text, "text": sentence.text,
                  "sentence_unique_id": str(text_id) + "_" + str(sentence_id)}
        results = self.execute_query(sentence_query, params)
        node_sentence_id = results[0]
        tag_occurrences = []
        tag_occurrence_dependencies = []
        for token in sentence:
            lexeme = self.nlp.vocab[token.text]
            # edited: included the punctuation as possible token candidates.
            #if not lexeme.is_punct and not lexeme.is_space:
            if not lexeme.is_space:
                tag_occurrence_id = str(text_id) + "_" + str(sentence_id) + "_" + str(token.idx)
                tag_occurrence = {"id": tag_occurrence_id,
                                    "index": token.idx,
                                    "end_index": (len(token.text)+token.idx),
                                    "text": token.text,
                                    "lemma": token.lemma_,
                                    "pos": token.tag_,
                                    "upos": token.pos_,
                                    "tok_index_doc": token.i,
                                    "tok_index_sent": (token.i - sentence.start),
                                    "is_stop": (lexeme.is_stop or lexeme.is_punct or lexeme.is_space)}
                tag_occurrences.append(tag_occurrence)
                tag_occurrence_dependency_source = str(text_id) + "_" + str(sentence_id) + "_" + str(token.head.idx)

                print(token.text, token.dep_, token.head.text, token.head.pos_,
            [child for child in token.children])
                dependency = {"source": tag_occurrence_dependency_source, "destination": tag_occurrence_id,
                                "type": token.dep_}
                tag_occurrence_dependencies.append(dependency)
        params = {"sentence_id": node_sentence_id, "tag_occurrences": tag_occurrences}
        if storeTag:
            results = self.execute_query(tag_occurrence_with_tag_query, params)
        else:
            results = self.execute_query(tag_occurrence_query, params)

        self.process_dependencies(tag_occurrence_dependencies)
        return results[0]


    # this snippet is for dbpedia-spotlight component
    def process_entities(self, spans, text_id):
        nes = []
        for entity in spans:
            if entity.kb_id_ != '': 
                ne = {'value': entity.text, 'type': entity.label_, 'start_index': entity.start_char,
                    'end_index': entity.end_char, 
                    'kb_id': entity.kb_id_, 'url_wikidata': entity.kb_id_, 'score': entity._.dbpedia_raw_result['@similarityScore'],
                    'normal_term': entity.text, 'description': entity._.dbpedia_raw_result.get('@surfaceForm')
                    }
            else:
                ne = {'value': entity.text, 'type': entity.label_, 'start_index': entity.start_char,
                    'end_index': entity.end_char
                    }

            nes.append(ne)
        self.store_entities(text_id, nes)
        return nes
    #end of this snippet


    # this snippet is only applicable for entity-fishing component
    # def process_entities(self, spans, text_id):
    #     nes = []
    #     for entity in spans:
    #         ne = {'value': entity.text, 'type': entity.label_, 'start_index': entity.start_char,
    #               'end_index': entity.end_char, 
    #               'kb_id': entity._.kb_qid, 'url_wikidata': entity._.url_wikidata, 'score': entity._.nerd_score,
    #               'normal_term': entity._.normal_term, 'description': entity._.description }
    #         nes.append(ne)
    #     self.store_entities(text_id, nes)
    #     return nes
    # end of this snippet. 

    def process_noun_chunks(self, doc, text_id):
        ncs = []
        for noun_chunk in doc.noun_chunks:
            nc = {'value': noun_chunk.text, 'type': noun_chunk.label_, 'start_index': noun_chunk.start_char,
                  'end_index': noun_chunk.end_char}
            ncs.append(nc)
        self.store_noun_chunks(text_id, ncs)
        return ncs

    def store_noun_chunks(self, document_id, ncs):
        nc_query = """
            UNWIND $ncs as item
            MERGE (nc:NounChunk {id: toString($documentId) + "_" + toString(item.start_index)})
            SET nc.type = item.type, nc.value = item.value, nc.index = item.start_index
            WITH nc, item as ncIndex
            MATCH (text:AnnotatedText)-[:CONTAINS_SENTENCE]->(sentence:Sentence)-[:HAS_TOKEN]->(tagOccurrence:TagOccurrence)
            WHERE text.id = $documentId AND tagOccurrence.index >= ncIndex.start_index AND tagOccurrence.index < ncIndex.end_index
            MERGE (nc)<-[:PARTICIPATES_IN]-(tagOccurrence)
        """
        self.execute_query(nc_query, {"documentId": document_id, "ncs": ncs})

    def store_entities(self, document_id, nes):
        ne_query = """
            UNWIND $nes as item
            MERGE (ne:NamedEntity {id: toString($documentId) + "_" + toString(item.start_index)+ "_" + toString(item.end_index)+ "_" + toString(item.type)})
            SET ne.type = item.type, ne.value = item.value, ne.index = item.start_index,
            ne.kb_id = item.kb_id, ne.url_wikidata = item.url_wikidata, ne.score = item.score, ne.normal_term = item.normal_term, 
            ne.description = item.description
            WITH ne, item as neIndex
            MATCH (text:AnnotatedText)-[:CONTAINS_SENTENCE]->(sentence:Sentence)-[:HAS_TOKEN]->(tagOccurrence:TagOccurrence)
            WHERE text.id = $documentId AND tagOccurrence.index >= neIndex.start_index AND tagOccurrence.index < neIndex.end_index
            MERGE (ne)<-[:PARTICIPATES_IN]-(tagOccurrence)
        """
        self.execute_query(ne_query, {"documentId": document_id, "nes": nes})

#ne.kb_id = item.kb_id, ne.description = item.description, ne.score = item.score


        #NamedEntity Multitoken
    def get_and_assign_head_info_to_entity_multitoken(self, document_id):

        # print(self.uri)
        # graph = Graph(self.uri, auth=(self.username, self.password))


        # query to find the head of a NamedEntity. (case is for entitities composed of  multitokens )
        # TODO: the head for the NAM should include the whole extent of the name. see newsreader annotation guidelines 
        # for more information. 
        query = """    
                        MATCH p= (text:AnnotatedText where text.id =  $documentId)-[:CONTAINS_SENTENCE]->(sentence:Sentence)-[:HAS_TOKEN]->(a:TagOccurrence)-[:PARTICIPATES_IN]-(ne:NamedEntity),q= (a)-[:IS_DEPENDENT]->()--(ne)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(ne))
                        WITH ne, a, p
                                                set ne.head = a.text, ne.headTokenIndex = a.tok_index_doc, 
                                                (case when a.pos in ['NNS', 'NN'] then ne END).syntacticType ='NOMINAL' ,
                                                (case when a.pos in ['NNP', 'NNPS'] then ne END).syntacticType ='NAM' 
        
        """
        self.execute_query(query, {'documentId': document_id})
        


    #NamedEntity Singletoken
    def get_and_assign_head_info_to_entity_singletoken(self, document_id):

        # print(self.uri)
        # graph = Graph(self.uri, auth=(self.username, self.password))


        # query to find the head of a NamedEntity. (case is for entitities composed of  single token )
        query = """    
                        MATCH p= (text:AnnotatedText where text.id =  $documentId )-[:CONTAINS_SENTENCE]->(sentence:Sentence)-[:HAS_TOKEN]->(a:TagOccurrence)-[:PARTICIPATES_IN]-(ne:NamedEntity)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(ne)) and not exists ((a)-[:IS_DEPENDENT]->()--(ne))
                        WITH ne, a, p
                                                set ne.head = a.text, ne.headTokenIndex = a.tok_index_doc, 
                                                (case when a.pos in ['NNS', 'NN'] then ne END).syntacticType ='NOMINAL' ,
                                                (case when a.pos in ['NNP', 'NNPS'] then ne END).syntacticType ='NAM'   
        
        """
        self.execute_query(query, {'documentId': document_id})



    def use_spacy_named_entities(self, document_id):
        # this query keep spacy named entities which have type of 'CARDINAL', 'DATE', 'ORDINAL', 'MONEY', 'TIME', 'QUANTITY', 'PERCENT' 
        query1 = """
                    match p = (ne:NamedEntity where ne.type in ['CARDINAL', 'DATE', 'ORDINAL', 'MONEY', 'TIME', 'QUANTITY', 'PERCENT'])--
                    (a:TagOccurrence )--(ne2:NamedEntity) 
                    where a.tok_index_doc = ne.headTokenIndex and a.tok_index_doc = ne2.headTokenIndex and ne.id <> ne2.id
                    detach delete ne2
        """ 
        self.execute_query(query1, {"documentId": document_id})


    
    def use_dbpedia_named_entities(self, document_id):
            # this query keeps the dbpedia ner entity but copies the spacy ner type information. 
        query2 = """
                    match p = (ne:NamedEntity where ne.kb_id is not null)--(a:TagOccurrence )--(ne2:NamedEntity) 
                    where a.tok_index_doc = ne.headTokenIndex and a.tok_index_doc = ne2.headTokenIndex and ne.id <> ne2.id
                    set ne.spacyType = ne2.type
                    detach delete ne2 
        """
        
        
        self.execute_query(query2, {"documentId": document_id})
     

    #In our pipeline, we employed two named entity recognition (NER) components, 
    # namely the spaCy NER and DBpedia-spotlight. By using both components, we were able 
    # to achieve high accuracy and recall. However, we needed to merge the results from 
    # these two components. To do this, we obtained two lists of named entities, one from
    #  spaCy NER and the other from DBpedia-spotlight. In some instances, we found duplicate
    #  entities or text spans that were classified by both components. 
    # We used the HEAD word to determine duplicate entries and removed them. 
    # We prioritized the results from spaCy NER for certain types of entities, 
    # specifically those classified as 'CARDINAL', 'DATE', 'ORDINAL', 'MONEY', 'TIME', 'QUANTITY', or 'PERCENT'.
    #  For the rest of the entities, we gave priority to the results from DBpedia-spotlight.
    #  However, there were instances where entities were detected by spaCy NER but not by DBpedia-spotlight 
    # and were not part of the preferred list. In such cases, we kept those entities as it is.   

    def deduplicate_named_entities(self, document_id):

        self.get_and_assign_head_info_to_entity_multitoken(document_id)
        self.get_and_assign_head_info_to_entity_singletoken(document_id)
        self.use_spacy_named_entities(document_id)
        self.use_dbpedia_named_entities(document_id)
        return ''

        
    



    def process_coreference2(self, doc, text_id):
        coref = []
        if doc._.has_coref:
            for cluster in doc._.coref_clusters:
                mention = {'from_index': cluster.mentions[-1].start_char, 'to_index': cluster.mentions[0].start_char}
                coref.append(mention)
            self.store_coref(text_id, coref)
        return coref

    def process_coreference_allennlp(self, doc, text_id):

        result = callAllenNlpCoref("coreference-resolution", doc.text )
        coref = []
        for cluster in result["clusters"]:
            #print("cluster: ", cluster)
            i = 0
            antecedent = ""
            for span in cluster:
                if i == 0:
                    i+=1
                    # the first span will be the antecedent for all other references
                    antecedent = span[0]
                    continue
                mention = {'from_index': span[-1], 'to_index': antecedent}
                coref.append(mention)
                print (mention)
        self.store_coref_allennlp(text_id, coref)

        

        return coref

    def process_coreference(self,doc,text_id):
        coref = []

        if len(doc._.coref_chains) > 0:
            for chain in doc._.coref_chains:
                for x in range(len(chain)-1):
                    mention = {'from_index': doc[chain[x+1].token_indexes[0]].idx, 'to_index': doc[chain[0].token_indexes[0]].idx}
                    coref.append(mention)
            self.store_coref(text_id,coref)
        return coref


    def store_coref2(self, document_id, corefs):
        coref_query = """
                MATCH (document:AnnotatedText)
                WHERE document.id = $documentId 
                WITH document
                UNWIND $corefs as coref  
                MATCH (document)-[*2]->(start:TagOccurrence), (document)-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NamedEntity) 
                WHERE start.index = coref.from_index AND np.index = coref.to_index
                MERGE (start)-[:MENTIONS]->(end)
        """
        self.execute_query(coref_query,
                           {"documentId": document_id, "corefs": corefs})

    
    def store_coref(self, document_id, corefs):
        coref_query = """
                MATCH (document:AnnotatedText)
                WHERE document.id = $documentId 
                WITH document
                UNWIND $corefs as coref  
                MATCH (document)-[*2]->(start:TagOccurrence), (document)-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NamedEntity) 
                WHERE start.index = coref.from_index AND np.index = coref.to_index
                MERGE (start)-[:MENTIONS]->(end)
        """
        # the below commented statement is the previous version of the query which consider noun chunk for mentions relationship
        # MATCH (document)-[*2]->(start:TagOccurrence), (document)-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NounChunk) 
        
        self.execute_query(coref_query,
                           {"documentId": document_id, "corefs": corefs})


    def store_coref_allennlp(self, document_id, corefs):
        coref_query = """
                MATCH (document:AnnotatedText)
                WHERE document.id = $documentId 
                WITH document
                UNWIND $corefs as coref  
                MATCH (document)-[*2]->(start:TagOccurrence), (document)-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NamedEntity) 
                WHERE start.tok_index_doc = coref.from_index AND np.tok_index_doc = coref.to_index
                MERGE (start)-[:MENTIONS]->(end)
        """
        # the below commented statement is the previous version of the query which consider noun chunk for mentions relationship
        # MATCH (document)-[*2]->(start:TagOccurrence), (document)-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NounChunk) 
        
        self.execute_query(coref_query,
                           {"documentId": document_id, "corefs": corefs})

    
    
    
    def process_textrank(self, doc, text_id):
        keywords = []
        spans = []
        for p in doc._.phrases:
            for span in p.chunks:
                item = {"span": span, "rank": p.rank}
                spans.append(item)
        spans = filter_extended_spans(spans)
        for item in spans:
            span = item['span']
            lexme = self.nlp.vocab[span.text]
            if lexme.is_stop or lexme.is_digit or lexme.is_bracket or "-PRON-" in span.lemma_:
                continue
            keyword = {"id": span.lemma_, "start_index": span.start_char, "end_index": span.end_char}
            if len(span.ents) > 0:
                keyword['NE'] = span.ents[0].label_
            keyword['rank'] = item['rank']
            keywords.append(keyword)
        self.store_keywords(text_id, keywords)

    # def create_annotated_text(self, doc, id):
    #     query = """MERGE (ann:AnnotatedText {id: $id})
    #         RETURN id(ann) as result
    #     """
    #     params = {"id": id}
    #     results = self.execute_query(query, params)
    #     return results[0]

    def process_dependencies(self, tag_occurrence_dependencies):
        tag_occurrence_query = """UNWIND $dependencies as dependency
            MATCH (source:TagOccurrence {id: dependency.source})
            MATCH (destination:TagOccurrence {id: dependency.destination})
            MERGE (source)-[:IS_DEPENDENT {type: dependency.type}]->(destination)
                """
        self.execute_query(tag_occurrence_query, {"dependencies": tag_occurrence_dependencies})

    def store_keywords(self, document_id, keywords):
        ne_query = """
            UNWIND $keywords as keyword
            MERGE (kw:Keyword {id: keyword.id})
            SET kw.NE = keyword.NE, kw.index = keyword.start_index, kw.endIndex = keyword.end_index
            WITH kw, keyword
            MATCH (text:AnnotatedText)
            WHERE text.id = $documentId
            MERGE (text)<-[:DESCRIBES {rank: keyword.rank}]-(kw)
        """
        self.execute_query(ne_query, {"documentId": document_id, "keywords": keywords})



#For the purpose of mapping named entities to entity instances in our pipeline, we distinguished between two types of named entities.
#  The first type includes entities that have been successfully disambiguated and assigned a unique KBID by the entity disambiguation module.
#  These entities can be easily mapped by creating instances based on the distinct KBIDs. The second type of named entities, 
# however, are unknown to the entity disambiguation module and are assigned a NULL KBID. To map these named entities, we rely on the text of
#  the named entity's span and its assigned type, which was determined by the NER component. As a result, named entity mentions with the 
# same text value and type are considered to refer to a single entity instance.

    def build_entities_inferred_graph(self, document_id):
        extract_direct_entities_query = """
            MATCH (document:AnnotatedText)
            WHERE document.id = $documentId
            WITH document
            MATCH (document)-[*3..3]->(ne:NamedEntity)
            WHERE NOT ne.type IN ['NP', 'TIME', 'ORDINAL', 'NUMBER', 'MONEY', 'DATE', 'CARDINAL', 'QUANTITY', 'PERCENT'] AND ne.kb_id IS NOT NULL
            WITH ne
            MERGE (entity:Entity {type: ne.type, kb_id:ne.kb_id, id: split(ne.kb_id, '/')[-1]})
            MERGE (ne)-[:REFERS_TO {type: "evoke"}]->(entity)
        """

        # extract_indirect_entities_query = """
        #     MATCH (document:AnnotatedText)
        #     WHERE document.id = $documentId
        #     WITH document
        #     MATCH (document)-[*3..3]->(ne:NamedEntity)<-[:MENTIONS]-(mention)
        #     WHERE NOT ne.type IN ['NP', 'ORDINAL', 'NUMBER', 'DATE', 'CARDINAL', 'QUANTITY', 'PERCENT']
        #     WITH ne, mention
        #     MERGE (entity:Entity {type: ne.type, id:ne.value})
        #     MERGE (mention)-[:REFERS_TO {type: "access"}]->(entity)
        # """


        # Here we have type and id as the unique identfier for Entity instances. It means if a NamedEntity has same type and same value
        # then it will consider unique. Some more investigations into this matter is required. 
        # However Entity deduplication will be performed using coreferencing information. 
        extract_indirect_entities_query = """
        MATCH (document:AnnotatedText)
            WHERE document.id = $documentId
            WITH document
            MATCH (document)-[*3..3]->(ne:NamedEntity)
            WHERE NOT ne.type IN ['NP', 'TIME', 'ORDINAL', 'MONEY', 'NUMBER', 'DATE', 'CARDINAL', 'QUANTITY', 'PERCENT'] AND ne.kb_id IS NULL
            WITH ne
            MERGE (entity:Entity {type: ne.type, kb_id:ne.value, id:ne.value})
            MERGE (ne)-[:REFERS_TO {type: "evoke"}]->(entity)
        """
        self.execute_query(extract_direct_entities_query, {"documentId": document_id})
        self.execute_query(extract_indirect_entities_query, {"documentId": document_id})

    def extract_relationships(self, document_id, rules):
        extract_relationships_query = """
            MATCH (document:AnnotatedText)
            WHERE document.id = $documentId
            WITH document
            UNWIND $rules as rule
            MATCH (document)-[*2..2]->(verb:TagOccurrence {pos: "VBD"})
            MATCH (verb:TagOccurrence {pos: "VBD"})
            WHERE verb.lemma IN rule.verbs
            WITH verb, rule
            MATCH (verb)-[:IS_DEPENDENT {type:"nsubj"}]->(subject)-[:PARTICIPATES_IN]->(subjectNe:NamedEntity)
            WHERE subjectNe.type IN rule.subjectTypes
            MATCH (verb)-[:IS_DEPENDENT {type:"dobj"}]->(object)-[:PARTICIPATES_IN]->(objectNe:NamedEntity {type: "WORK_OF_ART"})
            WHERE objectNe.type IN rule.objectTypes
            WITH verb, subjectNe, objectNe, rule
            MERGE (subjectNe)-[:IS_RELATED_TO {root: verb.lemma, type: rule.type}]->(objectNe)
        """
        self.execute_query(extract_relationships_query, {"documentId": document_id, "rules":rules})

    def build_relationships_inferred_graph(self, document_id):
        extract_relationships_query = """
            MATCH (document:AnnotatedText)
            WHERE document.id = $documentId
            WITH document
            MATCH (document)-[*2..3]->(ne1:NamedEntity)
            MATCH (entity1:Entity)<-[:REFERS_TO]-(ne1:NamedEntity)-[r:IS_RELATED_TO]->(ne2:NamedEntity)-[:REFERS_TO]->(entity2:Entity)
            MERGE (evidence:Evidence {id: id(r), type:r.type})
            MERGE (rel:Relationship {id: id(r), type:r.type})
            MERGE (ne1)<-[:SOURCE]-(evidence)
            MERGE (ne2)<-[:DESTINATION]-(evidence)
            MERGE (rel)-[:HAS_EVIDENCE]->(evidence)
            MERGE (entity1)<-[:FROM]-(rel)
            MERGE (entity2)<-[:TO]-(rel)
        """
        self.execute_query(extract_relationships_query, {"documentId": document_id})


    def execute_query3(self, query, params):
        session = None
        results = []

        try:
            session = self._driver.session()
            response = session.run(query, params)
            for item in response:
                results.append(item)
        except Exception as e:
            print("Query Failed: ", e)
        finally:
            if session is not None:
                session.close()
        return results


    def execute_query(self, query, params):
        session = None
        response = None
        results = []

        try:
            session = self._driver.session()
            response =  session.run(query, params)
            for items in response:
                item = items["result"]
                results.append(item)
        except Exception as e:
            print("Query Failed: ", str(e))
            traceback.print_exc()
        finally:
            if session is not None:
                session.close()
        return results


    def execute_query2(self, query, params):
        results = []
        with self._driver.session() as session:
            for items in session.run(query, params):
                item = items["result"]
                results.append(item)
        return results


def filter_spans(spans):
    get_sort_key = lambda span: (span.end - span.start, -span.start)
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for span in sorted_spans:
        # Check for end - 1 here because boundaries are inclusive
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            result.append(span)
        seen_tokens.update(range(span.start, span.end))
    result = sorted(result, key=lambda span: span.start)
    return result


def filter_extended_spans(items):
    get_sort_key = lambda item: (item['span'].end - item['span'].start, -item['span'].start)
    sorted_spans = sorted(items, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for item in sorted_spans:
        # Check for end - 1 here because boundaries are inclusive
        if item['span'].start not in seen_tokens and item['span'].end - 1 not in seen_tokens:
            result.append(item)
        seen_tokens.update(range(item['span'].start, item['span'].end))
    result = sorted(result, key=lambda span: span['span'].start)
    return result


import os
import spacy
import sys



from spacy.tokens import Doc, Token, Span
from util.GraphDbBase import GraphDBBase
import xml.etree.ElementTree as ET
from py2neo import Graph
from py2neo import *
import configparser
import requests
import json




class TlinksRecognizer():

    uri=""
    username =""
    password =""
    graph=""

    def __init__(self, argv):
        #super().__init__(command=__file__, argv=argv)
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
        #self.__text_processor = TextProcessor(self.nlp, self._driver)
        #self.create_constraints()

        

    
    def get_annotated_text(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = "MATCH (n:AnnotatedText) RETURN n.id"
        data= graph.run(query).data()

        annotatedd_text_docs= list()

        listDocIDs=[]
        for record in data:
            #print(record)
            #print(record.get("n.text"))
            #t = (record.get("n.text"), {'text_id': record.get("n.id")})
            id = record.get('n.id')
            #text = record.get('n.text')
            listDocIDs.append(id)
        
        return listDocIDs


        #CASE 1 - to create a DCT node for a document*******
        #-- this query should be executed in the beginning of the temporal phase. 
        #-- precondition: the annotatedText should be there.
    def create_DCT_node(self, doc_id):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ match (ann:AnnotatedText where ann.id = """+str(doc_id)+""")
                    merge (DCT:TIMEX {type: 'DATE', value: replace(split(ann.creationtime, 'T')[0],'-','') , tid: 'dct'+ toString(ann.id), 
                    doc_id: ann.id})<-[:CREATED_ON]-(ann)
                """
        
        data= graph.run(query).data()
        
        return ""


    
    #CASE 1. 
    #//TLINKS: linking events based on their context provided by SRL
    #// head is a verb here that connects two events via frameargument. 
    #// TODO: its only works for after. other temporal conjunctions or preposition need to be added. such as before.
    def create_tlinks_case1(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ MATCH p= (e1:TEvent)-[:DESCRIBES]-(f1:Frame)<-[:PARTICIPANT]-(fa:FrameArgument where fa.type = 'ARGM-TMP')
                    <-[:PARTICIPATES_IN]-(et:TagOccurrence where et.pos = 'VBD')-[:PARTICIPATES_IN]->(f2:Frame)-[:DESCRIBES]-(e2:TEvent) 
                    where fa.headTokenIndex = et.tok_index_doc and fa.signal = 'after'
                    with *
                    match (e1),(e2)
                    merge (e1)-[tl:TLINK]-(e2)
                    on create set tl.relType = 'AFTER', tl.source = 't2g'
                    on match set tl.relType = 'AFTER'
                    RETURN p
        
        """

        data= graph.run(query).data()
        return ""

    # CASE 2. 
    # // verb which is gerund, i.e., having pos VBG. 
    # // here the verb is not a headword instead its connected with head (most probably a preposition /SCONJ) via PCOMP relation.
    # // TODO: its only works for after. other temporal conjunctions or preposition need to be added. such as before.
    def create_tlinks_case2(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ MATCH p= (e1:TEvent)-[:DESCRIBES]-(f1:Frame)<-[:PARTICIPANT]-(fa:FrameArgument where fa.type = 'ARGM-TMP')
                    <-[:PARTICIPATES_IN]-(et:TagOccurrence where et.pos = 'VBG')-[:PARTICIPATES_IN]->(f2:Frame)-[:DESCRIBES]-(e2:TEvent) 
                    where fa.complement = et.text and fa.syntacticType = 'EVENTIVE'
                    with *
                    merge (e1)-[tl:TLINK]-(e2)
                    with *
                    set tl.source = 't2g', (case when fa.signal in ['after'] then tl END).relType = 'AFTER',
                    (case when fa.signal in ['before'] then tl END).relType = 'BEFORE'
                    RETURN p
        
        """

        data= graph.run(query).data()
        return ""


    # CASE 3
    # // SIMILAR TO CASE 1 BUT head is VBG and whose text is 'following'
    # // example: following in 'following the European Central Bank'
    def create_tlinks_case3(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ MATCH p= (e1:TEvent)-[:DESCRIBES]-(f1:Frame)<-[:PARTICIPANT]-(fa:FrameArgument where fa.type = 'ARGM-TMP')
                    <-[:PARTICIPATES_IN]-(et:TagOccurrence where et.pos = 'VBG')-[:PARTICIPATES_IN]->(f2:Frame)-[:DESCRIBES]-(e2:TEvent) 
                    where fa.headTokenIndex = et.tok_index_doc and fa.syntacticType = 'EVENTIVE'
                    with *
                    merge (e1)-[tl:TLINK]-(e2)
                    with *
                    set tl.source = 't2g', 
                    (case when fa.signal in ['after'] then tl END).relType = 'AFTER',
                    (case when fa.signal in ['before'] then tl END).relType = 'BEFORE',
                    (case when fa.signal in ['following'] then tl END).relType = 'SIMULTANEOUS'
                    RETURN p
        
        """

        data= graph.run(query).data()
        return ""




    
    # CASE 4 
    # // event to timex
    # // TIMEX is corresponding to the head of FA without any preposition
    # // straight-forward case of IS_INCLUDED TLINK
    def create_tlinks_case4(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ MATCH p = (t:TIMEX)<-[:TRIGGERS]-(h:TagOccurrence where h.pos in ['NN','NNP'])-[:PARTICIPATES_IN]->
                    (fa:FrameArgument {type: 'ARGM-TMP'})-[:PARTICIPANT]-(f:Frame)-[:DESCRIBES]->(e:TEvent)
                    // TIMEX is corresponding to the head of FA without any preposition
                    WHERE fa.headTokenIndex = h.tok_index_doc
                    MERGE (e)-[tlink:TLINK]->(t)
                    SET tlink.source = 't2g', tlink.relType = 'IS_INCLUDED'
        
        """

        data= graph.run(query).data()
        return ""



    # CASE 5
    # // Event to timex 
    # //FAs of type ARGM-TMP with PREPOSITIONS
    # // SIGNAL is the preposition (usually)
    def create_tlinks_case5(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ MATCH p = (t:TIMEX)<-[:TRIGGERS]-(pobj:TagOccurrence where pobj.pos in ['NN','NNP'])-[:PARTICIPATES_IN]->(fa:FrameArgument {type: 'ARGM-TMP', syntacticType: 'IN'})-[:PARTICIPANT]-(f:Frame)-[:DESCRIBES]->(e:TEvent)
                    WHERE fa.complementIndex = pobj.tok_index_doc

                    MERGE (e)-[tlink:TLINK]->(t)
                    SET tlink.source = 't2g',
                    (CASE WHEN t.type = 'DURATION' and toLower(fa.head) = 'for' and e.tense in ['PAST', 'PRESENT'] THEN tlink END).relType = 'MEASURE',
                    (CASE WHEN t.type = 'DURATION' and toLower(fa.head) IN ['in', 'during'] THEN tlink END).relType = 'IS_INCLUDED',
                    (CASE WHEN t.type = 'DURATION' and t.quant <> 'N/A' and fa.head IN ['in'] THEN tlink END).relType = 'AFTER',
                    (CASE WHEN t.type = 'DURATION' and toLower(fa.head) IN ['for'] and e.tense in ['PAST', 'PRESENT'] and e.aspect = 'PERFECTIVE' THEN tlink END).relType = 'BEGUN_BY',
                    (CASE WHEN t.type = 'DATE' and toLower(fa.head) IN ['since'] THEN tlink END).relType = 'BEGUN_BY',
                    (CASE WHEN t.type = 'DURATION' and toLower(fa.head) IN ['in'] THEN tlink END).relType = 'AFTER',
                    (CASE WHEN t.type = 'DATE' and toLower(fa.head) IN ['by'] THEN tlink END).relType = 'ENDED_BY',
                    (CASE WHEN t.type = 'DATE' and toLower(fa.head) IN ['until'] and e.tense in ['PAST'] THEN tlink END).relType = 'ENDED_BY',
                    (CASE WHEN t.type = 'TIME' and toLower(fa.head) IN ['by'] THEN tlink END).relType = 'BEFORE',
                    (CASE WHEN t.type in ['TIME', 'DATE', 'DURATION'] and toLower(fa.head) IN ['before'] THEN tlink END).relType = 'BEFORE',
                    (CASE WHEN t.type in ['TIME', 'DATE', 'DURATION'] and toLower(fa.head) IN ['after'] THEN tlink END).relType = 'AFTER',
                    (CASE WHEN t.type in ['TIME', 'DATE', 'DURATION'] and toLower(fa.head) IN ['on'] THEN tlink END).relType = 'IS_INCLUDED',
                    //case added as per the observation during evaluation for 'in' e.g.,Temporal FA 'in the third quarter of this year' should be mentioned with 'IS_INCLUDED'
                    (CASE WHEN t.type in ['TIME', 'DATE', 'DURATION'] and toLower(fa.head) IN ['in'] THEN tlink END).relType = 'IS_INCLUDED',
                    (CASE WHEN t.type in ['TIME', 'DATE'] and toLower(fa.head) IN ['on'] THEN tlink END).relType = 'IS_INCLUDED'

                    //return p
                    //MERGE (e)-[tlink:TLINK]->(t)
                    //SET tlink.source = 't2g', tlink.relType = 'IS_INCLUDED'
        
        """

        data= graph.run(query).data()
        return ""




    #CASE 6 (NOT COMPLETE see the todo)
    #// Events with DCT
    #// Events relaized by FINITE verb forms will be linked to the DCT according to the tense and aspect of the event. 
    #//PRECONDITION: this event is non-modal. It means that modal property must be null
    #// TODO: we need to study whether checking the modality is really required here. 

    def create_tlinks_case6(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ MATCH p = (e:TEvent)<-[:TRIGGERS]-(t:TagOccurrence)<-[:HAS_TOKEN]-(s:Sentence)<-[:CONTAINS_SENTENCE]-(ann:AnnotatedText)-[:CREATED_ON]->(dct:TIMEX)
                    WHERE e.modal IS NULL and NOT e.tense IN ['PRESPART', 'PASPART', 'INFINITIVE'] and NOT t.pos  IN ['NNP', 'NNS', 'NN'] 
                    //AND NOT (e.tense IN ['PRESENT'] and e.aspect IN ['NONE'])
                    MERGE (e)-[tlink:TLINK]-(dct)
                    SET tlink.source = 't2g',
                    (CASE WHEN e.tense in ['FUTURE'] THEN tlink END).relType = 'AFTER',
                    (CASE WHEN e.tense in ['PRESENT'] and e.aspect = 'PROGRESSIVE' THEN tlink END).relType = 'IS_INCLUDED',
                    (CASE WHEN e.tense in ['PAST'] THEN tlink END).relType = 'IS_INCLUDED',
                    (CASE WHEN e.tense in ['PRESENT'] and e.aspect = 'PERFECTIVE' THEN tlink END).relType = 'BEFORE',
                    (CASE WHEN e.tense in ['PASTPART'] and e.aspect = 'NONE' THEN tlink END).relType = 'IS_INCLUDED'

                    RETURN p
        
        """

        data= graph.run(query).data()
        return ""


    # / PURPOSE: To add/link core-participants to an Event object. Core-Participants include ['ARG0','ARG1','ARG2','ARG3','ARG4']
    # // PRECONDITION: Event is already linked with the corresponding Frame
    # //               FrameArgument is referring to an Entity
    # // POSTCONDITION: some attributes need to be added as a relationship properties such as participant role (e.g., ARG0, 1), 
    # preposition (in case of prepostional frame argument) 
    # // DESCRIPTION: It will not include contextual or adjunts particpants such as MNR, TMP, CAU etc.                 
    def add_event_participants(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ match p= (event:TEvent)<-[:DESCRIBES]-(f:Frame)<-[:PARTICIPANT]-
                    (fa:FrameArgument where fa.type in ['ARG0','ARG1','ARG2','ARG3','ARG4'])-[:REFERS_TO]->(e:Entity)
                    merge (e)-[r:PARTICIPANT]->(event)
                    set r.type = fa.type, (case when fa.syntacticType in ['IN'] then r END).prep = fa.head 
                    return p
        
        """

        data= graph.run(query).data()
        return ""



    def link_event_to_frame(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ match p = (f:Frame)<-[:PARTICIPATES_IN]-(t:TagOccurrence)-[:TRIGGERS]->(event:TEvent)
                    merge (f)-[:DESCRIBES]->(event)
                    return p
        
        """

        data= graph.run(query).data()
        return ""

    # it detect those frames which are modal and set attribute 'modal' with the value of modal word.
    # we just need to look for frameargument whose type is ARGM-MOD
    def tag_modal_frame(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """ match p = (e:TEvent)<-[:DESCRIBES]-(f:Frame)<-[:PARTICIPANT]-(fa:FrameArgument {type:'ARGM-MOD'})
                    set f.modal = fa.text, e.modal = fa.text
                    return p
        
        """

        data= graph.run(query).data()
        return ""


    


if __name__ == '__main__':
    tp= TlinksRecognizer(sys.argv[1:])

    # This script should be executed after temporal phase and refinement phase
    # this is follow-up part of refinement phase

    # query for getting all AnnotatedDoc

    #this method is temporary here, will be added into other class file later. 
    #tp.link_event_to_frame()
    tp.tag_modal_frame()
    #tp.add_event_participants()
    tp.create_tlinks_case1()
    tp.create_tlinks_case2()
    tp.create_tlinks_case3()
    tp.create_tlinks_case4()
    tp.create_tlinks_case5()
    tp.create_tlinks_case6()
        

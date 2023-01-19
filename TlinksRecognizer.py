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


if __name__ == '__main__':
    tp= TlinksRecognizer(sys.argv[1:])

    # This script should be executed after temporal phase and refinement phase
    # this is follow-up part of refinement phase

    # query for getting all AnnotatedDoc

    #this method is temporary here, will be added into other class file later. 
    tp.link_event_to_frame()
    tp.add_event_participants()
    tp.create_tlinks_case1()
    tp.create_tlinks_case2()
    tp.create_tlinks_case3()
        

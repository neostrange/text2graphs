import os
import spacy
import sys
#import neuralcoref
import coreferee
from util.SemanticRoleLabeler import SemanticRoleLabel
from util.EntityFishingLinker import EntityFishing
from spacy.tokens import Doc, Token, Span
from util.RestCaller import callAllenNlpApi
import TextProcessor
from util.GraphDbBase import GraphDBBase
from TextProcessor import TextProcessor
import xml.etree.ElementTree as ET
from py2neo import Graph
from py2neo import *
import configparser




class EventEnrichmentPhase():

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

         


    # Link FA to Event as a DESCRIBES relationship
    def link_frameArgument_to_event(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p = (f:Frame)<-[:PARTICIPATES_IN]-(t:TagOccurrence)-[:TRIGGERS]->(event:TEvent)
                        merge (f)-[:DESCRIBES]->(event)
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""




    #// PURPOSE: To add/link core-participants to an Event object. Core-Participants include ['ARG0','ARG1','ARG2','ARG3','ARG4']
    #// PRECONDITION: Event is already linked with the corresponding Frame
    #//               FrameArgument is referring to an Entity
    #// POSTCONDITION: some attributes need to be added as a relationship properties such as participant 
    #// role (e.g., ARG0, 1), preposition (in case of prepostional frame argument) 
    #// DESCRIPTION: It will not include contextual or adjunts particpants such as MNR, TMP, CAU etc.                 

    def add_core_participants_to_event(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                    match p= (event:TEvent)<-[:DESCRIBES]-(f:Frame)<-[:PARTICIPANT]-(fa:FrameArgument where fa.type in 
                    ['ARG0','ARG1','ARG2','ARG3','ARG4'])-[:REFERS_TO]->(e:Entity)
                    merge (e)-[r:PARTICIPANT]->(event)
                    set r.type = fa.type, (case when fa.syntacticType in ['IN'] then r END).prep = fa.head 
                    return p    
        
        """
        data= graph.run(query).data()
        
        return ""



if __name__ == '__main__':
    tp= EventEnrichmentPhase(sys.argv[1:])

    tp.link_frameArgument_to_event()
    tp.add_core_participants_to_event()











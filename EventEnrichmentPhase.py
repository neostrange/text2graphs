import os
import spacy
import sys
#import neuralcoref

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



# This phase will run after the TemporalPhase.
# NOTES: 
## 
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
    #//               FrameArgument is referring to an Entity or a NUMERIC
    #// POSTCONDITION: some attributes need to be added as a relationship properties such as participant 
    #// role (e.g., ARG0, 1), preposition (in case of prepostional frame argument) 
    #// DESCRIPTION: It will not include contextual or adjunts particpants such as MNR, TMP, CAU etc.
    #// version 1.1 : added support for NUMERIC participants.                  

    def add_core_participants_to_event(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                    match p= (event:TEvent)<-[:DESCRIBES]-(f:Frame)<-[:PARTICIPANT]-(fa:FrameArgument where fa.type in 
                    ['ARG0','ARG1','ARG2','ARG3','ARG4'])-[:REFERS_TO]->(e)
                    where e:Entity OR e:NUMERIC
                    merge (e)-[r:PARTICIPANT]->(event)
                    set r.type = fa.type, (case when fa.syntacticType in ['IN'] then r END).prep = fa.head 
                    return p     
        
        """
        data= graph.run(query).data()
        
        return ""
    


# custom labels for non-core arguments and storing it as a node attribute: argumentType. The second step the value in the fa.argumentType 
# will be set as a lable for this node. It will perform event enrichment fucntion as well as attaching propbank modifiers arguments 
# with the event node. 
# TODO: Though we have found fa nodes with duplicates content with same label or arg type but we will deal with it later.                 

    def add_non_core_participants_to_event(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                    MATCH (event:TEvent)<-[:DESCRIBES]-(f:Frame)<-[:PARTICIPANT]-(fa:FrameArgument)
                    WHERE NOT fa.type IN ['ARG0', 'ARG1', 'ARG2', 'ARG3', 'ARG4', 'ARGM-TMP']
                    WITH event, f, fa
                    SET fa.argumentType =
                        CASE fa.type
                        WHEN 'ARGM-COM' THEN 'Comitative'
                        WHEN 'ARGM-LOC' THEN 'Locative'
                        WHEN 'ARGM-DIR' THEN 'Directional'
                        WHEN 'ARGM-GOL' THEN 'Goal'
                        WHEN 'ARGM-MNR' THEN 'Manner'
                        WHEN 'ARGM-TMP' THEN 'Temporal'
                        WHEN 'ARGM-EXT' THEN 'Extent'
                        WHEN 'ARGM-REC' THEN 'Reciprocals'
                        WHEN 'ARGM-PRD' THEN 'SecondaryPredication'
                        WHEN 'ARGM-PRP' THEN 'PurposeClauses'
                        WHEN 'ARGM-CAU' THEN 'CauseClauses'
                        WHEN 'ARGM-DIS' THEN 'Discourse'
                        WHEN 'ARGM-MOD' THEN 'Modals'
                        WHEN 'ARGM-NEG' THEN 'Negation'
                        WHEN 'ARGM-DSP' THEN 'DirectSpeech'
                        WHEN 'ARGM-ADV' THEN 'Adverbials'
                        WHEN 'ARGM-ADJ' THEN 'Adjectival'
                        WHEN 'ARGM-LVB' THEN 'LightVerb'
                        WHEN 'ARGM-CXN' THEN 'Construction'
                        ELSE 'NonCore'
                        END
                    MERGE (fa)-[r:PARTICIPANT]->(event)
                    SET r.type = fa.type,
                        (CASE WHEN fa.syntacticType IN ['IN'] THEN r END).prep = fa.head 
                    RETURN event, f, fa, r     
        
        """
        data= graph.run(query).data()
        
        return ""
    



 # 2nd step where we set the labels for the non-core fa arguments are assigned

    def add_label_to_non_core_fa(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                   
                    MATCH (fa:FrameArgument)
                    WHERE fa.argumentType is not NULL
                    CALL apoc.create.addLabels(id(fa), [fa.argumentType]) YIELD node
                    RETURN node     
        
        """
        data= graph.run(query).data()
        
        return ""



if __name__ == '__main__':
    tp= EventEnrichmentPhase(sys.argv[1:])

    tp.link_frameArgument_to_event()
    tp.add_core_participants_to_event()
    tp.add_non_core_participants_to_event()
    tp.add_label_to_non_core_fa()











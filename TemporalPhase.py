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


# call TTK service which uses TARSQI toolkit and 
# call Heideltime service for temporal expression detection and normalization
# It also stores the DCT i.e., document creation time.
# ORDER of EXECUTION: after refinement phase

class TemporalPhase():

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
        
        data= graph.run(query,parameters={'doc_id': doc_id}).data()
        
        return ""


    def create_tlinks_e2e(self, doc_id):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """CALL apoc.load.xml('"""+str(doc_id)+""".xml') 
                    YIELD value as result
                    UNWIND [item in result._children where item._type ="tarsqi_tags"] AS tarsqi
                    UNWIND [item in tarsqi._children where item._type ="TLINK"] AS tlink
                    WITH tlink.lid as lid, tlink.origin as origin, tlink.relType as relType, tlink.relatedToTime as relatedToTime, tlink.timeID as timeID, tlink.eventInstanceID as eventInstanceID, tlink.relatedToEventInstance as relatedToEventInstance, tlink.syntax as syntax
                    foreach(ignoreMe IN CASE WHEN eventInstanceID IS NOT NULL and relatedToEventInstance IS NOT NULL THEN [1] ELSE [] END | merge (e1:TEvent{eiid:eventInstanceID, doc_id: """+str(doc_id)+"""}) merge (e2:TEvent{eiid:relatedToEventInstance, doc_id:"""+str(doc_id)+"""}) MERGE (e1)-[:TLINK{id:lid, relType:relType}]->(e2))
                """
        
        data= graph.run(query).data()
        
        return ""


    def create_tlinks_e2t(self, doc_id):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """CALL apoc.load.xml('"""+str(doc_id)+""".xml') 
                    YIELD value as result
                    UNWIND [item in result._children where item._type ="tarsqi_tags"] AS tarsqi
                    UNWIND [item in tarsqi._children where item._type ="TLINK"] AS tlink
                    WITH tlink.lid as lid, tlink.origin as origin, tlink.relType as relType, tlink.relatedToTime as relatedToTime, tlink.timeID as timeID, tlink.eventInstanceID as eventInstanceID, tlink.relatedToEventInstance as relatedToEventInstance, tlink.syntax as syntax
                    foreach(ignoreMe IN CASE WHEN relatedToTime IS NOT NULL and eventInstanceID IS NOT NULL THEN [1] ELSE [] END | merge (e:TEvent{eiid:eventInstanceID, doc_id:"""+str(doc_id)+"""}) merge (t:TIMEX {tid:relatedToTime, doc_id:"""+str(doc_id)+"""}) MERGE (e)-[:TLINK{id:lid, relType:relType}]->(t))
                """
        
        data= graph.run(query).data()
        
        return data

        

    def create_tlinks_t2t(self, doc_id):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """CALL apoc.load.xml('"""+str(doc_id)+""".xml')
                    YIELD value as result
                    UNWIND [item in result._children where item._type ="tarsqi_tags"] AS tarsqi
                    UNWIND [item in tarsqi._children where item._type ="TLINK"] AS tlink
                    WITH tlink.lid as lid, tlink.origin as origin, tlink.relType as relType, tlink.relatedToTime as relatedToTime, tlink.timeID as timeID, tlink.eventInstanceID as eventInstanceID, tlink.relatedToEventInstance as relatedToEventInstance, tlink.syntax as syntax
                    foreach(ignoreMe IN CASE WHEN relatedToTime IS NOT NULL and timeID IS NOT NULL THEN [1] ELSE [] END | merge (t1:TIMEX{tid:timeID, doc_id:"""+str(doc_id)+"""}) merge (t2:TIMEX {tid:relatedToTime, doc_id:"""+str(doc_id)+"""}) MERGE (t1)-[:TLINK{id:lid, relType:relType}]->(t2))
                    """
        
        data= graph.run(query).data()
        
        return ""

    def get_doc_text_and_dct(self, doc_id):
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """match (n:AnnotatedText) where n.id = """+str(doc_id)+""" return n.text, n.creationtime """
        
        data = graph.run(query).data()
        result={}

        result["text"] = str(data[0].get('n.text'))
        result["dct"] = data[0].get('n.creationtime')
        
        return result



    def create_timexes2(self, doc_id):
        response_dict = self.get_doc_text_and_dct(doc_id)

        result_xml= self.callHeidelTimeService(response_dict)
        doc_id = str(doc_id)

        #print(result_xml)
        graph = Graph(self.uri, auth=(self.username, self.password))




        query =  """ WITH $result_xml
        AS xmlString
        WITH apoc.xml.parse(xmlString) AS value
        UNWIND [item in value._children where item._type ="TIMEX3"] AS timex
        WITH timex.start_index as begin, timex.end_index as end, timex.origin as orig, timex.tid as tid, timex.type as typ, timex.value as val, timex._text as text, timex.quant as quant
        MERGE (t:TIMEX {tid:tid, doc_id:toInteger($doc_id), start_index:toInteger(begin), end_index:toInteger(end), origin:'text2graph', type:typ,  value:val, text: text, quant: coalesce(quant,"N/A")})
        with t
        MATCH (a:AnnotatedText {id:toInteger($doc_id)})-[*2]->(ta:TagOccurrence) where ta.index>= toInteger(t.start_index) AND ta.end_index <= toInteger(t.end_index)
        MERGE (ta)-[:TRIGGERS]->(t)
        """
        #query = query.replace("\n","")
        #query = query.replace("\\","")
        data= graph.run(query,parameters={'result_xml': result_xml, 'doc_id': doc_id}).data()
        
        return ""


    def callHeidelTimeService(self, parameters):
        dct = parameters.get("dct")
        text = parameters.get("text")
        
        #String.replace(split(ann.creationtime, 'T')[0],'-','')


        dct = dct.split('T')[0]


        data = {"input":text, "dct": dct}

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}


        response = requests.post("http://localhost:5000/annotate", json=data, headers=headers)

        # print(response.content)
        return response.text



    def create_timexes(self, doc_id):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """CALL apoc.load.xml('"""+str(doc_id)+""".xml') 
                    YIELD value as result
                    UNWIND [item in result._children where item._type ="tarsqi_tags"] AS tarsqi
                    UNWIND [item in tarsqi._children where item._type ="TIMEX3"] AS timex
                    WITH timex.begin as begin, timex.end as end, timex.origin as orig, timex.tid as tid, timex.type as typ, timex.value as val
                    MERGE (t:TIMEX {tid:tid, doc_id:"""+str(doc_id)+""", begin:toInteger(begin), end:toInteger(end), origin:orig, type:typ,  value:val})
                    WITH t
                    MATCH (a:AnnotatedText {id:"""+str(doc_id)+"""})-[*2]->(ta:TagOccurrence) where ta.index>= toInteger(t.begin) AND ta.end_index <= toInteger(t.end)
                    MERGE (ta)-[:TRIGGERS]->(t)"""
        
        data= graph.run(query).data()
        
        return ""




    def callTtkService(self, parameters):
        dct = parameters.get("dct")
        text = parameters.get("text")
        
        #String.replace(split(ann.creationtime, 'T')[0],'-','')


        dct = dct.split('T')[0]

        dct.replace('-','')

        data = {"input":text, "dct": dct}

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}


        response = requests.post("http://localhost:5050/annotate", json=data, headers=headers)

        # print(response.content)
        return response.text


    def create_tevents2(self, doc_id):

        response_dict = self.get_doc_text_and_dct(doc_id)

        result_xml= self.callTtkService(response_dict)
        doc_id = str(doc_id)

        #print(result_xml)

        graph = Graph(self.uri, auth=(self.username, self.password))



        query = """WITH $result_xml
                    AS xmlString
                    WITH apoc.xml.parse(xmlString) AS result
                    UNWIND [item in result._children where item._type ="tarsqi_tags"] AS tarsqi
                    UNWIND [item in tarsqi._children where item._type ="EVENT"] AS event
                    WITH event.begin as begin, event.end as end, event.aspect as aspect, event.class as class, event.eid as eid, event.eiid as eiid, event.epos as epos, event.form as form, event.pos as pos, event.tense as tense
                    match (a:AnnotatedText {id:"""+str(doc_id)+"""})-[*2]->(ta:TagOccurrence) where ta.index= toInteger(begin) 
                    MERGE (ta)-[:TRIGGERS]->(event:TEvent{doc_id:"""+str(doc_id)+""", eiid:eiid}) set event.begin=toInteger(begin), event.end=toInteger(end), event.aspect=aspect, event.class=class,  event.epos=epos, event.form=form, event.pos=pos, event.tense=tense"""
        
        data= graph.run(query,parameters={'result_xml': result_xml, 'doc_id': doc_id}).data()
        
        return ""



    def create_tevents(self, doc_id):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """CALL apoc.load.xml('"""+str(doc_id)+""".xml') 
                    YIELD value as result
                    UNWIND [item in result._children where item._type ="tarsqi_tags"] AS tarsqi
                    UNWIND [item in tarsqi._children where item._type ="EVENT"] AS event
                    WITH event.begin as begin, event.end as end, event.aspect as aspect, event.class as class, event.eid as eid, event.eiid as eiid, event.epos as epos, event.form as form, event.pos as pos, event.tense as tense
                    match (a:AnnotatedText {id:"""+str(doc_id)+"""})-[*2]->(ta:TagOccurrence) where ta.index= toInteger(begin) 
                    MERGE (ta)-[:TRIGGERS]->(event:TEvent{doc_id:"""+str(doc_id)+""", eiid:eiid}) set event.begin=toInteger(begin), event.end=toInteger(end), event.aspect=aspect, event.class=class,  event.epos=epos, event.form=form, event.pos=pos, event.tense=tense"""
        
        data= graph.run(query).data()
        
        return ""

if __name__ == '__main__':
    tp= TemporalPhase(sys.argv[1:])

    # create the filename by getting the id of the document. 

    # query for getting all AnnotatedDoc
    ids = tp.get_annotated_text()
    for id in ids:
        
        tp.create_DCT_node(id)
        tp.create_tevents2(id)
        #tp.create_timexes(id)
        tp.create_timexes2(id)
        #tp.create_tlinks_e2e(id)
        #tp.create_tlinks_e2t(id)
        #tp.create_tlinks_t2t(id)
        

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




class RefinementPhase():

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

        
# PHASE 1 
# Identification of HEADWORD and assigning related metadata about headword
# Subjects include, NamedEntity, Antecedent, CorefMention, FrameArgument
    
    #NamedEntity Multitoken
    def get_and_assign_head_info_to_entity_multitoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))


        # query to find the head of a NamedEntity. (case is for entitities composed of  multitokens )
        # TODO: the head for the NAM should include the whole extent of the name. see newsreader annotation guidelines 
        # for more information. 
        query = """    
                        match p= (a:TagOccurrence)-[:PARTICIPATES_IN]->(f:NamedEntity), q= (a)-[:IS_DEPENDENT]->()--(f)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                        WITH f, a, p
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, 
                        (case when a.pos in ['NNS', 'NN'] then f END).syntacticType ='NOMINAL' ,
                        (case when a.pos in ['NNP', 'NNPS'] then f END).syntacticType ='NAM'
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""


    #NamedEntity Singletoken
    def get_and_assign_head_info_to_entity_singletoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))


        # query to find the head of a NamedEntity. (case is for entitities composed of  single token )
        query = """    
                        match p= (a:TagOccurrence)-[:PARTICIPATES_IN]->(c:NamedEntity)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(c)) and not exists ((a)-[:IS_DEPENDENT]->()--(c))
                        WITH c, a, p
                        set c.head = a.text, c.headTokenIndex = a.tok_index_doc, 
                        (case when a.pos in ['NNS', 'NN'] then c END).syntacticType ='NOMINAL' , 
                        (case when a.pos in ['NNP', 'NNPS'] then c END).syntacticType ='NAM', 
                        (case when a.pos in ['PRP', 'PRP$'] then c END).syntacticType ='PRO'
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""




    #Antecedent Multitoken
    def get_and_assign_head_info_to_antecedent_multitoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))


        # query to find the head of a NamedEntity. (case is for entitities composed of  multitokens )
        # TODO: the head for the NAM should include the whole extent of the name. see newsreader annotation guidelines 
        # for more information. 
        query = """    
                        match p= (a:TagOccurrence)-[:PARTICIPATES_IN]->(f:Antecedent), q= (a)-[:IS_DEPENDENT]->()--(f)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                        WITH f, a, p
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, 
                        (case when a.pos in ['NNS', 'NN'] then f END).syntacticType ='NOMINAL' ,
                        (case when a.pos in ['NNP', 'NNPS'] then f END).syntacticType ='NAM'
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""


    #Antecedent Singletoken
    def get_and_assign_head_info_to_antecedent_singletoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))


        # query to find the head of a NamedEntity. (case is for entitities composed of  single token )
        query = """    
                        match p= (a:TagOccurrence)-[:PARTICIPATES_IN]->(c:Antecedent)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(c)) and not exists ((a)-[:IS_DEPENDENT]->()--(c))
                        WITH c, a, p
                        set c.head = a.text, c.headTokenIndex = a.tok_index_doc, 
                        (case when a.pos in ['NNS', 'NN'] then c END).syntacticType ='NOMINAL' , 
                        (case when a.pos in ['NNP', 'NNPS'] then c END).syntacticType ='NAM', 
                        (case when a.pos in ['PRP', 'PRP$'] then c END).syntacticType ='PRO'
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""
        
    #CorefMention Multitoken    
    def get_and_assign_head_info_to_corefmention_multitoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))


        # query to find the head of a NamedEntity. (case is for entitities composed of  multitokens )
        # TODO: the head for the NAM should include the whole extent of the name. see newsreader annotation guidelines 
        # for more information. 
        query = """    
                        match p= (a:TagOccurrence)-[:PARTICIPATES_IN]->(f:CorefMention), q= (a)-[:IS_DEPENDENT]->()--(f)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                        WITH f, a, p
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, 
                        (case when a.pos in ['NNS', 'NN'] then f END).syntacticType ='NOMINAL' ,
                        (case when a.pos in ['NNP', 'NNPS'] then f END).syntacticType ='NAM'
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""


    #CorefMention Singletoken
    def get_and_assign_head_info_to_corefmention_singletoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))


        # query to find the head of a NamedEntity. (case is for entitities composed of  single token )
        query = """    
                        match p= (a:TagOccurrence)-[:PARTICIPATES_IN]->(c:CorefMention)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(c)) and not exists ((a)-[:IS_DEPENDENT]->()--(c))
                        WITH c, a, p
                        set c.head = a.text, c.headTokenIndex = a.tok_index_doc, 
                        (case when a.pos in ['NNS', 'NN'] then c END).syntacticType ='NOMINAL' , 
                        (case when a.pos in ['NNP', 'NNPS'] then c END).syntacticType ='NAM', 
                        (case when a.pos in ['PRP', 'PRP$'] then c END).syntacticType ='PRO'
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""

    #To find head info for the FrameArgument i.e., with single token as head
    def get_and_assign_head_info_to_frameArgument_singletoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (a:TagOccurrence where a.pos in ['NNS', 'NN', 'NNP', 'NNPS','PRP', 'PRP$'])--(c:FrameArgument)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(c)) and not exists ((a)-[:IS_DEPENDENT]->()--(c))
                        WITH c, a, p
                        set c.head = a.text, c.headTokenIndex = a.tok_index_doc,
                        (case when a.pos in ['NNS', 'NN'] then c END).syntacticType ='NOMINAL' , 
                        (case when a.pos in ['NNP', 'NNPS'] then c END).syntacticType ='NAM', 
                        (case when a.pos in ['PRP', 'PRP$'] then c END).syntacticType ='PRO'
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""


    #To find head info for the FrameArgument i.e., with multi token as head
    def get_and_assign_head_info_to_frameArgument_multitoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))
        
        query = """    
                        match p= (a:TagOccurrence where a.pos in ['NNS', 'NN', 'NNP', 'NNPS','PRP', 'PRP$'])-
                        [:PARTICIPATES_IN]->(f:FrameArgument), q= (a)-[:IS_DEPENDENT]->()--(f)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                        WITH f, a, p
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, 
                        (case when a.pos in ['NNS', 'NN'] then f END).syntacticType ='NOMINAL' , 
                        (case when a.pos in ['NNP', 'NNPS'] then f END).syntacticType ='NAM',  
                        (case when a.pos in ['PRP', 'PRP$'] then f END).syntacticType ='PRO'
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""



    # // This query first find out those FrameArguments which have preposition as a headword. 
    # // Then It finds out the complement (pobj) of the preposition and mark it as 
    # // complement. This complement will be used to refer to the entity. 
    # // The preoposition word will help in understanding the type of association between frame and
    # // frameargument with respect to the preposition and complement (noun) entity. 
    def get_and_assign_head_info_to_frameArgument_with_preposition(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (a:TagOccurrence where a.pos in ['IN'])--
                        (f:FrameArgument where f.type in ['ARG1', 'ARG0', 'ARG2', 'ARG3', 'ARG4', 'ARGA']), q= (a)-[:IS_DEPENDENT]->()--(f)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, f.syntacticType ='IN'
                        with *
                        match (a)-[x:IS_DEPENDENT]->(c) where x.type = 'pobj' 
                        set f.complement = c.text, f.complementIndex = c.tok_index_doc, 
                        f.complementFullText = substring(f.text, size(f.head)+1)
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""


# PHASE 2 
# Linking FA to NamedEntity

    # //WE JUST NEED TO CONNECT FA TO NAMED ENTITY. 
    # //CASE: when FA's headword is either a proper noun or common noun
    # // It is straight forward as the named entity and FA both sharing the same headword
    def link_frameArgument_to_namedEntity_for_nam_nom(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (f:FrameArgument)<-[:PARTICIPATES_IN]-(head:TagOccurrence )-[:PARTICIPATES_IN]->(ne:NamedEntity)
                        where head.tok_index_doc = f.headTokenIndex and head.tok_index_doc = ne.headTokenIndex
                        merge (f)-[:REFERS_TO]->(ne)
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""

    # //WE JUST NEED TO CONNECT FA TO NAMED ENTITY. 
    # //CASE: when FA's headword is a prepostion. In this case we gonna see the POBJ headword and match it with namedEntity.
    # TODO: add pobj as type of refers_to relationship
    def link_frameArgument_to_namedEntity_for_pobj(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (f:FrameArgument)<-[:PARTICIPATES_IN]-(complementHead:TagOccurrence )-[:PARTICIPATES_IN]->(ne:NamedEntity)
                        where complementHead.tok_index_doc = f.complementIndex and complementHead.tok_index_doc = ne.headTokenIndex
                        merge (f)-[:REFERS_TO]->(ne)
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""



    # //WE JUST NEED TO CONNECT FA (prepositional) TO NAMED ENTITY. 
    # //CASE:  when FA refereing to an entity but not named entity. usually such situation it refering to nominal. 
    # //CASE: when FA's headword is a prepostion. In this case we gonna see the POBJ headword and match it with Entity.
    # // this query try to find those FAs who do not have any entity instance created during NER or NEL.  
    # // MISSING: fields such as extent, type(set here temporarily). Further, entity disambiguation and deduplication may be required. 
    # // coreferencing information can be employed to deduplicate entities.  
    def link_frameArgument_to_namedEntity_for_pobj_entity(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        MATCH p= (f:FrameArgument where f.type in ['ARG0','ARG1','ARG2','ARG3','ARG4'])-[:PARTICIPATES_IN]-
                        (complementHead:TagOccurrence)
                        where f.complementIndex = complementHead.tok_index_doc and not exists 
                        ((complementHead)-[]-(:NamedEntity {headTokenIndex: complementHead.tok_index_doc}))
                        merge (complementHead)-[:PARTICIPATES_IN]->(e:Entity 
                        {id:f.complementFullText, type:complementHead.pos, syntacticType:complementHead.pos, head:f.complement, 
                        headTokenIndex:f.complementIndex})
                        merge (f)-[:REFERS_TO]->(e)
                        RETURN p    
        
        """
        data= graph.run(query).data()
        
        return ""
    

    # //WE JUST NEED TO CONNECT FA TO NAMED ENTITY. 
    # //CASE: when FA's headword is a pronominal
    # // we designed this query because we need to deal with FAs who have pronominal token. 
    # //we need the path to the named entity via coref-antecedent links
    def link_frameArgument_to_namedEntity_for_pro(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (f:FrameArgument)<-[:PARTICIPATES_IN]-(head:TagOccurrence )-[:PARTICIPATES_IN]->
                        (crf:CorefMention)--(ant:Antecedent)-[:REFERS_TO]->(ne:NamedEntity)
                        where head.tok_index_doc = f.headTokenIndex and head.tok_index_doc = crf.headTokenIndex
                        merge (f)-[:REFERS_TO]->(ne)
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""

    # // this query try to find those FAs who do not have any entity instance created during NER or NEL.  
    # // MISSING: fields such as extent, type(set here temporarily). Further, entity disambiguation and deduplication may be required. 
    # // coreferencing information can be employed to deduplicate entities.
    def link_frameArgument_to_new_entity(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        MATCH p= (f:FrameArgument where f.type in ['ARG0','ARG1','ARG2','ARG3','ARG4'])-[:PARTICIPATES_IN]-(h:TagOccurrence where not  h.pos  in ['IN'])
                        where f.headTokenIndex = h.tok_index_doc 
                        and not exists ((h)-[]-(:NamedEntity {headTokenIndex: h.tok_index_doc}))
                        merge (h)-[:PARTICIPATES_IN]->(e:Entity {id:f.text, type:f.syntacticType, 
                        syntacticType:f.syntacticType, head:f.head, headTokenIndex:f.headTokenIndex})
                        merge (f)-[:REFERS_TO]->(e)
                        RETURN p      
        
        """
        data= graph.run(query).data()
        
        return ""

    # //WE JUST NEED TO CONNECT ANTECEDENT TO NAMED ENTITY.
    def link_antecedent_to_namedEntity(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (f:Antecedent)<-[:PARTICIPATES_IN]-(head:TagOccurrence )-[:PARTICIPATES_IN]->(ne:NamedEntity)
                        where head.tok_index_doc = f.headTokenIndex and head.tok_index_doc = ne.headTokenIndex
                        merge (f)-[:REFERS_TO]->(ne)
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""


    




if __name__ == '__main__':
    tp= RefinementPhase(sys.argv[1:])

    tp.get_and_assign_head_info_to_entity_multitoken()
    tp.get_and_assign_head_info_to_entity_singletoken()
    tp.get_and_assign_head_info_to_antecedent_multitoken()
    tp.get_and_assign_head_info_to_antecedent_singletoken()
    tp.get_and_assign_head_info_to_corefmention_multitoken()
    tp.get_and_assign_head_info_to_corefmention_singletoken()
    tp.get_and_assign_head_info_to_frameArgument_singletoken()
    tp.get_and_assign_head_info_to_frameArgument_multitoken()
    tp.get_and_assign_head_info_to_frameArgument_with_preposition()
    tp.link_frameArgument_to_namedEntity_for_nam_nom()
    tp.link_frameArgument_to_namedEntity_for_pobj()
    tp.link_frameArgument_to_namedEntity_for_pobj_entity()
    tp.link_frameArgument_to_namedEntity_for_pro()
    tp.link_frameArgument_to_new_entity()
    tp.link_antecedent_to_namedEntity()





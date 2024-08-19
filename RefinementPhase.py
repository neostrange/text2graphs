import os
import spacy
import sys
#import neuralcoref
#import coreferee
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
    # here head is noun or pronoun
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


    #To find head info for the FrameArgument i.e., with single token as head
    # here head is noun or pronoun
    def get_and_assign_head_info_to_all_frameArgument_singletoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (a:TagOccurrence where a.pos in ['NNS', 'NN', 'NNP', 'NNPS','PRP', 'PRP$'])--(c:FrameArgument)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(c)) and not exists ((a)-[:IS_DEPENDENT]->()--(c))
                        WITH c, a, p
                        set c.head = a.text, c.headTokenIndex = a.tok_index_doc, c.headPos = a.pos
                        return p
    
        
        """
        data= graph.run(query).data()
        
        return ""



        

    #To find head info for the FrameArgument i.e., with single token as head
    # here head is noun or pronoun
    def get_and_assign_head_info_to_temporal_frameArgument_singletoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        # query = """    
        #                 match p= (a:TagOccurrence where a.pos in ['NNS', 'NN', 'NNP', 'NNPS','PRP', 'PRP$', 'RB'])--
        #                 (c:FrameArgument {type:'ARGM-TMP'})
        #                 where not exists ((a)<-[:IS_DEPENDENT]-()--(c)) and not exists ((a)-[:IS_DEPENDENT]->()--(c))
        #                 WITH c, a, p
        #                 set c.head = a.text, c.headTokenIndex = a.tok_index_doc,
        #                 (case when a.pos in ['NNS', 'NN'] then c END).syntacticType ='NOMINAL' , 
        #                 (case when a.pos in ['NNP', 'NNPS'] then c END).syntacticType ='NAM', 
        #                 (case when a.pos in ['PRP', 'PRP$'] then c END).syntacticType ='PRO',
        #                 (case when a.pos in ['RB'] then c END).syntacticType ='ADV'
        #                 return p    
        
        # """

        query = """    
                        match p= (a:TagOccurrence where a.pos in ['NNS', 'NN', 'NNP', 'NNPS','PRP', 'PRP$', 'RB'])--
                        (c:FrameArgument)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(c)) and not exists ((a)-[:IS_DEPENDENT]->()--(c))
                        WITH c, a, p
                        set c.head = a.text, c.headTokenIndex = a.tok_index_doc,
                        (case when a.pos in ['NNS', 'NN'] then c END).syntacticType ='NOMINAL' , 
                        (case when a.pos in ['NNP', 'NNPS'] then c END).syntacticType ='NAM', 
                        (case when a.pos in ['PRP', 'PRP$'] then c END).syntacticType ='PRO',
                        (case when a.pos in ['RB'] then c END).syntacticType ='ADV'
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""


    #To find head info for the FrameArgument i.e., with multi token as head
    #here the head is noun or pronoun
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



 




    #General rule to get and assign head of all multi-token framearguments
    def get_and_assign_head_info_to_all_frameArgument_multitoken(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))
        
        query = """    
                        match p= (a:TagOccurrence)-[:PARTICIPATES_IN]->(f:FrameArgument), q= (a)-[:IS_DEPENDENT]->()--(f)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                        WITH f, a, p
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, f.headPos = a.pos 
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""

    # // This query first find out those FrameArguments of type ['ARG1', 'ARG0', 'ARG2', 'ARG3', 'ARG4', 'ARGA', 'ARGM-TMP'] and
    # // which have 'preposition' as a headword. 
    # // Then It finds out the complement (pobj) of the preposition and mark it as 
    # // complement. This complement will be used to refer to the entity. 
    # // NOTE: The preoposition word will help in understanding the type of association between frame and
    # // the frameargument with respect to the preposition and complement (noun) entity. 
    #// UPDATE: ARGM-TMP is added in the list of allowable types. 
    def get_and_assign_head_info_to_frameArgument_with_preposition(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (a:TagOccurrence where a.pos in ['IN'])--
                        (f:FrameArgument where f.type in ['ARG1', 'ARG0', 'ARG2', 'ARG3', 'ARG4', 'ARGA', 'ARGM-TMP']), q= (a)-[:IS_DEPENDENT]->()--(f)
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





    #To find head info for the FrameArgument i.e., with multi token as head
    #// It shows when an action took place
    # // case: when headword in an FA is a verb connected with preposition via MARK dep-parse relation.
    # // the text is a clause starts with some temporal preposition such as 
    # // after, before, 
    # #// COMMON OBSERVATIONS: 
    # #// - FA has type ARGM-TMP
    #// - FA has some VERB denoting that its refering to some event
    #// - FA has some signal that we could relate to some type of TLINK  
    def get_and_assign_head_info_to_temporal_frameArgument_multitoken_mark(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))
        
        query = """    
                        match p= (s:TagOccurrence where s.pos = 'IN')<-[:IS_DEPENDENT {type: 'mark'}]
                        -(a:TagOccurrence where a.pos in ['VBD'])-
                        [:PARTICIPATES_IN]->(f:FrameArgument where f.type = 'ARGM-TMP'), q= (a)-[:IS_DEPENDENT]->()--(f)
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                        WITH f, a, p,s
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, f.syntacticType ='EVENTIVE', f.signal = s.text
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""



    #To find head info for the FrameArgument which has type of ARGM-TMP i.e., with multi token as head
    #// It shows when an action took place
    # // case: when headword in an FA is a preposition connected with verb gerund (complement) via pcomp dep-parse relation.
    # // the text is a clause starts with some temporal preposition such as 
    # // after, before,    
    #// COMMON OBSERVATIONS:
    #// - FA has type ARGM-TMP
    #// - FA has some VERB denoting that its refering to some event
    #// - FA has some signal that we could relate to some type of TLINK
    def get_and_assign_head_info_to_temporal_frameArgument_multitoken_pcomp(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))
        
        query = """    
                        match p= (f)--(v:TagOccurrence {pos: 'VBG'})<-[l:IS_DEPENDENT {type: 'pcomp'}]-
                        (a:TagOccurrence where a.pos in ['IN'])-[:PARTICIPATES_IN]->(f:FrameArgument where f.type = 'ARGM-TMP')
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                        WITH f, a, p, v
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, f.syntacticType ='EVENTIVE', f.signal = a.text, f.complement = v.text
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""

#To find head info for the FrameArgument i.e., with multi token as head
    #// It shows when an action took place
    # // case: when headword in an FA is a preposition connected with verb gerund (complement) via pcomp dep-parse relation.  
    #// COMMON OBSERVATIONS:
    #// - FA has some VERB denoting that its refering to some event
    #// - FA has some signal that we could relate to some type of Link
    def get_and_assign_head_info_to_eventive_frameArgument_multitoken_pcomp(self):

            print(self.uri)
            graph = Graph(self.uri, auth=(self.username, self.password))
            
            query = """    
                            match p= (f)--(v:TagOccurrence {pos: 'VBG'})<-[l:IS_DEPENDENT {type: 'pcomp'}]-
                            (a:TagOccurrence where a.pos in ['IN'])-[:PARTICIPATES_IN]->(f:FrameArgument)
                            where not exists ((a)<-[:IS_DEPENDENT]-()--(f))
                            WITH f, a, p, v
                            set f.head = a.text, f.headTokenIndex = a.tok_index_doc, f.syntacticType ='EVENTIVE', f.signal = a.text, f.complement = v.text
                            return p    
            
            """
            data= graph.run(query).data()
            
            return ""

    
    #To find head info for the FrameArgument which has type of ARGM-TMP i.e., with multi token as head
    #// CASE: has root as a verb. But this verb is acting like a preposition as it has POBJ link with an object. 
    #// example can be following in 'following the European Central Bank' 
    #// to see more detail: check pobj in https://downloads.cs.stanford.edu/nlp/software/dependencies_manual.pdf
    #// COMMON OBSERVATIONS: 
    #// - FA has type ARGM-TMP
    #// - FA has some VERB denoting that its refering to some event
    #// - FA has some signal that we could relate to some type of TLINK
    def get_and_assign_head_info_to_temporal_frameArgument_multitoken_pobj(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))
        
        query = """    
                        match p= (f)--(v:TagOccurrence)<-[l:IS_DEPENDENT {type: 'pobj'}]-
                        (a:TagOccurrence where a.pos in ['IN', 'VBG'])-[:PARTICIPATES_IN]->(f:FrameArgument where f.type = 'ARGM-TMP')
                        where not exists ((a)<-[:IS_DEPENDENT]-()--(f)) and a.text in ['following']
                        WITH f, a, p, v
                        set f.head = a.text, f.headTokenIndex = a.tok_index_doc, f.syntacticType ='EVENTIVE', f.signal = a.text, f.complement = v.text
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
                        ((complementHead)-[]-(:NamedEntity {headTokenIndex: complementHead.tok_index_doc})) and not exists
                        ((f)-[:REFERS_TO]-(:NamedEntity))
                        MERGE (e:Entity {id: f.complementFullText})
                        ON CREATE SET e.type = complementHead.pos, e.syntacticType = complementHead.pos, e.head = f.complement, e.headTokenIndex = f.complementIndex
                        MERGE (complementHead)-[:PARTICIPATES_IN]->(e)
                        MERGE (f)-[:REFERS_TO]->(e)
                        RETURN p   
        
        """
        data= graph.run(query).data()
        
        return ""
    

    # //WE JUST NEED TO CONNECT FA TO NAMED ENTITY. 
    # //CASE: when FA's headword is a pronominal i.e., having pos value as PRP or PRP$
    # // we designed this query because we need to deal with FAs who have pronominal token. 
    # //we need the path to the named entity via coref-antecedent links
    def link_frameArgument_to_namedEntity_for_pro(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (f:FrameArgument)<-[:PARTICIPATES_IN]-(head:TagOccurrence )-[:PARTICIPATES_IN]->
                        (crf:CorefMention)--(ant:Antecedent)-[:REFERS_TO]->(ne:NamedEntity)
                        where head.pos in ['PRP','PRP$'] and head.tok_index_doc = f.headTokenIndex and head.tok_index_doc = crf.headTokenIndex
                        merge (f)-[:REFERS_TO]->(ne)
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""

    # // this query try to find those FAs who do not have any entity instance created during NER or NEL.  
    # // TODO: fields such as extent, type(set here temporarily). Further, entity disambiguation and deduplication may be required. 
    # // coreferencing information can be employed to deduplicate entities.
    # // CASES NOT COVERED: 
    # // 1: when FA has text span which has more than one entity. For example, 'millions of people', here we have million as numeric and millions of people as nominal.
    # //    -- perhaps these overlapping spans denoting multiple entities can be handled using SPANCAT. R&D is required 
    # //    -- presently, the pipeline tag 'millions' as CARDINAL and refers_to connection is establish between FA and CARDINAL entity. However this connection is not
    # //    -- correct as the correct entity is 'millions of people' which is NOMINAL.  Though head of FA is 'millions' in this phrase. 
    def link_frameArgument_to_new_entity(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        MATCH p= (f:FrameArgument where f.type in ['ARG0','ARG1','ARG2','ARG3','ARG4'] and f.syntacticType <> 'PRO')
                        -[:PARTICIPATES_IN]-(h:TagOccurrence where not  h.pos  in ['IN'])
                        where f.headTokenIndex = h.tok_index_doc 
                        and not exists ((h)-[]-(:NamedEntity {headTokenIndex: h.tok_index_doc}))
                        merge (e:Entity {id:f.text, type:f.syntacticType, 
                        syntacticType:f.syntacticType, head:f.head})
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

        


    
# //It will add another label to named entities that are qualified as value.
    def tag_numeric_entities(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match (ne:NamedEntity) where ne.type in ['MONEY', 'QUANTITY', 'PERCENT']
                        set ne:NUMERIC   
        
        """
        data= graph.run(query).data()
        
        return ""



    # //It will add another label to named entities that are qualified as value.
    def tag_value_entities(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match (ne:NamedEntity) where ne.type in ['CARDINAL', 'ORDINAL', 'MONEY', 'QUANTITY', 'PERCENT']
                        set ne:VALUE   
        
        """
        data= graph.run(query).data()
        
        return ""


    #// CASE Incorrect Named Entity Disambiguation (Example 1: JIM CRAMER detected as PIETER CRAMER which is wrong)
    #// 
    #// NED processing has not accurately disambiguated an entity. We are using Coref information to detect and correct the incorrect result
    #// ASSUMPTION: that the antecedent is correctly disambiguated and we should rely on it. d
    #// Here we are giving preference to NamedEntity refered by Antecedent node. Replacing the incorrect with the correct one.  
    #// PRECONDITION: KB_ID attributes of both NamedEntities are not null. This query should be run before the Frameargument linking with NamedEntity
    #// cases - 1. kb_id of both namedEntities are not null (DONE in this query)
    #//         2. ne1 doesnt have kb_id and ne2 has kb_id  (e.g., Fed as a spacy entity but actually refering to dbpedia Federal Researve)(DONE in next query v2)
    #//               
    def detect_correct_NEL_result_for_having_kb_id(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (e1:Entity)<-[:REFERS_TO]-(ne1:NamedEntity)<-[:PARTICIPATES_IN]-(t1:TagOccurrence)-[:PARTICIPATES_IN]->(coref:CorefMention)-[:COREF]->(ant:Antecedent)-[:REFERS_TO]->(ne2:NamedEntity)-[:REFERS_TO]->(e2:Entity)
                        where t1.text = ne1.head and t1.text = coref.head and ne1.kb_id is not null and ne2.kb_id is not null and ne1.kb_id <> ne2.kb_id
                        set ne1.kb_id = ne2.kb_id, ne1.description = ne2.description, ne1.normal_term = ne2.normal_term, ne1.url_wikidata = ne2.url_wikidata,ne1.type = ne2.type
                        detach delete e1
                        merge (ne1)-[:REFERS_TO]->(e2)
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""




    #// detecting and correcting named entities result. 
    #// Using the coreferencing information, and assuming antecedent refering to correct entity.
    #// CONDITION: if entity of token from any of the corefmention is not equal to entity refered by antecedent.
    #// CONDITION: ne1 doesnt have kb_id and ne2 has kb_id  (e.g., Fed as a spacy entity but actually refering to dbpedia Federal Researve)              
    def detect_correct_NEL_result_for_missing_kb_id(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p= (e1:Entity)<-[:REFERS_TO]-(ne1:NamedEntity)<-[:PARTICIPATES_IN]-(t1:TagOccurrence)-[:PARTICIPATES_IN]->(coref:CorefMention)-[:COREF]->(ant:Antecedent)-[:REFERS_TO]->(ne2:NamedEntity)-[:REFERS_TO]->(e2:Entity)
                        where t1.text = ne1.head and t1.text = coref.head and ne1.kb_id is null and ne2.kb_id is not null
                        set ne1.kb_id = ne2.kb_id, ne1.spacyType = ne1.type, ne1.type = ne2.type, ne1.description = ne2.description, ne1.normal_term = ne2.normal_term, ne1.url_wikidata = ne2.url_wikidata
                        detach delete e1
                        merge (ne1)-[:REFERS_TO]->(e2)
                        return p    
        
        """
        data= graph.run(query).data()
        
        return ""
         



    # // This method detects the presence of quantified entities and create a new instance of it. 
    # // It will first see whether the head token in frameArgument denotes a NUMERIC value (as a namedEntity) or some quantified signal such as all, some, many etc
    # // and it is satisfying the following noun phrase composition:
    # // (head {any quantifier}) --- (preposition {text:'of'}) --- (noun) e.g., millions of people, some of the players etc.
    # // it deletes the existing REFERS_TO relationship between frameArgument and (numeric)NamedEntity. creates a new Entity and link frameArgument with that entity. 
    # // PRECONDITIONS: should be executed after NER, NEL, head-identification, linking FA to namedEntities, entities.    
    # // TODO: currently it only assign a type as NOMINAL to newly created entity. But it needs to be improved to detect PARTITIVE constructions. 
    # // also it should be able to differentiate between partitive and nominal instances. for more detail see page 20 of 
    # // 'NEWSREADER GUIDELINES FOR ANNOTATION AT DOCUMENT LEVEL' NWR-2014-2-2
    def detect_quantified_entities_from_frameArgument(self):

        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                            match p = (pobj:TagOccurrence where pobj.pos in ['NNS','NNP','NN', 'NNPS','PRP', 'PRP$'])<-[dep2:IS_DEPENDENT {type: 'pobj'}]
                            -(prep:TagOccurrence where prep.text= 'of')<-[dep1:IS_DEPENDENT {type: 'prep'}]-(head:TagOccurrence {tok_index_doc : fa.headTokenIndex})-
                            [:PARTICIPATES_IN]->(fa:FrameArgument), (pobj)--(fa)
                            where exists ((head)-[:PARTICIPATES_IN]->(:NamedEntity {type: 'CARDINAL'})) OR head.lemma in ['all', 'some', 'many', 'group']
                            merge (fa)-[:REFERS_TO]->(e:Entity {id: fa.text, type: 'NOMINAL'})
                            with fa,p
                            match (fa)-[r:REFERS_TO]->(ne:NamedEntity)
                            delete r
                            return p    
        
        """
        data= graph.run(query).data()
        
        return ""


    # Link FA to Entity by using their links with NamedEntities. path = FA --> NE --> E  implies FA --> E
    def link_frameArgument_to_entity_via_named_entity(self):
 
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        match p = (fa:FrameArgument)-[:REFERS_TO]->(ne:NamedEntity)-[:REFERS_TO]-(e:Entity)
                        merge (fa)-[:REFERS_TO]-(e)
                        return p     
        
        """
        data= graph.run(query).data()
        
        return ""


    #//It connects frame argument to numeric entities.
    #//PRECONDITION: query 'detect_quantified_entities_from_frameArgument' in refinment phase must be run before this. 
    #//Because, cases like 'millions of people' actually refering to nominal rather numeric
    #//It checks that frame argument is not yet connected to entity. If it exists it means it is a case about quantified entities. 
    def link_frameArgument_to_numeric_entities(self):
        print(self.uri)
        graph = Graph(self.uri, auth=(self.username, self.password))

        query = """    
                        MATCH p = (f:FrameArgument)<-[:PARTICIPATES_IN]-(t:TagOccurrence)-[:PARTICIPATES_IN]->(e:NUMERIC)
                        where f.headTokenIndex = t.tok_index_doc and not exists ((f)-[:REFERS_TO]-(:Entity))
                        merge (f)-[:REFERS_TO]-(e)
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

    # NOTE: it assigns the grammatical head to all the framearguments without any condition or filter 
    tp.get_and_assign_head_info_to_all_frameArgument_singletoken()
    tp.get_and_assign_head_info_to_all_frameArgument_multitoken()
    # -----------------------------------------------------------------------------------------------
    
    tp.get_and_assign_head_info_to_frameArgument_singletoken()
    tp.get_and_assign_head_info_to_frameArgument_multitoken()
    tp.get_and_assign_head_info_to_frameArgument_with_preposition()
    tp.get_and_assign_head_info_to_temporal_frameArgument_singletoken()
    tp.get_and_assign_head_info_to_temporal_frameArgument_multitoken_mark()
    tp.get_and_assign_head_info_to_temporal_frameArgument_multitoken_pcomp()
    tp.get_and_assign_head_info_to_temporal_frameArgument_multitoken_pobj()
    tp.get_and_assign_head_info_to_eventive_frameArgument_multitoken_pcomp()
    


    tp.link_antecedent_to_namedEntity()
    #tp.detect_correct_NEL_result_for_having_kb_id()
    tp.detect_correct_NEL_result_for_missing_kb_id()

    tp.link_frameArgument_to_namedEntity_for_nam_nom()
    tp.link_frameArgument_to_namedEntity_for_pobj()
    tp.link_frameArgument_to_namedEntity_for_pobj_entity()
    tp.link_frameArgument_to_namedEntity_for_pro()
    
    tp.link_frameArgument_to_new_entity()
    
    tp.tag_value_entities()
    tp.tag_numeric_entities()
    tp.detect_quantified_entities_from_frameArgument()
    tp.link_frameArgument_to_numeric_entities()
    tp.link_frameArgument_to_entity_via_named_entity()






# custom labels for non-core arguments and storing it as a node attribute: argumentType. The second step the value in the fa.argumentType 
# will be set as a label for this node. It will perform event enrichment fucntion as well as attaching propbank modifiers arguments 
# with the event node. 
# TODO: Though we have found fa nodes with duplicates content with same label or arg type but we will deal with it later. 
# 
# 
# MATCH (event:TEvent)<-[:DESCRIBES]-(f:Frame)<-[:PARTICIPANT]-(fa:FrameArgument)
# WHERE not fa.type IN ['ARG0', 'ARG1', 'ARG2', 'ARG3', 'ARG4', 'ARGM-TMP']
# WITH event, f, fa
# SET fa.argumentType=
#     CASE fa.type
#     WHEN 'ARGM-MNR' THEN 'Manner'
#     WHEN 'ARGM-ADV' THEN 'Adverbial'
#     WHEN 'ARGM-DIR' THEN 'Direction'
#     WHEN 'ARGM-DIS' THEN 'Discourse'
#     WHEN 'ARGM-LOC' THEN 'Location'
#     WHEN 'ARGM-PRP' THEN 'Purpose'
#     WHEN 'ARGM-CAU' THEN 'Cause'
#     WHEN 'ARGM-EXT' THEN 'Extent'
#     ELSE 'NonCore'
#     END
# MERGE (fa)-[r:PARTICIPANT]->(event)
# SET r.type = fa.type,
#     (CASE WHEN fa.syntacticType IN ['IN'] THEN r END).prep = fa.head 
# RETURN event, f, fa, r




#VERSION 2 of the previous query with additional propbank arguments
# MATCH (event:TEvent)<-[:DESCRIBES]-(f:Frame)<-[:PARTICIPANT]-(fa:FrameArgument)
# WHERE NOT fa.type IN ['ARG0', 'ARG1', 'ARG2', 'ARG3', 'ARG4', 'ARGM-TMP']
# WITH event, f, fa
# SET fa.argumentType =
#     CASE fa.type
#     WHEN 'ARGM-COM' THEN 'Comitative'
#     WHEN 'ARGM-LOC' THEN 'Locative'
#     WHEN 'ARGM-DIR' THEN 'Directional'
#     WHEN 'ARGM-GOL' THEN 'Goal'
#     WHEN 'ARGM-MNR' THEN 'Manner'
#     WHEN 'ARGM-TMP' THEN 'Temporal'
#     WHEN 'ARGM-EXT' THEN 'Extent'
#     WHEN 'ARGM-REC' THEN 'Reciprocals'
#     WHEN 'ARGM-PRD' THEN 'SecondaryPredication'
#     WHEN 'ARGM-PRP' THEN 'PurposeClauses'
#     WHEN 'ARGM-CAU' THEN 'CauseClauses'
#     WHEN 'ARGM-DIS' THEN 'Discourse'
#     WHEN 'ARGM-MOD' THEN 'Modals'
#     WHEN 'ARGM-NEG' THEN 'Negation'
#     WHEN 'ARGM-DSP' THEN 'DirectSpeech'
#     WHEN 'ARGM-ADV' THEN 'Adverbials'
#     WHEN 'ARGM-ADJ' THEN 'Adjectival'
#     WHEN 'ARGM-LVB' THEN 'LightVerb'
#     WHEN 'ARGM-CXN' THEN 'Construction'
#     ELSE 'NonCore'
#     END
# MERGE (fa)-[r:PARTICIPANT]->(event)
# SET r.type = fa.type,
#     (CASE WHEN fa.syntacticType IN ['IN'] THEN r END).prep = fa.head 
# RETURN event, f, fa, r


# 2nd step where we set the labels for the non-core fa arguments
# MATCH (fa:FrameArgument)
# WHERE fa.argumentType is not NULL
# CALL apoc.create.addLabels(id(fa), [fa.argumentType]) YIELD node
# RETURN node



##
#


#
##










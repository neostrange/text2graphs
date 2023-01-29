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







class GraphBasedNLP(GraphDBBase):

    def __init__(self, argv):
        super().__init__(command=__file__, argv=argv)
        spacy.prefer_gpu()

        self.nlp = spacy.load('en_core_web_trf')
        #coref = neuralcoref.NeuralCoref(self.nlp.vocab)
        #self.nlp.add_pipe(coref, name='neuralcoref')
        #self.nlp.add_pipe('opentapioca')
        #self.nlp.add_pipe("entityfishing", config= {"api_ef_base": "http://localhost:8090/service", "extra_info": True})
        # add the pipeline stage
        self.nlp.add_pipe('dbpedia_spotlight', config={'confidence': 0.5, 'overwrite_ents': True})
        
        #self.nlp.add_pipe('coreferee')
        #self.nlp.add_pipe("xx_coref", config={"chunk_size": 2500, "chunk_overlap": 2, "device": 0})

        if "srl" in self.nlp.pipe_names:
            self.nlp.remove_pipe("srl")
            _ = self.nlp.add_pipe("srl")

        self.nlp.add_pipe("srl")


        print(self.nlp.pipe_names)

        self.__text_processor = TextProcessor(self.nlp, self._driver)
        self.create_constraints()

    def create_constraints(self):
        self.execute_without_exception("CREATE CONSTRAINT ON (u:Tag) ASSERT (u.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (i:TagOccurrence) ASSERT (i.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (t:Sentence) ASSERT (t.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (l:AnnotatedText) ASSERT (l.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (l:NamedEntity) ASSERT (l.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (l:Entity) ASSERT (l.type, l.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (l:Evidence) ASSERT (l.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (l:Relationship) ASSERT (l.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (l:NounChunk) ASSERT (l.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (l:TEvent) ASSERT (l.eiid, l.doc_id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT ON (l:TIMEX) ASSERT (l.tid, l.doc_id) IS NODE KEY")
        #self.execute_without_exception("CREATE CONSTRAINT ON (l:CorefMention) ASSERT (l.id) IS NODE KEY")

        

    # filenames are retrieved from the wsl2 ubuntu instance but neo4j accesses these files from its import directory
    # keeping copies of files at both sides is temporaray solution, later we can keep files and neo4j instance at same location
    def store_corpus(self, directory):
        text_id = 1
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            # checking if it is a file
            if os.path.isfile(f):
                print(filename)

                tree = ET.parse('/home/neo/environments/text2graphs/text2graphs/dataset/'+filename)
                root = tree.getroot()
                text = root[1].text
                #text = text.replace('\n\n','. ')
                text = text.replace('\n','')
                #storing the corpus files as nodes in neo4j with meta-data
                self.__text_processor.create_annotated_text(filename, text, text_id)
                text_id+=1
        
        text_tuples = tuple(self.__text_processor.get_annotated_text())
        #text_tuples = self.__text_processor.get_annotated_text()
        return text_tuples



    def tokenize_and_store(self, text_tuples, text_id, storeTag):

        if not Doc.has_extension("text_id"):
            Doc.set_extension("text_id", default=None)

        doc_tuples = self.nlp.pipe(text_tuples, as_tuples=True)

        docs=[]

        for doc, context in doc_tuples:
            doc._.text_id = context["text_id"]
            docs.append(doc)



        for doc in docs:
            #annotated_text = self.__text_processor.create_annotated_text(doc, text_id)
            text_id = doc._.text_id

            # here doc[0] refers to the text context of doc
            spans = self.__text_processor.process_sentences(doc._.text_id, doc, storeTag, text_id)
            noun_chunks = self.__text_processor.process_noun_chunks(doc, text_id),
            nes = self.__text_processor.process_entities(spans, text_id)
            deduplicate = self.__text_processor.deduplicate_named_entities(text_id)
            #coref = self.__text_processor.process_coreference(doc, text_id)
            #coref = self.__text_processor.process_coreference_allennlp(doc, text_id)
            coref = self.__text_processor.do_coref2(doc, text_id)
            # HERE I NEED THE HEAD IDENTIFICATION FOR NAMED ENTITIES, COREF, ANTECEDENT, FRAMEARGUMENT
            # 1. FOR SINGLE TOKEN, 2. FOR MULTI-TOKEN, 
            self.__text_processor.build_entities_inferred_graph(text_id)
            self.__text_processor.apply_pipeline_1(doc)
            rules = [
                {
                    'type': 'RECEIVE_PRIZE',
                    'verbs': ['receive'],
                    'subjectTypes': ['PERSON', 'NP'],
                    'objectTypes': ['WORK_OF_ART']
                }
            ]
            self.__text_processor.extract_relationships(text_id, rules)
            self.__text_processor.build_relationships_inferred_graph(text_id)


if __name__ == '__main__':
    basic_nlp = GraphBasedNLP(sys.argv[1:])

    #directory = r'C:\Users\neo strange\.Neo4jDesktop\relate-data\dbmss\dbms-526a9b9e-9d99-4d7f-8a1b-47e71323376f\import'
    
    directory = r'/../home/neo/environments/text2graphs/text2graphs/dataset'
   
    
    # stores the file as a node in neo4j
    text_tuples = basic_nlp.store_corpus(directory)

    basic_nlp.tokenize_and_store(text_tuples=text_tuples, text_id= 1, storeTag= False)
    

    basic_nlp.close()

    # basic_nlp.tokenize_and_store(
    #     """Apple Computer today introduced the new MacBook line, which includes the Macbook and Macbook Pro. It is the successor to the iBook line and contains Intel Core Duo processors and a host of features, and starting at a price of $1,099. The Macbook features a 13.3" widescreen display, while the Pro can be purchased with either 15" or 17" displays. It comes in two colors: Black (2 GHz model only) and White (1.83 and 2 GHz models). This release leaves only one PowerPC processor computer that has not made the transition to Intel chips, the PowerMac G5.""",
    #     3,
    #     False)


    #basic_nlp.tokenize_and_store(directory, 3,
     #   False)

    #basic_nlp.close()

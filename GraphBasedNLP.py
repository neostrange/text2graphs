import os
import spacy
import sys
from util.SemanticRoleLabeler import SemanticRoleLabel
from util.EntityFishingLinker import EntityFishing
from spacy.tokens import Doc, Token, Span
from util.RestCaller import callAllenNlpApi
import TextProcessor
from util.GraphDbBase import GraphDBBase
from TextProcessor import TextProcessor
import xml.etree.ElementTree as ET
from spacy.lang.char_classes import ALPHA, ALPHA_LOWER, ALPHA_UPPER
from spacy.lang.char_classes import CONCAT_QUOTES, LIST_ELLIPSES, LIST_ICONS
from spacy.util import compile_infix_regex



class GraphBasedNLP(GraphDBBase):



    def __init__(self, argv):
        super().__init__(command=__file__, argv=argv)
        spacy.prefer_gpu()

        self.nlp = spacy.load('en_core_web_trf')

        #-----------------------alter tokenization behavior for hyphens when used as infix------------

        # Modify tokenizer infix patterns
        infixes = (
            LIST_ELLIPSES 
            + LIST_ICONS
            + [
                r"(?<=[0-9])[+\\-\\*^](?=[0-9-])",
                r"(?<=[{al}{q}])\\.(?=[{au}{q}])".format(
                    al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES
                ),
                r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
                # ✅ Commented out regex that splits on hyphens between letters:
                # r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
                r"(?<=[{a}0-9])[:<>=/](?=[{a}])".format(a=ALPHA),
            ]
        )

        infix_re = compile_infix_regex(infixes)
        self.nlp.tokenizer.infix_finditer = infix_re.finditer
        self.nlp.add_pipe('dbpedia_spotlight', config={'confidence': 0.5, 'overwrite_ents': True})
        

        if "srl" in self.nlp.pipe_names:
            self.nlp.remove_pipe("srl")
            _ = self.nlp.add_pipe("srl")

        self.nlp.add_pipe("srl")

        self.__text_processor = TextProcessor(self.nlp, self._driver)
        self.create_constraints()

    def create_constraints(self):
        self.execute_without_exception("CREATE CONSTRAINT for (u:Tag) require u.id IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (i:TagOccurrence) require i.id IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (t:Sentence) require t.id IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (l:AnnotatedText) require l.id IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (l:NamedEntity) require l.id IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (l:Entity) require (l.type, l.id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (l:Evidence) require l.id IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (l:Relationship) require l.id IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (l:NounChunk) require l.id IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (l:TEvent) require (l.eiid, l.doc_id) IS NODE KEY")
        self.execute_without_exception("CREATE CONSTRAINT for (l:TIMEX) require (l.tid, l.doc_id) IS NODE KEY")
        #self.execute_without_exception("CREATE CONSTRAINT ON (l:CorefMention) ASSERT (l.id) IS NODE KEY")

        

    # filenames are retrieved from the wsl2 ubuntu instance but neo4j accesses these files from its import directory
    # keeping copies of files at both sides is temporaray solution, later we can keep files and neo4j instance at same location
    def store_corpus2(self, directory):
        text_id = 1
        path= '/home/neo/environments/text2graphs/text2graphs/data/dataset/'
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            # checking if it is a file
            if os.path.isfile(f):
                print(filename)
                tree = ET.parse('/home/neo/environments/text2graphs/text2graphs/data/dataset/'+filename)
                root = tree.getroot()
                text = root[1].text
                #text = text.replace('\n\n','. ')
                text = text.replace('\n','')
                # getting the text of the file as string
                text_file = open(path+filename, 'r')
                data = text_file.read()
                text_file.close()
                #storing the corpus files as nodes in neo4j with meta-data
                #self.__text_processor.create_annotated_text(filename, text, text_id)
                self.__text_processor.create_annotated_text(data, text, text_id)
                text_id+=1
        
        text_tuples = tuple(self.__text_processor.get_annotated_text())
        #text_tuples = self.__text_processor.get_annotated_text()
        return text_tuples
    


    def store_corpus(self, directory):
        text_id = 1
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            if os.path.isfile(f):
                print(filename)
                tree = ET.parse(f)
                root = tree.getroot()
                text = root[1].text
                text = text.replace('\n', '')
                with open(f, 'r') as text_file:
                    data = text_file.read()
                self.__text_processor.create_annotated_text(data, text, text_id)
                text_id += 1
        
        text_tuples = tuple(self.__text_processor.get_annotated_text())
        return text_tuples

    def tokenize_and_store(self, text_tuples, text_id, storeTag):
        """
        Tokenize and store text data with additional processing steps
        """
        # Ensure the "text_id" extension is registered
        if not Doc.has_extension("text_id"):
            Doc.set_extension("text_id", default=None)

        # Process text tuples using the NLP pipeline
        doc_tuples = self.nlp.pipe(text_tuples, as_tuples=True)

        # Create a list to store the processed documents
        docs = []

        # Iterate over the document tuples
        for doc, context in doc_tuples:
            # Set the text ID for the document
            doc._.text_id = context["text_id"]
            docs.append(doc)

        # Define a list to store the rules for later use
        rules = [
            {
                'type': 'RECEIVE_PRIZE',
                'verbs': ['receive'],
                'subjectTypes': ['PERSON', 'NP'],
                'objectTypes': ['WORK_OF_ART']
            }
        ]

        # Iterate over the processed documents
        for doc in docs:
            text_id = doc._.text_id

            # Perform various processing steps
            spans = self.__text_processor.process_sentences(text_id, doc, storeTag, text_id)
            wsd = self.__text_processor.perform_wsd(text_id)
            wn = self.__text_processor.assign_synset_info_to_tokens(text_id)
            noun_chunks = self.__text_processor.process_noun_chunks(doc, text_id)
            nes = self.__text_processor.process_entities(spans, text_id)
            deduplicate = self.__text_processor.deduplicate_named_entities(text_id)
            coref = self.__text_processor.do_coref2(doc, text_id)
            self.__text_processor.build_entities_inferred_graph(text_id)
            self.__text_processor.apply_pipeline_1(doc)

# if __name__ == '__main__':
#     basic_nlp = GraphBasedNLP(sys.argv[1:])
    
#     directory = r'/../home/neo/environments/text2graphs/text2graphs/data/dataset'
    
#     # stores the file as a node in neo4j
#     text_tuples = basic_nlp.store_corpus(directory)

#     basic_nlp.tokenize_and_store(text_tuples=text_tuples, text_id= 1, storeTag= False)
    
#     basic_nlp.close()


if __name__ == '__main__':
    # Check if the correct number of arguments are provided
    if len(sys.argv) < 2:
        directory = os.path.join(os.path.dirname(__file__), 'data', 'dataset')
        print(f"Using default directory: {directory}")
    else:
        directory = os.path.join(os.path.dirname(__file__), sys.argv[1])

    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist")
        sys.exit(1)

    basic_nlp = GraphBasedNLP(sys.argv[1:])

    # stores the file as a node in neo4j
    text_tuples = basic_nlp.store_corpus(directory)

    # Consider using a more descriptive variable name instead of `text_id`
    basic_nlp.tokenize_and_store(text_tuples=text_tuples, text_id=1, storeTag=False)

    basic_nlp.close()



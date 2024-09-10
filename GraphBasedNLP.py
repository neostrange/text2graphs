import os
import spacy
# from spacy.language import Language
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
from spacy.lang.char_classes import ALPHA, ALPHA_LOWER, ALPHA_UPPER
from spacy.lang.char_classes import CONCAT_QUOTES, LIST_ELLIPSES, LIST_ICONS
from spacy.util import compile_infix_regex







class GraphBasedNLP(GraphDBBase):

    """ @Language.component("segm")
    def set_custom_segmentation(doc):
        for token in doc[:-1]:
            if token.text == '#':
                doc[token.i+1].is_sent_start = True
                
            # else:
            #     doc[token.i+1].is_sent_start = False
        return doc """

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
        #---------------------------------------------------------------------------------------------

        #----------------------------------------stock market related patterns----------------------------------
        #ruler = self.nlp.add_pipe("entity_ruler", after='ner')
        patterns = [
        {"label": "FinancialActivity", "pattern": "stock trading"},
        {"label": "FinancialActivity", "pattern": "investment"},
        {"label": "FinancialActivity", "pattern": "portfolio management"},
        {"label": "FinancialActivity", "pattern": "asset allocation"},
        {"label": "FinancialActivity", "pattern": "capital allocation"},
        {"label": "FinancialActivity", "pattern": "trading strategy"},
        {"label": "FinancialActivity", "pattern": "equity investment"},
        {"label": "FinancialActivity", "pattern": "bonds"},
        {"label": "FinancialActivity", "pattern": "derivatives trading"},
        {"label": "FinancialActivity", "pattern": "forex trading"},
        {"label": "FinancialActivity", "pattern": "asset management"},
        {"label": "FinancialActivity", "pattern": "share trading"},
        {"label": "FinancialActivity", "pattern": "investment strategy"},
        {"label": "FinancialActivity", "pattern": "wealth management"},
        {"label": "FinancialActivity", "pattern": "commodities trading"},
        {"label": "FinancialActivity", "pattern": "futures contracts"},
        {"label": "FinancialActivity", "pattern": "securities trading"},
        {"label": "FinancialActivity", "pattern": "algorithmic trading"},
        {"label": "FinancialActivity", "pattern": "high-frequency trading"},
        {"label": "FinancialActivity", "pattern": "options trading"},
        {"label": "FinancialActivity", "pattern": "risk management"},
        {"label": "FinancialIndicator", "pattern": "stock price"},
        {"label": "FinancialIndicator", "pattern": "market index"},
        {"label": "FinancialIndicator", "pattern": "interest rate"},
        {"label": "FinancialIndicator", "pattern": "dividend yield"},
        {"label": "FinancialIndicator", "pattern": "bond yield"},
        {"label": "FinancialIndicator", "pattern": "volatility index"},
        {"label": "FinancialIndicator", "pattern": "price-to-earnings ratio"},
        {"label": "FinancialIndicator", "pattern": "consumer price index"},
        {"label": "FinancialIndicator", "pattern": "gross domestic product (gdp)"},
        {"label": "FinancialIndicator", "pattern": "unemployment rate"},
        {"label": "FinancialIndicator", "pattern": "stock market index"},
        {"label": "FinancialIndicator", "pattern": "bond rating"},
        {"label": "FinancialIndicator", "pattern": "inflation rate"},
        {"label": "FinancialIndicator", "pattern": "exchange rate"},
        {"label": "FinancialIndicator", "pattern": "treasury yield"},
        {"label": "FinancialIndicator", "pattern": "credit spread"},
        {"label": "FinancialIndicator", "pattern": "mortgage rate"},
        {"label": "FinancialIndicator", "pattern": "yield curve"},
        {"label": "FinancialIndicator", "pattern": "commodity price index"},
        {"label": "FinancialIndicator", "pattern": "leading economic index"},
        {"label": "FinancialIndicator", "pattern": "retail sales index"},
        {"label": "EconomicActivity", "pattern": "trade relations"},
        {"label": "EconomicActivity", "pattern": "gdp growth"},
        {"label": "EconomicActivity", "pattern": "consumer spending"},
        {"label": "EconomicActivity", "pattern": "industrial production"},
        {"label": "EconomicActivity", "pattern": "business investment"},
        {"label": "EconomicActivity", "pattern": "foreign direct investment"},
        {"label": "EconomicActivity", "pattern": "trade deficit"},
        {"label": "EconomicActivity", "pattern": "trade surplus"},
        {"label": "EconomicActivity", "pattern": "economic development"},
        {"label": "EconomicActivity", "pattern": "employment rate"},
        {"label": "EconomicActivity", "pattern": "housing starts"},
        {"label": "EconomicActivity", "pattern": "business sentiment"},
        {"label": "EconomicActivity", "pattern": "consumer confidence"},
        {"label": "EconomicActivity", "pattern": "retail sales"},
        {"label": "EconomicActivity", "pattern": "business investment"},
        {"label": "EconomicActivity", "pattern": "factory orders"},
        {"label": "EconomicActivity", "pattern": "trade balance"},
        {"label": "EconomicActivity", "pattern": "export-import volume"},
        {"label": "EconomicActivity", "pattern": "manufacturing pmi"},
        {"label": "EconomicPolicy", "pattern": "monetary policy"},
        {"label": "EconomicPolicy", "pattern": "fiscal policy"},
        {"label": "EconomicPolicy", "pattern": "interest rate policy"},
        {"label": "EconomicPolicy", "pattern": "tax policy"},
        {"label": "EconomicPolicy", "pattern": "budgetary policy"},
        {"label": "EconomicPolicy", "pattern": "regulatory policy"},
        {"label": "EconomicPolicy", "pattern": "economic stimulus"},
        {"label": "EconomicPolicy", "pattern": "inflation targeting"},
        {"label": "EconomicPolicy", "pattern": "interest rate decision"},
        {"label": "EconomicPolicy", "pattern": "quantitative easing"},
        {"label": "EconomicPolicy", "pattern": "fiscal stimulus"},
        {"label": "EconomicPolicy", "pattern": "central bank intervention"},
        {"label": "EconomicPolicy", "pattern": "austerity measures"},
        {"label": "EconomicPolicy", "pattern": "tax reform"},
        {"label": "EconomicPolicy", "pattern": "tariff policy"},
        {"label": "EconomicPolicy", "pattern": "trade agreement"},
        {"label": "EconomicPolicy", "pattern": "regulatory reform"},
        {"label": "EconomicPolicy", "pattern": "budget deficit reduction"},
        {"label": "EconomicSituation", "pattern": "recession"},
        {"label": "EconomicSituation", "pattern": "inflation"},
        {"label": "EconomicSituation", "pattern": "deflation"},
        {"label": "EconomicSituation", "pattern": "market volatility"},
        {"label": "EconomicSituation", "pattern": "economic downturn"},
        {"label": "EconomicSituation", "pattern": "economic recovery"},
        {"label": "EconomicSituation", "pattern": "stagflation"},
        {"label": "EconomicSituation", "pattern": "hyperinflation"},
        {"label": "EconomicSituation", "pattern": "economic stability"},
        {"label": "EconomicSituation", "pattern": "economic indicators"},
        {"label": "EconomicSituation", "pattern": "economic recession"},
        {"label": "EconomicSituation", "pattern": "economic recovery"},
        {"label": "EconomicSituation", "pattern": "economic slowdown"},
        {"label": "EconomicSituation", "pattern": "boom-bust cycle"},
        {"label": "EconomicSituation", "pattern": "deflationary pressures"},
        {"label": "EconomicSituation", "pattern": "economic expansion"},
        {"label": "EconomicSituation", "pattern": "economic stagnation"},
        {"label": "EconomicSituation", "pattern": "economic resilience"},
        {"label": "EconomicSituation", "pattern": "fiscal imbalance"},
        {"label": "EconomicSituation", "pattern": "debt crisis"},
        {"label": "EconomicEntity", "pattern": "financial institution"},
        {"label": "EconomicEntity", "pattern": "multinational corporation"},
        {"label": "EconomicEntity", "pattern": "investment bank"},
        {"label": "EconomicEntity", "pattern": "commercial bank"},
        {"label": "EconomicEntity", "pattern": "hedge fund"},
        {"label": "EconomicEntity", "pattern": "sovereign wealth fund"},
        {"label": "EconomicEntity", "pattern": "credit rating agency"},
        {"label": "EconomicEntity", "pattern": "central bank"},
        {"label": "EconomicEntity", "pattern": "pension fund"},
        {"label": "EconomicEntity", "pattern": "investment firm"},
        {"label": "EconomicEntity", "pattern": "venture capitalist"},
        {"label": "EconomicEntity", "pattern": "angel investor"},
        {"label": "EconomicEntity", "pattern": "mutual fund"},
        {"label": "EconomicEntity", "pattern": "credit union"},
        {"label": "EconomicEntity", "pattern": "brokerage firm"},
        {"label": "EconomicEntity", "pattern": "insurance company"},
        {"label": "EconomicEntity", "pattern": "financial regulator"},
        {"label": "EconomicEntity", "pattern": "sovereign debt holder"},
        {"label": "EconomicEntity", "pattern": "corporate bondholder"},
        {"label": "EconomicEntity", "pattern": "institutional investor"},
        {"label": "GeographicRegion", "pattern": "developed economies"},
        {"label": "GeographicRegion", "pattern": "emerging markets"},
        {"label": "GeographicRegion", "pattern": "developed countries"},
        {"label": "GeographicRegion", "pattern": "developing nations"},
        {"label": "GeographicRegion", "pattern": "global regions (north america, asia-pacific, europe, etc.)"},
        {"label": "GeographicRegion", "pattern": "economic zones"},
        {"label": "GeographicRegion", "pattern": "free trade zones"},
        {"label": "GeographicRegion", "pattern": "emerging markets"},
        {"label": "GeographicRegion", "pattern": "developing economies"},
        {"label": "GeographicRegion", "pattern": "global economies"},
        {"label": "GeographicRegion", "pattern": "regional blocs (eu, asean, nafta)"},
        {"label": "GeographicRegion", "pattern": "economic zones"},
        {"label": "GeographicRegion", "pattern": "special economic zones"},
        {"label": "GeographicRegion", "pattern": "economic corridors"},
        {"label": "GeographicRegion", "pattern": "economic blocs"},
        {"label": "GeographicRegion", "pattern": "economic alliances"},
        {"label": "GeographicRegion", "pattern": [{"LOWER": "global"}, {"LOWER": "stock"}, {"LOWER": "markets"}]},
        {"label": "EconomicSituation", "pattern": [{"LOWER": "sub-prime"}, {"LOWER": "mortgage"}, {"LOWER": "crisis"}]},
        {"label": "FinancialIndicator", "pattern": [{"LOWER": "dow"}, {"LOWER": "jones"}, {"LOWER": "industrial"}, {"LOWER": "average"}]},
        {"label": "GeographicRegion", "pattern": [{"LOWER": "uk"}]},
        {"label": "FinancialIndicator", "pattern": [{"LOWER": "ftse-100"}, {"LOWER": "index"}]},
        {"label": "GeographicRegion", "pattern": [{"LOWER": "japan"}]},
        {"label": "FinancialIndicator", "pattern": [{"LOWER": "nikkei"}, {"LOWER": "225"}]},
    ]

        #ruler.add_patterns(patterns)

        #---------------------------------------stock market patterns--------------------------------------------

        #coref = neuralcoref.NeuralCoref(self.nlp.vocab)
        #self.nlp.add_pipe(coref, name='neuralcoref')
        #self.nlp.add_pipe('opentapioca')
        #self.nlp.add_pipe("entityfishing", config= {"api_ef_base": "http://localhost:8090/service", "extra_info": True, "dbpedia_rest_endpoint": "http://localhost:2222/rest"})
        # add the pipeline stage
        # self.nlp.add_pipe('segm', before='parser')
        self.nlp.add_pipe('dbpedia_spotlight', config={'confidence': 0.5, 'overwrite_ents': True, 'dbpedia_rest_endpoint': 'http://localhost:2222/rest'})
        
        #self.nlp.add_pipe('coreferee')
        #self.nlp.add_pipe("xx_coref", config={"chunk_size": 2500, "chunk_overlap": 2, "device": 0})

        if "srl" in self.nlp.pipe_names:
            self.nlp.remove_pipe("srl")
            _ = self.nlp.add_pipe("srl")

        self.nlp.add_pipe("srl")


        #print(self.nlp.pipe_names)

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
    def store_corpus(self, directory):
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
            wsd = self.__text_processor.perform_wsd(doc._.text_id)
            wn = self.__text_processor.assign_synset_info_to_tokens(doc._.text_id)
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
    
    directory = r'/../home/neo/environments/text2graphs/text2graphs/data/dataset'
   
    
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

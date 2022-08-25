from cgitb import text
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import json
from tokenize import String
#from allennlp.predictors.predictor import Predictor
#from allennlp_models import pretrained
#import allennlp_models.tagging
from spacy import Language
import GPUtil
import spacy
from spacy.matcher import Matcher, DependencyMatcher
from spacy.tokens import Doc, Token, Span
from spacy.language import Language
import textwrap
from util.RestCaller import callAllenNlpApi
from transformers import logging
logging.set_verbosity_error()

from py2neo import Graph
from py2neo import *




class TextProcessor(object):


    def get_annotated_text(self):
        graph = Graph("bolt://10.200.37.170:7687", auth=("neo4j", "neo123"))

        query = "MATCH (n:AnnotatedText) RETURN n.text, n.id"
        data= graph.run(query).data()

        annotatedd_text_docs= list()

        for record in data:
            #print(record)
            #print(record.get("n.text"))
            t = (record.get("n.text"), {'text_id': record.get("n.id")})
            annotatedd_text_docs.append(t)
        
        return annotatedd_text_docs

            

        

        


    
    def apply_pipeline_1(self, doc, flag_display = False):

        graph = Graph("bolt://10.200.37.170:7687", auth=("neo4j", "neo123"))
        #doc = nlp(ss)

        list_pipeline = []

        # for tok in doc:
        #     list_pipeline.append((tok.i, tok.text, tok.tag_, tok.pos_, tok.dep_, 
        #                         '\n'.join(textwrap.wrap(json.dumps(tok._.SRL), width = 60))
        #                         ))

        #a = Node("Frame", text="verb", span="", startIndex="", endIndex="")
        #b = Node("FrameArgument", type="", text="Bob", span="", startIndex="", endIndex="")
        
        frameDict ={}

        v = ""
        sg = ""
        tv = ""
        ta = ""

        PARTICIPANT = Relationship.type("PARTICIPANT")
        PARTICIPATES_IN = Relationship.type("PARTICIPATES_IN")

        for tok in doc:
            sg=""
            v="" 
            frameDict={} 
            for x,y in tok._.SRL.items():
                span = doc[y[0]:y[len(y)-1]+1]


                # now got the span, iterate through span for each token
                # locate that token in neo4j as the TagOccurrence by id
                # make connection with the frame or frameargument node.


                if x == "V":
                    # see if the token refers to verb (predicate)
                    v = Node("Frame", text=span.text, startIndex=y[0], endIndex=y[len(y)-1])

                    for index in y:
                        query = "match (x:TagOccurrence {tok_index_doc:" + str(index) + "})-[:HAS_TOKEN]-()-[:CONTAINS_SENTENCE]-(:AnnotatedText {id:"+str(doc._.text_id)+"}) return x"
                        token_node= graph.evaluate(query) 
                        token_verb_rel = PARTICIPATES_IN(token_node,v)

                    #frameDict[x] = v;
                    # save the verb node seperately 
                    #sg=v
                    #sg = token_span_rel 
                    tv = token_verb_rel
                else:
                    # find all the respective argument nodes and save it to dictionary
                    a = Node("FrameArgument", type= x, text=span.text, startIndex=y[0], endIndex=y[len(y)-1])

                    if a is None:
                        continue
                    
                    for index in y:
                        query = "match (x:TagOccurrence {tok_index_doc:" + str(index) + "})-[:HAS_TOKEN]-()-[:CONTAINS_SENTENCE]-(:AnnotatedText {id:"+str(doc._.text_id)+"}) return x"
                        token_node= graph.evaluate(query) 

                        if token_node is None:
                            continue
                        token_arg_rel = PARTICIPATES_IN(token_node,a)

                        if ta == "":
                            ta = token_arg_rel
                        else:
                            ta = ta | token_arg_rel

                    frameDict[x] = a;
            
            if tv == "":
                continue
            else:
                sg = tv | ta

                for i in frameDict:
                    if not sg:
                        break;
                    r = PARTICIPANT(frameDict[i],v)
                    sg = sg | r


                graph.create(sg)

            #print(x, ": ",y, span.text)
                        

        # print("list pipeline: ", list_pipeline)
        # print("------------------------------------------------")
        # print(tok._.SRL)

    

    def __init__(self, nlp, driver):
        self.nlp = nlp
        self._driver = driver

 # query = """MERGE (ann:AnnotatedText {id: $id})
       #     RETURN id(ann) as result
        #"""

        
    def create_annotated_text(self, filename, id):
        filename = "file://" + filename
        query = """ CALL apoc.load.xml($filename) 
        YIELD value
        UNWIND [item in value._children where item._type ="nafHeader"] AS nafHeader
        UNWIND [item in value._children where item._type ="raw"] AS raw
        UNWIND [item in nafHeader._children where item._type = "fileDesc"] AS fileDesc
        UNWIND [item in nafHeader._children where item._type = "public"] AS public
        WITH  fileDesc.author as author, fileDesc.creationtime as creationtime, fileDesc.filename as filename, fileDesc.filetype as filetype, fileDesc.title as title, public.publicId as publicId, public.uri as uri, raw._text as text
        MERGE (at:AnnotatedText {id: $id}) set at.author = author, at.creationtime = creationtime, at.filename = filename, at.filetype = filetype, at.title = title, at.publicId = publicId, at.uri = uri, at.text = replace(text,"  "," ")
        """
        params = {"id": id, "filename":filename}
        results = self.execute_query(query, params)
        #return results[0]

    def process_sentences(self, annotated_text, doc, storeTag, text_id):
        i = 1
        for sentence in doc.sents:
            sentence_id = self.store_sentence(sentence, annotated_text, text_id, i, storeTag)
            #spans = list(doc.ents) + list(doc.noun_chunks) - just removed so that only entities get stored.
            spans = list(doc.ents)
            spans = filter_spans(spans)
            i += 1
        return spans

    def store_sentence(self, sentence, annotated_text, text_id, sentence_id, storeTag):
        # sentence_query = """MATCH (ann:AnnotatedText) WHERE id(ann) = $ann_id
        #     MERGE (sentence:Sentence {id: $sentence_unique_id})
        #     SET sentence.text = $text
        #     MERGE (ann)-[:CONTAINS_SENTENCE]->(sentence)
        #     RETURN id(sentence) as result
        # """


        sentence_query = """MATCH (ann:AnnotatedText) WHERE ann.id = $ann_id
            MERGE (sentence:Sentence {id: $sentence_unique_id})
            SET sentence.text = $text
            MERGE (ann)-[:CONTAINS_SENTENCE]->(sentence)
            RETURN id(sentence) as result
        """

        tag_occurrence_query = """MATCH (sentence:Sentence) WHERE id(sentence) = $sentence_id
            WITH sentence, $tag_occurrences as tags
            FOREACH ( idx IN range(0,size(tags)-2) |
            MERGE (tagOccurrence1:TagOccurrence {id: tags[idx].id})
            SET tagOccurrence1 = tags[idx]
            MERGE (sentence)-[:HAS_TOKEN]->(tagOccurrence1)
            MERGE (tagOccurrence2:TagOccurrence {id: tags[idx + 1].id})
            SET tagOccurrence2 = tags[idx + 1]
            MERGE (sentence)-[:HAS_TOKEN]->(tagOccurrence2)
            MERGE (tagOccurrence1)-[r:HAS_NEXT {sentence: sentence.id}]->(tagOccurrence2))
            RETURN id(sentence) as result
        """

        tag_occurrence_with_tag_query = """MATCH (sentence:Sentence) WHERE id(sentence) = $sentence_id
            WITH sentence, $tag_occurrences as tags
            FOREACH ( idx IN range(0,size(tags)-2) |
            MERGE (tagOccurrence1:TagOccurrence {id: tags[idx].id})
            SET tagOccurrence1 = tags[idx]
            MERGE (sentence)-[:HAS_TOKEN]->(tagOccurrence1)
            MERGE (tagOccurrence2:TagOccurrence {id: tags[idx + 1].id})
            SET tagOccurrence2 = tags[idx + 1]
            MERGE (sentence)-[:HAS_TOKEN]->(tagOccurrence2)
            MERGE (tagOccurrence1)-[r:HAS_NEXT {sentence: sentence.id}]->(tagOccurrence2))
            FOREACH (tagItem in [tag_occurrence IN $tag_occurrences WHERE tag_occurrence.is_stop = False] | 
            MERGE (tag:Tag {id: tagItem.lemma}) MERGE (tagOccurrence:TagOccurrence {id: tagItem.id}) MERGE (tag)<-[:REFERS_TO]-(tagOccurrence))
            RETURN id(sentence) as result
        """

        params = {"ann_id": annotated_text, "text": sentence.text,
                  "sentence_unique_id": str(text_id) + "_" + str(sentence_id)}
        results = self.execute_query(sentence_query, params)
        node_sentence_id = results[0]
        tag_occurrences = []
        tag_occurrence_dependencies = []
        for token in sentence:
            lexeme = self.nlp.vocab[token.text]
            # edited: included the punctuation as possible token candidates.
            #if not lexeme.is_punct and not lexeme.is_space:
            if not lexeme.is_space:
                tag_occurrence_id = str(text_id) + "_" + str(sentence_id) + "_" + str(token.idx)
                tag_occurrence = {"id": tag_occurrence_id,
                                  "index": token.idx,
                                  "text": token.text,
                                  "lemma": token.lemma_,
                                  "pos": token.tag_,
                                  "tok_index_doc": token.i,
                                  "tok_index_sent": (token.i - sentence.start),
                                  "is_stop": (lexeme.is_stop or lexeme.is_punct or lexeme.is_space)}
                tag_occurrences.append(tag_occurrence)
                tag_occurrence_dependency_source = str(text_id) + "_" + str(sentence_id) + "_" + str(token.head.idx)
                dependency = {"source": tag_occurrence_dependency_source, "destination": tag_occurrence_id,
                              "type": token.dep_}
                tag_occurrence_dependencies.append(dependency)
        params = {"sentence_id": node_sentence_id, "tag_occurrences": tag_occurrences}
        if storeTag:
            results = self.execute_query(tag_occurrence_with_tag_query, params)
        else:
            results = self.execute_query(tag_occurrence_query, params)

        self.process_dependencies(tag_occurrence_dependencies)
        return results[0]

    def process_entities(self, spans, text_id):
        nes = []
        for entity in spans:
            ne = {'value': entity.text, 'type': entity.label_, 'start_index': entity.start_char,
                  'end_index': entity.end_char}
            nes.append(ne)
        self.store_entities(text_id, nes)
        return nes

    def process_noun_chunks(self, doc, text_id):
        ncs = []
        for noun_chunk in doc.noun_chunks:
            nc = {'value': noun_chunk.text, 'type': noun_chunk.label_, 'start_index': noun_chunk.start_char,
                  'end_index': noun_chunk.end_char}
            ncs.append(nc)
        self.store_noun_chunks(text_id, ncs)
        return ncs

    def store_noun_chunks(self, document_id, ncs):
        nc_query = """
            UNWIND $ncs as item
            MERGE (nc:NounChunk {id: toString($documentId) + "_" + toString(item.start_index)})
            SET nc.type = item.type, nc.value = item.value, nc.index = item.start_index
            WITH nc, item as ncIndex
            MATCH (text:AnnotatedText)-[:CONTAINS_SENTENCE]->(sentence:Sentence)-[:HAS_TOKEN]->(tagOccurrence:TagOccurrence)
            WHERE text.id = $documentId AND tagOccurrence.index >= ncIndex.start_index AND tagOccurrence.index < ncIndex.end_index
            MERGE (nc)<-[:PARTICIPATES_IN]-(tagOccurrence)
        """
        self.execute_query(nc_query, {"documentId": document_id, "ncs": ncs})

    def store_entities(self, document_id, nes):
        ne_query = """
            UNWIND $nes as item
            MERGE (ne:NamedEntity {id: toString($documentId) + "_" + toString(item.start_index)})
            SET ne.type = item.type, ne.value = item.value, ne.index = item.start_index
            WITH ne, item as neIndex
            MATCH (text:AnnotatedText)-[:CONTAINS_SENTENCE]->(sentence:Sentence)-[:HAS_TOKEN]->(tagOccurrence:TagOccurrence)
            WHERE text.id = $documentId AND tagOccurrence.index >= neIndex.start_index AND tagOccurrence.index < neIndex.end_index
            MERGE (ne)<-[:PARTICIPATES_IN]-(tagOccurrence)
        """
        self.execute_query(ne_query, {"documentId": document_id, "nes": nes})


    def process_coreference2(self, doc, text_id):
        coref = []
        if doc._.has_coref:
            for cluster in doc._.coref_clusters:
                mention = {'from_index': cluster.mentions[-1].start_char, 'to_index': cluster.mentions[0].start_char}
                coref.append(mention)
            self.store_coref(text_id, coref)
        return coref

    def process_coreference(self,doc,text_id):
        coref = []

        if len(doc._.coref_chains) > 0:
            for chain in doc._.coref_chains:
                for x in range(len(chain)-1):
                    mention = {'from_index': doc[chain[x+1].token_indexes[0]].idx, 'to_index': doc[chain[0].token_indexes[0]].idx}
                    coref.append(mention)
            self.store_coref(text_id,coref)
        return coref


    def store_coref2(self, document_id, corefs):
        coref_query = """
                MATCH (document:AnnotatedText)
                WHERE document.id = $documentId 
                WITH document
                UNWIND $corefs as coref  
                MATCH (document)-[*2]->(start:TagOccurrence), (document)-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NamedEntity) 
                WHERE start.index = coref.from_index AND np.index = coref.to_index
                MERGE (start)-[:MENTIONS]->(end)
        """
        self.execute_query(coref_query,
                           {"documentId": document_id, "corefs": corefs})

    
    def store_coref(self, document_id, corefs):
        coref_query = """
                MATCH (document:AnnotatedText)
                WHERE document.id = $documentId 
                WITH document
                UNWIND $corefs as coref  
                MATCH (document)-[*2]->(start:TagOccurrence), (document)-[*2]->(np:TagOccurrence)-[:PARTICIPATES_IN]->(end:NounChunk) 
                WHERE start.index = coref.from_index AND np.index = coref.to_index
                MERGE (start)-[:MENTIONS]->(end)
        """
        self.execute_query(coref_query,
                           {"documentId": document_id, "corefs": corefs})

    
    
    
    def process_textrank(self, doc, text_id):
        keywords = []
        spans = []
        for p in doc._.phrases:
            for span in p.chunks:
                item = {"span": span, "rank": p.rank}
                spans.append(item)
        spans = filter_extended_spans(spans)
        for item in spans:
            span = item['span']
            lexme = self.nlp.vocab[span.text]
            if lexme.is_stop or lexme.is_digit or lexme.is_bracket or "-PRON-" in span.lemma_:
                continue
            keyword = {"id": span.lemma_, "start_index": span.start_char, "end_index": span.end_char}
            if len(span.ents) > 0:
                keyword['NE'] = span.ents[0].label_
            keyword['rank'] = item['rank']
            keywords.append(keyword)
        self.store_keywords(text_id, keywords)

    # def create_annotated_text(self, doc, id):
    #     query = """MERGE (ann:AnnotatedText {id: $id})
    #         RETURN id(ann) as result
    #     """
    #     params = {"id": id}
    #     results = self.execute_query(query, params)
    #     return results[0]

    def process_dependencies(self, tag_occurrence_dependencies):
        tag_occurrence_query = """UNWIND $dependencies as dependency
            MATCH (source:TagOccurrence {id: dependency.source})
            MATCH (destination:TagOccurrence {id: dependency.destination})
            MERGE (source)-[:IS_DEPENDENT {type: dependency.type}]->(destination)
                """
        self.execute_query(tag_occurrence_query, {"dependencies": tag_occurrence_dependencies})

    def store_keywords(self, document_id, keywords):
        ne_query = """
            UNWIND $keywords as keyword
            MERGE (kw:Keyword {id: keyword.id})
            SET kw.NE = keyword.NE, kw.index = keyword.start_index, kw.endIndex = keyword.end_index
            WITH kw, keyword
            MATCH (text:AnnotatedText)
            WHERE text.id = $documentId
            MERGE (text)<-[:DESCRIBES {rank: keyword.rank}]-(kw)
        """
        self.execute_query(ne_query, {"documentId": document_id, "keywords": keywords})

    def build_entities_inferred_graph(self, document_id):
        extract_direct_entities_query = """
            MATCH (document:AnnotatedText)
            WHERE document.id = $documentId
            WITH document
            MATCH (document)-[*3..3]->(ne:NamedEntity)
            WHERE NOT ne.type IN ['NP', 'NUMBER', 'DATE']
            WITH ne
            MERGE (entity:Entity {type: ne.type, id:ne.value})
            MERGE (ne)-[:REFERS_TO {type: "evoke"}]->(entity)
        """

        extract_indirect_entities_query = """
            MATCH (document:AnnotatedText)
            WHERE document.id = $documentId
            WITH document
            MATCH (document)-[*3..3]->(ne:NamedEntity)<-[:MENTIONS]-(mention)
            WHERE NOT ne.type IN ['NP', 'NUMBER', 'DATE']
            WITH ne, mention
            MERGE (entity:Entity {type: ne.type, id:ne.value})
            MERGE (mention)-[:REFERS_TO {type: "access"}]->(entity)
        """
        self.execute_query(extract_direct_entities_query, {"documentId": document_id})
        self.execute_query(extract_indirect_entities_query, {"documentId": document_id})

    def extract_relationships(self, document_id, rules):
        extract_relationships_query = """
            MATCH (document:AnnotatedText)
            WHERE document.id = $documentId
            WITH document
            UNWIND $rules as rule
            MATCH (document)-[*2..2]->(verb:TagOccurrence {pos: "VBD"})
            MATCH (verb:TagOccurrence {pos: "VBD"})
            WHERE verb.lemma IN rule.verbs
            WITH verb, rule
            MATCH (verb)-[:IS_DEPENDENT {type:"nsubj"}]->(subject)-[:PARTICIPATES_IN]->(subjectNe:NamedEntity)
            WHERE subjectNe.type IN rule.subjectTypes
            MATCH (verb)-[:IS_DEPENDENT {type:"dobj"}]->(object)-[:PARTICIPATES_IN]->(objectNe:NamedEntity {type: "WORK_OF_ART"})
            WHERE objectNe.type IN rule.objectTypes
            WITH verb, subjectNe, objectNe, rule
            MERGE (subjectNe)-[:IS_RELATED_TO {root: verb.lemma, type: rule.type}]->(objectNe)
        """
        self.execute_query(extract_relationships_query, {"documentId": document_id, "rules":rules})

    def build_relationships_inferred_graph(self, document_id):
        extract_relationships_query = """
            MATCH (document:AnnotatedText)
            WHERE document.id = $documentId
            WITH document
            MATCH (document)-[*2..3]->(ne1:NamedEntity)
            MATCH (entity1:Entity)<-[:REFERS_TO]-(ne1:NamedEntity)-[r:IS_RELATED_TO]->(ne2:NamedEntity)-[:REFERS_TO]->(entity2:Entity)
            MERGE (evidence:Evidence {id: id(r), type:r.type})
            MERGE (rel:Relationship {id: id(r), type:r.type})
            MERGE (ne1)<-[:SOURCE]-(evidence)
            MERGE (ne2)<-[:DESTINATION]-(evidence)
            MERGE (rel)-[:HAS_EVIDENCE]->(evidence)
            MERGE (entity1)<-[:FROM]-(rel)
            MERGE (entity2)<-[:TO]-(rel)
        """
        self.execute_query(extract_relationships_query, {"documentId": document_id})

    def execute_query(self, query, params):
        results = []
        with self._driver.session() as session:
            for items in session.run(query, params):
                item = items["result"]
                results.append(item)
        return results


def filter_spans(spans):
    get_sort_key = lambda span: (span.end - span.start, -span.start)
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for span in sorted_spans:
        # Check for end - 1 here because boundaries are inclusive
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            result.append(span)
        seen_tokens.update(range(span.start, span.end))
    result = sorted(result, key=lambda span: span.start)
    return result


def filter_extended_spans(items):
    get_sort_key = lambda item: (item['span'].end - item['span'].start, -item['span'].start)
    sorted_spans = sorted(items, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for item in sorted_spans:
        # Check for end - 1 here because boundaries are inclusive
        if item['span'].start not in seen_tokens and item['span'].end - 1 not in seen_tokens:
            result.append(item)
        seen_tokens.update(range(item['span'].start, item['span'].end))
    result = sorted(result, key=lambda span: span['span'].start)
    return result


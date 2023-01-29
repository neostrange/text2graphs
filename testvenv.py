import spacy
from util.RestCaller import callAllenNlpApi

nlp = spacy.blank("en")
#nlp.add_pipe('opentapioca')
doc = nlp("Japan began the defence of their title with a lucky 2-1 win against Syria in a championship match on Friday.")
#for span in doc.ents:
 #   print((span.text, span.kb_id_, span.label_, span._.description, span._.score))

#print(doc.text)

result = callAllenNlpApi("coreference-resolution", "the quick brown fox jumps over the lazy dog." )

print(result)
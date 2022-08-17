# text2graphs

- install spacy 3.3.1
- install spacy models both trf and lg
  - python -m spacy download en_core_web_trf
  - python -m spacy download en_core_web_lg
- install coreferee
  - python3 -m pip install coreferee
  - python3 -m coreferee install en
- install neo4j
- install py2neo
- install GPUtil
- install neo4j desktop and 
  - copy the files from the dataset folder in repository to the import folder. 
  - install apoc plugin and enable import file configuration in apoc.conf file. 
  - Restart the neo4j.
- this command is not required until you need to work in nested dir: export PYTHONPATH="$(pwd):$PYTHONPATH"

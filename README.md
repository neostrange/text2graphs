# text2graphs

- install spacy 3.3.1
- install spacy models both trf and lg
  - python -m spacy download en_core_web_trf
  - python -m spacy download en_core_web_lg
- install coreferee
  - python3 -m pip install coreferee
  - python3 -m coreferee install en
- pip install neo4j
- pip install py2neo
- pip install GPUtil
- You may also need to replace the spacy-transformers with version 1.1.6
- install neo4j desktop and 
  - copy the files from the dataset folder in repository to the import folder of Neo4j. 
  - install apoc pluginin neo4j and enable import file configuration in apoc.conf file (note: you would need to create apoc.conf file in project conf folder. Type the folder command in apoc.conf file apoc.import.file.enabled=true). 
  - Restart the neo4j instance.
- this command is not required until you need to work in nested dir: export PYTHONPATH="$(pwd):$PYTHONPATH"



-Run power shell to make wsl entry in windows fire wall using following command and restart the system
  - New-NetFirewallRule -DisplayName "WSL" -Direction Inbound  -InterfaceAlias "vEthernet (WSL)"  -Action Allow
  
 - Neo4J setting, enable set dbms.default_listen_address=0.0.0.0

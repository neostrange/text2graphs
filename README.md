Text2Graph: Autonomous Knowledge Graph Generation Framework
Text2Graph is a Python-based framework for the autonomous construction of domain-specific Knowledge Graphs (KG) from unstructured text data. The system transforms textual data into a labeled property graph-based representation using various NLP and semantic processing tools and integrates with Neo4j for graph storage and querying.

Features
Automated NLP pipeline for entity extraction, relation extraction, and semantic enrichment.
Integration with Neo4j for graph-based storage and querying.
Support for large-scale Knowledge Graphs with rich domain-specific entity typing, event tagging, and temporal relationships.
Extensible and schema-free architecture.
Requirements
System Requirements
Ubuntu Linux (or Windows Subsystem for Linux (WSL))
Neo4j 4.4 with APOC plugin
Docker for external NLP services
Python 3.8+



Python Dependencies
Ensure Python 3.8+ is installed. You can install the required dependencies using the following instructions:
# Clone the repository
git clone https://github.com/yourusername/text2graph.git
cd text2graph


Install SpaCy and Models
pip install spacy
python -m spacy download en_core_web_trf
python -m spacy download en_core_web_lg


Additional SpaCy Dependency
pip install spacy-dbpedia-spotlight


Install WordNet (nltk) 3.1
pip install nltk
python -c "import nltk; nltk.download('wordnet')"


Other Python Dependencies
pip install cgitb requests distutils spacy json tokenize GPUtil textwrap py2neo configparser neo4j
pip install py2neo==2021.2.3  # Ensure version compatibility
pip install GPUtil


SpaCy Transformers (Version Fix)
If you encounter issues with SpaCy's transformers, you may need to downgrade:
pip install spacy-transformers==1.1.6


Neo4j Setup
Install Neo4j 4.4: Follow the Neo4j installation instructions for your system.

Enable APOC Plugin:

Install the APOC plugin via the Neo4j plugin manager.
Create an apoc.conf file in the Neo4j configuration folder (typically located at /var/lib/neo4j/conf/), and add the following:

apoc.import.file.enabled=true

Copy Dataset Files: Copy the files from the dataset folder in this repository to the import folder of Neo4j (usually located at /var/lib/neo4j/import/).

Restart Neo4j: Restart the Neo4j service to apply the changes:

sudo systemctl restart neo4j

Neo4j Configuration for WSL: If running on WSL, enable the Neo4j default listen address in the Neo4j configuration (/etc/neo4j/neo4j.conf):
dbms.default_listen_address=0.0.0.0


Docker Services
To extend the pipeline, you must ensure the following Docker containers are running:

Coreference Resolution:

Build from this repository: Spacy Coref Docker
Expose on localhost:9999:


Event Tagging:

Build from this repository: TTK Docker
Expose on localhost:5050:


Temporal Expression Tagging:

Use the HeidelTime WebService: HeidelTime WebService Docker
Expose on localhost:5000:


Word Sense Disambiguation:

Use AMUSE-WSD Docker:
Expose on localhost:81:


Semantic Role Labeling:

From AllenNLP Docker:
Expose on localhost:8000:


Make sure all Docker services are running before initiating the text2graph pipeline to ensure full functionality for entity enrichment, event tagging, and temporal expressions.



WSL Specific Setup
If you're running the project on WSL (Windows Subsystem for Linux), you may need to configure the firewall:

Add WSL to Windows Firewall: Run the following command in PowerShell (as Administrator):

New-NetFirewallRule -DisplayName "WSL" -Direction Inbound -InterfaceAlias "vEthernet (WSL)" -Action Allow

Restart Your System: After applying the firewall rule, restart your computer.


Usage Instructions
Set up the Python Path (optional): If you need to work with nested directories, you can add the current working directory to the Python path:
export PYTHONPATH="$(pwd):$PYTHONPATH"


Run the Pipeline: After setting up the environment and ensuring the Docker services are running, you can start processing text documents using the pipeline to generate the Knowledge Graph:

python3 text2graph.py --input /path/to/text/documents




Neo4j Interaction: The framework provides REST endpoints (powered by FastAPI) to query the generated Knowledge Graph in Neo4j.

Contributing
Contributions to text2graph are welcome! Please submit a pull request or open an issue for any bugs or feature requests.

License
This project is licensed under the MIT License. See the LICENSE file for more details.



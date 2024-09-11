
# Text2Graph: Autonomous Knowledge Graph Generation Framework
Text2Graph is a Python-based framework for the autonomous construction of domain-specific Knowledge Graphs (KG) from unstructured text data. The system transforms textual data into a labeled property graph-based representation using various NLP and semantic processing tools and integrates with Neo4j for graph storage and querying.

## Features
- Automated NLP pipeline for entity extraction, relation extraction, and semantic enrichment.
- Integration with Neo4j for graph-based storage and querying.
- Support for large-scale Knowledge Graphs with rich domain-specific entity typing, event tagging, and temporal relationships.
- Extensible and schema-free architecture.

## Requirements

### System Requirements
- Ubuntu Linux (or Windows Subsystem for Linux (WSL))
- Neo4j 4.4 with APOC plugin
- Docker for external NLP services
- Python 3.8+

### Python Dependencies
Ensure Python 3.8+ is installed. You can install the required dependencies using the following instructions:

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/text2graph.git
   cd text2graph
2. Install Spacy Mode
    ```bash
    pip install spacy
    python -m spacy download en_core_web_trf
    python -m spacy download en_core_web_lg
3. Additional SpaCy Dependency
    ```bash
    pip install spacy-dbpedia-spotlight
4. Install WordNet (nltk) 3.1
    ```bash
    pip install nltk
    python -c "import nltk; nltk.download('wordnet')"
5. Other Python Dependencies
    ```bash
    pip install cgitb requests distutils spacy json tokenize    
    GPUtil textwrap py2neo configparser neo4j
    pip install py2neo==2021.2.3
    pip install GPUtil
6. SpaCy Transformers (Version Fix) If you encounter issues with SpaCy's transformers, you may need to downgrade:
    ```bash
    pip install spacy-transformers==1.1.6





## Neo4j Setup

1. Install Neo4j 4.4:** Follow the Neo4j installation instructions for your system.
2. Enable APOC Plugin**
   * Install the APOC plugin via the Neo4j plugin manager.
   * Create an `apoc.conf` file in the Neo4j configuration folder (typically located at `/var/lib/neo4j/conf/`), and add the following:
     ```bash
     apoc.import.file.enabled=true
     ```
3. Copy Dataset Files**
   * Copy the files from the `dataset` folder in this repository to the import folder of Neo4j (usually located at `/var/lib/neo4j/import/`).
4. Restart Neo4j**
   * Restart the Neo4j service to apply the changes:
     ```bash
     sudo systemctl restart neo4j
     ```
5. Neo4j Configuration for WSL**
   * If running on WSL, enable the Neo4j default listen address in the Neo4j configuration (`/etc/neo4j/neo4j.conf`):
     ```bash
     dbms.default_listen_address=0.0.0.0

## Docker Services

To extend the pipeline, you must ensure the following Docker containers are running:

* Coreference Resolution:
    * Build from this repository: Spacy Coref Docker
    * Expose on localhost:9999:
        ```bash
        docker run -p 9999:9999 neostrange/spacy-experimental-coref
        ```
* Event Tagging:
    * Build from this repository: TTK Docker
    * Expose on localhost:5050:
        ```bash
        docker run -p 5050:5050 neostrange/ttk
        ```
* Temporal Expression Tagging:
    * Use the HeidelTime WebService: HeidelTime WebService Docker
    * Expose on localhost:5000:
        ```bash
        docker run -p 5000:5000 neostrange/heideltime
        ```
* Word Sense Disambiguation:
    * Use AMUSE-WSD Docker:
    * Expose on localhost:81:
        ```bash
        docker run -p 81:81 amuse/amuse-wsd
        ```
* Semantic Role Labeling:
    * From AllenNLP Docker:
    * Expose on localhost:8000:
        ```bash
        docker run -p 8000:8000 allennlp/allennlp
        ```

Make sure all Docker services are running before initiating the `text2graph` pipeline to ensure full functionality for entity enrichment, event tagging, and temporal expressions.
## WSL Specific Setup

If you're running the project on WSL (Windows Subsystem for Linux), you may need to configure the firewall:

* **Add WSL to Windows Firewall:**
    * Run the following command in PowerShell (as Administrator):
      ```powershell
      New-NetFirewallRule -DisplayName "WSL" -Direction Inbound -InterfaceAlias "vEthernet (WSL)" -Action Allow
      ```
* **Restart Your System:**
    * After applying the firewall rule, restart your computer.
## Usage Instructions

**Set up the Python Path (optional):**

If you need to work with nested directories, you can add the current working directory to the Python path:

```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

**Run the Pipeline:**

After setting up the environment and ensuring the Docker services are running, you can start processing text documents using the pipeline to generate the Knowledge Graph:

```bash
python3 text2graph.py --input /path/to/text/documents
```

## Neo4j Interaction
Neo4j Interaction: The framework provides REST endpoints (powered by FastAPI) to query the generated Knowledge Graph in Neo4j.


## Contributing to Text2Graph

**We welcome contributions to Text2Graph!** If you have any bugs to report, feature requests, or would like to contribute new functionality, please submit a pull request or open an issue on our GitHub repository.
We appreciate your contributions to Text2Graph! By following these guidelines, you can help us improve the framework and make it more valuable for the community.
## Screenshots

![App Screenshot](https://github.com/neostrange/text2graphs/blob/main/images/Screenshot%202024-06-10%20105103.png)

![App Screenshot](https://github.com/neostrange/text2graphs/blob/main/images/Screenshot%202024-06-10%20105205.png)














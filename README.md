
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
## Run the Pipeline

The Text2Graph pipeline is a modular system designed to efficiently generate Knowledge Graphs from textual data. It consists of several distinct phases, each focusing on specific NLP tasks. Let's walk through how to run the pipeline and explore each phase:

**Phase 1: Basic Linguistic Analysis (python3 GraphBasedNLP.py --input /path/to/text/documents)**

* **Function:** This phase performs the foundational tasks of Natural Language Processing (NLP) on the input text documents. 
* **Input:** You can specify the path to your text documents using the `--input` argument. If no argument is provided, the script will load text data files by default from the `data/dataset` folder within the Text2Graph repository. Currently, this folder contains pre-loaded files from the MEANTIME corpus for your convenience.

**Running Phase 1:**

1. Open a terminal window and navigate to the directory containing the `GraphBasedNLP.py` script within your Text2Graph installation.
2. (Optional) If you have your own text documents, execute the script with the `--input` argument followed by the path to your data directory:

   ```bash
   python3 GraphBasedNLP.py --input /path/to/your/text/documents
3. If you'd like to use the pre-loaded MEANTIME corpus data, simply run the script without any arguments:
   ```bash
   python3 GraphBasedNLP.py```

**Phase 2: Refinement Phase**
* **Function:** This phase focuses on refining the extracted information from Phase 1. It establishes connections between different linguistic elements and ensures consistency within the data.
* **Input:** The output from Phase 1 (typically stored in a Neo4j database) serves as the input for this phase.
**Running Phase 2:**

1. Ensure Phase 1 has completed successfully.
2. Navigate to the directory containing the RefinementPhase.py script.
3. Execute the script
   ```bash
   python3 RefinementPhase.py
**Phase 3: Temporal Enrichment**

* **Function:** This phase enriches the Knowledge Graph with temporal information. It involves identifying and tagging time expressions and event triggers within the text data.
* **Input:** The refined data from Phase 2 is used as input for this phase.

**Running Phase 3:**
1. Ensure Phases 1 and 2 have completed successfully.
2. Navigate to the directory containing the TemporalPhase.py script.
3. Execute the script:
   ```bash
   python3 TemporalPhase.py
**Phase 4: Event Enrichment**
* **Function:** This phase focuses on enriching event information within the Knowledge Graph. It establishes links between identified events and entities, as well as other events, based on the linguistic elements present in the graph.
* **Input:** The temporally enriched data from Phase 3 is used as input for this phase.

**Running Phase 4:**
1. Ensure Phases 1, 2 and 3 have completed successfully.
2. Navigate to the directory containing the EventEnrichmentPhase.py script.
3. Execute the script:   
   ```bash
   python3 EventEnrichmentPhase.py

**Phase 5: TLink Recognition**

**Function:** This phase aims to identify Temporal Links (TLinks) within the Knowledge Graph. TLinks describe temporal relationships between events, such as "before," "after," or "during".  
**Input:** The event-enriched data from phase 4, will serve as input for TLink recognition.
**Running Phase 5:**
1. Ensure all the previous steps have been completed.
2. Navigate to the directory containing TlinksRecognizer.py script.
3. Execute the script:
   ```bash
   python3 TlinksRecognizer.py




## Neo4j Interaction
Note: While the REST endpoints powered by FastAPI are not yet implemented, you can still interact with the generated Knowledge Graph directly through the Neo4j Browser or Neo4j Bloom.

These tools provide a user-friendly interface for exploring and querying the graph data. You can execute Cypher queries to retrieve specific information or visualize the graph structure.


## Screenshots

![App Screenshot](https://github.com/neostrange/text2graphs/blob/main/images/Screenshot%202024-06-10%20105103.png)

![App Screenshot](https://github.com/neostrange/text2graphs/blob/main/images/Screenshot%202024-06-10%20105205.png)



## References

1. A. Hur, N. Janjua, and M. Ahmed, "A Survey on State-of-the-art Techniques for Knowledge Graphs Construction and Challenges ahead," 2021 IEEE Fourth International Conference on Artificial Intelligence and Knowledge Engineering (AIKE), Laguna Hills, CA, USA, 2021, pp. 99-103, doi: [10.1109/AIKE52691.2021.00021](https://doi.org/10.1109/AIKE52691.2021.00021).

2. Ali Hur, Naeem Janjua, and Mohiuddin Ahmed, "Unifying context with labeled property graph: A pipeline-based system for comprehensive text representation in NLP," Expert Systems with Applications, Volume 239, 2024, 122269, doi: [10.1016/j.eswa.2023.122269](https://doi.org/10.1016/j.eswa.2023.122269).

3. A. Hur, N. Janjua, "Constructing Domain-Specific Knowledge Graphs From Text: A Case Study on Subprime Mortgage Crisis," Special Issue on Knowledge Graph Construction, Semantic Web Journal (by IOS Press), 2024 **(Under Review)**.

## Contributing to Text2Graph

**We welcome contributions to Text2Graph!** If you have any bugs to report, feature requests, or would like to contribute new functionality, please submit a pull request or open an issue on our GitHub repository.
We appreciate your contributions to Text2Graph!, you can help us improve the framework and make it more valuable for the community.
## License

[MIT](https://choosealicense.com/licenses/mit/)


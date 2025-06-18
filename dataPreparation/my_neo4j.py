import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
import os

#TODO: Create Relevant section on the properties of nodes and edges so that only that can be sent to the LLMs


class Node(BaseModel):
    extraction_id: str
    first_level_class:str
    second_level_class:str
    extracted_content:str
    supporting_evidence: str
    confidence_score: float
    keywords: List[str]

class Relationship(BaseModel):
    relationship_id:str
    source_extraction_id:str
    target_extraction_id:str
    relationship_type:str
    relationship_description: str
    confidence_score: float
    supporting_evidence:str
    
class Paper(BaseModel):
    paper_id: str
    main_theme:str
    key_contributions: List[str]
    study_location: str
    study_period: str
    primary_methods: List[str]    

load_dotenv()


URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
def create_node(tx, node:Node)->bool:
    """
    Transactional function created for Neo4j to create a node
    Args:
        tx: default way to perform transaction
        node[Node]: node object that contains all the information to be store in the node
    Returns:
        True if nodes are created successfully
    """
    node_id = node.extraction_id
    label = node.first_level_class.replace('-', '_') +'_' + node.second_level_class.replace('-', '_')
    props = {
             "id": node.extraction_id,
             "content": node.extracted_content,
             "evidence": node.supporting_evidence,
             "confidence_score": node.confidence_score,
             "keywords": node.keywords}
    tx.run(f"MERGE (n:{label} {{id:$id}}) SET n+= $props", id=node_id, props=props)
    return True


def create_relationship(tx, relationship:Relationship)->bool:
    """
    Transactional function created for Neo4j to create relationship(edge) between nodes
    Args:
        tx: default wat to perform transaction
        relationship[Relationship]: relationship object that contains ll the infromation to create an edge
    Returns:
        True if edges are created sucessfully
    """
    relationship_id = relationship.relationship_id
    label = relationship.relationship_type
    props = {
        "id": relationship_id,
        "type": label,
        "description": relationship.relationship_description,
        "confidence_score": relationship.confidence_score,
        "evidence": relationship.supporting_evidence
    }

    tx.run(f"""
            MATCH (a {{id:$source_id}}), (b {{id:$target_id}})
            MERGE (a)-[r:{label}]->(b)
            SET r += $props
    """, source_id = relationship.source_extraction_id, target_id = relationship.target_extraction_id, props=props )
    return True

def create_paper_connections(tx, paper:Paper, extractions:List[str])->bool:
    """
    Creates the paper and connect the papers with its extractions
    Args:
        tx: default way to perform transaction
        paper[Paper]: Paper object with its details
        extractions[List(str)]: list of extraction ids
    Returns:
        True if paper and its connections are created successfully
    """
    #create the paper node
    label = paper.paper_id
    props = {
            "main_theme":paper.main_theme,
            "key_contributions": paper.key_contributions,
            "study_location": paper.study_location,
            "study_period": paper.study_period,
            "primary_methods": paper.primary_methods
            }

    tx.run(f"MERGE (n:{label} {{id:$id}}) SET n+= $props", id=label, props=props)
    print('Success: Created paper node: ', label)

    for ex in extractions:
        tx.run(f"""
                MATCH (a {{id:$paper_id}}), (b {{id: $extraction_id}})
                MERGE (b)-[r:{'belongs_to'}]->(a)
            """, paper_id=paper.paper_id, extraction_id=ex)

    print('Success: Created relationship of papers with extractions')
    return True

if __name__ == '__main__':
    file_name = '/home/aditya/REU/Code/Graph_RAG/dataPreparation/ontology_outputs_json/v2/mandli_et_al_coupling_coastal_and_hydrologic_models_through_next_generation_national_water_model_framework.json'
    with open(file_name, 'r') as f:
       data = json.load(f)

    paper_id = data["paper_id"]
    paper = data["paper_summary"]
    paper["paper_id"] = paper_id
    
    extractions = []                #collection of all the extraction id so that they can be linked back to the paper
    
    nodes = data["extractions"]
    edges = data["relationships"]

    with driver.session() as session:
        # print('Sending node: ', nodes[0])
        # print('Type of node: ', type(nodes[0]) )
        for node in nodes:
            N = Node(**node)
            extractions.append(N.extraction_id)
            session.execute_write(create_node, N)
        print('Successfully created nodes: ', len(nodes))

        for edge in edges:
            E = Relationship(**edge)
            session.execute_write(create_relationship, E)

        print('Successfully created edges: ', len(edges))        
        
        session.execute_write(create_paper_connections, Paper(**paper), extractions)
        




    




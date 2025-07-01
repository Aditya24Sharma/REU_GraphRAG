"""
Neo4j modules containing all the functions for Neo4j
"""

from typing import List
import json
import logging
from dotenv import load_dotenv
from pydantic import BaseModel


from neo4j import GraphDatabase, Query

from . import config

# TODO: Create Relevant section on the properties of nodes & edge that only that can be sent to the LLMs

logger = logging.getLogger(__name__)
logging.getLogger("neo4j").setLevel(logging.WARNING)


class Node(BaseModel):
    extraction_id: str
    first_level_class: str
    second_level_class: str
    extracted_content: str
    supporting_evidence: str
    confidence_score: float
    keywords: List[str]


class Relationship(BaseModel):
    relationship_id: str
    source_extraction_id: str
    target_extraction_id: str
    relationship_type: str
    relationship_description: str
    confidence_score: float
    supporting_evidence: str


class Paper(BaseModel):
    paper_id: str
    main_theme: str
    key_contributions: List[str]
    study_location: str
    study_period: str
    primary_methods: List[str]


load_dotenv()


class Neo4j:
    """
    Neo4j class containing all the functions
    """

    def __init__(self) -> None:
        uri = config.NEO4J_URI or ""
        username = config.NEO4J_USERNAME or ""
        password = config.NEO4J_PASSWORD or ""
        self.driver = GraphDatabase.driver(uri=uri, auth=(username, password))

    def create_node(self, tx, node: Node) -> bool:
        """
        Transactional function created for Neo4j to create a node
        Args:
            tx: default way to perform transaction
            node[Node]: node object that contains all the information to be store in the node
        Returns:
            True if nodes are created successfully
        """
        try:
            node_id = node.extraction_id
            label = (
                node.first_level_class.replace("-", "_")
                + "_"
                + node.second_level_class.replace("-", "_")
            )
            props = {
                "id": node.extraction_id,
                "content": node.extracted_content,
                "evidence": node.supporting_evidence,
                "confidence_score": node.confidence_score,
                "keywords": node.keywords,
            }
            tx.run(
                f"MERGE (n:{label} {{id:$id}}) SET n+= $props", id=node_id, props=props
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create node: {e}")
            return False

    def create_relationship(self, tx, relationship: Relationship) -> bool:
        """
        Transactional function created for Neo4j to create relationship(edge) between nodes
        Args:
            tx: default wat to perform transaction
            relationship[Relationship]: relationship object that contains ll the infromation to create an edge
        Returns:
            True if edges are created sucessfully
        """
        try:
            relationship_id = relationship.relationship_id
            label = relationship.relationship_type
            props = {
                "id": relationship_id,
                "type": label,
                "description": relationship.relationship_description,
                "confidence_score": relationship.confidence_score,
                "evidence": relationship.supporting_evidence,
            }

            tx.run(
                f"""
                    MATCH (a {{id:$source_id}}), (b {{id:$target_id}})
                    MERGE (a)-[r:{label}]->(b)
                    SET r += $props
            """,
                source_id=relationship.source_extraction_id,
                target_id=relationship.target_extraction_id,
                props=props,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create relationship {e}")
            return False

    def create_paper_connections(
        self, tx, paper: Paper, extractions: List[str]
    ) -> bool:
        """
        Creates the paper and connect the papers with its extractions
        Args:
            tx: default way to perform transaction
            paper[Paper]: Paper object with its details
            extractions[List(str)]: list of extraction ids
        Returns:
            True if paper and its connections are created successfully
        """
        # create the paper node
        try:
            logger.info("Creating paper link")
            label = paper.paper_id
            props = {
                "main_theme": paper.main_theme,
                "key_contributions": paper.key_contributions,
                "study_location": paper.study_location,
                "study_period": paper.study_period,
                "primary_methods": paper.primary_methods,
            }

            tx.run(
                f"MERGE (n:{label} {{id:$id}}) SET n+= $props", id=label, props=props
            )

            for ex in extractions:
                tx.run(
                    f"""
                        MATCH (a {{id:$paper_id}}), (b {{id: $extraction_id}})
                        MERGE (b)-[r:{'belongs_to'}]->(a)
                    """,
                    paper_id=paper.paper_id,
                    extraction_id=ex,
                )
            logger.info("Success: Created paper link")
            return True
        except Exception as e:
            logger.error(f"Failed to create paper link {e}")
            return False

    def create_knowledge_graph(self, file_path: str) -> None:
        """
        Create knowledge graph from your data.

        Args:
            file_path(str): full file path(.json) from where to extract the entities and relationships
        Returns:
            None
        """
        try:
            logger.info(f"Creating knoweldge graph for {file_path.split('/')[-1]}")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            paper_id = data["paper_id"]
            paper = data["paper_summary"]
            paper["paper_id"] = paper_id

            extractions = (
                []
            )  # collection of all the extraction id so that they can be linked back to the paper

            nodes = data["extractions"]
            edges = data["relationships"]

            with self.driver.session() as session:
                for node in nodes:
                    N = Node(**node)
                    extractions.append(N.extraction_id)
                    session.execute_write(self.create_node, N)

                # logger.info(f"Success created nodes {len(nodes)}")

                for edge in edges:
                    E = Relationship(**edge)
                    session.execute_write(self.create_relationship, E)

                # logger.info(f"Success created edges{len(edges)}")

                session.execute_write(
                    self.create_paper_connections, Paper(**paper), extractions
                )
                return
        except Exception as e:
            logger.error(f"Failed to create knowledge graph {e}")
            return

    def retrieve_neighbors(self, nodes: List[str]):
        """
        Given nodes return all of this neighbors with their relationships
        Args:
            nodes(List[str]): Pid_EXT_id of the nodes to extract the neighbors an relationships of

        Returns:
            List of all the nodes, papers and relationships
        """
        try:
            logger.info("Retrieving Neighbors")
            final_output = []
            with self.driver.session() as session:
                for node in nodes:
                    print("Finding neighbors for", node)
                    output = {"Record": []}
                    cypher_self = f"MATCH (node) WHERE node.id='{node}' RETURN node"
                    # params = {"node_id": node}
                    # result = session.run(Query(cypher_self, params))
                    result = session.run(cypher_self)
                    # print('For Node the number of results is ',len(result))
                    for record in result:

                        content = record["node"]._properties["content"]
                        evidence = record["node"]._properties["evidence"]
                        output["Node"] = {"content": content, "evidence": evidence}

                    cypher_other = f"MATCH (node)-[relationship]-(neighbor) WHERE node.id ='{node}' RETURN relationship, neighbor"
                    # print('Running Cypher: ', cypher_other)
                    params = {"node_id": node}
                    # result = session.run(Query(cypher_other, params))
                    result = session.run(cypher_other)
                    # print(f"Got cypher results {cypher_other}")

                    for record in result:
                        rec = {}
                        relationship = record["relationship"]
                        neighbour = record["neighbor"]
                        if relationship:
                            if relationship.type == "belongs_to":
                                pass
                            else:
                                rel_type = relationship._properties["type"]
                                rel_evd = relationship._properties["evidence"]
                                rel_des = relationship._properties["description"]
                                rec["Relationship"] = {
                                    "Type": rel_type,
                                    "Evidence": rel_evd,
                                    "Description": rel_des,
                                }

                        if neighbour:
                            if relationship.type == "belongs_to":
                                if "Paper" not in output.keys():
                                    paper_theme = neighbour._properties["main_theme"]
                                    paper_key_contr = neighbour._properties[
                                        "key_contributions"
                                    ]
                                    paper_prim_meth = neighbour._properties[
                                        "primary_methods"
                                    ]
                                    paper_id = neighbour._properties["id"]
                                    output["Paper"] = {
                                        "main_theme": paper_theme,
                                        "Key_contributions": paper_key_contr,
                                        "paper_prim_meth": paper_prim_meth,
                                        "paper_id": paper_id,
                                    }
                                pass
                            else:
                                nei_evd = neighbour._properties["evidence"]
                                nei_cont = neighbour._properties["content"]
                                rec["Neighbour"] = {
                                    "Evidence": nei_evd,
                                    "Content": nei_cont,
                                }
                        output["Record"].append(rec)
                    final_output.append(output)

            logger.info(f"Successfully extracted {len(final_output)} neighbors")
            return final_output
        except Exception as e:
            logger.error(f"Failed to retrieve nodes {e}")
            return []

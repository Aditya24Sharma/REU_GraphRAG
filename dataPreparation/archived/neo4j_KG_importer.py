import json
import os
import logging
from typing import Dict, List, Any
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, TransientError
import time

from txt_to_json import convert_txt_to_json


class Neo4jKnowledgeGraphImporter:
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j database URI (e.g., "bolt://localhost:7687")
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Setup logging configuration"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def create_indexes(self):
        """Create indexes for better performance"""
        indexes = [
            "CREATE INDEX paper_id_index IF NOT EXISTS FOR (p:Paper) ON (p.paper_id)",
            "CREATE INDEX extraction_id_index IF NOT EXISTS FOR (e:Extraction) ON (e.extraction_id)",
            "CREATE INDEX relationship_id_index IF NOT EXISTS FOR ()-[r]-() ON (r.relationship_id)",
            "CREATE INDEX first_level_class_index IF NOT EXISTS FOR (c:FirstLevelClass) ON (c.name)",
            "CREATE INDEX second_level_class_index IF NOT EXISTS FOR (c:SecondLevelClass) ON (c.name)",
            "CREATE FULLTEXT INDEX extraction_content_index IF NOT EXISTS FOR (e:Extraction) ON EACH [e.extracted_content, e.supporting_evidence]"
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    self.logger.info(f"Created index: {index_query.split()[2]}")
                except Exception as e:
                    self.logger.warning(f"Index creation failed or already exists: {e}")
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            self.logger.info("Database cleared")
    
    def create_paper_node(self, session, paper_data: Dict[str, Any]):
        """Create paper node with summary information"""
        paper_summary = paper_data.get('paper_summary', {})
        extraction_summary = paper_data.get('extraction_summary', {})
        
        query = """
        MERGE (p:Paper {paper_id: $paper_id})
        SET p.main_theme = $main_theme,
            p.study_location = $study_location,
            p.study_period = $study_period,
            p.primary_methods = $primary_methods,
            p.key_contributions = $key_contributions,
            p.total_extractions = $total_extractions,
            p.classes_covered = $classes_covered,
            p.relationships_identified = $relationships_identified,
            p.confidence_average = $confidence_average,
            p.created_timestamp = timestamp()
        RETURN p
        """
        
        parameters = {
            'paper_id': paper_data.get('paper_id'),
            'main_theme': paper_summary.get('main_theme'),
            'study_location': paper_summary.get('study_location'),
            'study_period': paper_summary.get('study_period'),
            'primary_methods': paper_summary.get('primary_methods', []),
            'key_contributions': paper_summary.get('key_contributions', []),
            'total_extractions': extraction_summary.get('total_extractions', 0),
            'classes_covered': extraction_summary.get('classes_covered', 0),
            'relationships_identified': extraction_summary.get('relationships_identified', 0),
            'confidence_average': extraction_summary.get('confidence_average', 0.0)
        }
        
        result = session.run(query, parameters)
        return result.single()
    
    def create_classification_nodes(self, session, first_level: str, second_level: str):
        """Create hierarchical classification nodes"""
        query = """
        MERGE (flc:FirstLevelClass {name: $first_level})
        MERGE (slc:SecondLevelClass {name: $second_level})
        MERGE (flc)-[:HAS_SUBCLASS]->(slc)
        RETURN flc, slc
        """
        
        return session.run(query, {
            'first_level': first_level,
            'second_level': second_level
        })
    
    def create_extraction_node(self, session, paper_id: str, extraction: Dict[str, Any]):
        """Create extraction node with all properties and relationships"""
        context = extraction.get('context', {})
        quant_data = extraction.get('quantitative_data', {})
        
        # Create extraction node
        extraction_query = """
        MATCH (p:Paper {paper_id: $paper_id})
        MERGE (flc:FirstLevelClass {name: $first_level_class})
        MERGE (slc:SecondLevelClass {name: $second_level_class})
        MERGE (flc)-[:HAS_SUBCLASS]->(slc)
        
        CREATE (e:Extraction {
            extraction_id: $extraction_id,
            extracted_content: $extracted_content,
            supporting_evidence: $supporting_evidence,
            confidence_score: $confidence_score,
            keywords: $keywords,
            section: $section,
            subsection: $subsection,
            paragraph_position: $paragraph_position,
            page_number: $page_number,
            quantitative_values: $quant_values,
            quantitative_units: $quant_units,
            statistical_significance: $statistical_significance,
            created_timestamp: timestamp()
        })
        
        CREATE (p)-[:CONTAINS]->(e)
        CREATE (e)-[:CLASSIFIED_AS]->(flc)
        CREATE (e)-[:SPECIFICALLY_CLASSIFIED_AS]->(slc)
        
        RETURN e
        """
        
        parameters = {
            'paper_id': paper_id,
            'extraction_id': extraction.get('extraction_id'),
            'first_level_class': extraction.get('first_level_class'),
            'second_level_class': extraction.get('second_level_class'),
            'extracted_content': extraction.get('extracted_content'),
            'supporting_evidence': extraction.get('supporting_evidence'),
            'confidence_score': extraction.get('confidence_score', 0.0),
            'keywords': extraction.get('keywords', []),
            'section': context.get('section'),
            'subsection': context.get('subsection'),
            'paragraph_position': context.get('paragraph_position'),
            'page_number': context.get('page_number'),
            'quant_values': quant_data.get('values', []),
            'quant_units': quant_data.get('units', []),
            'statistical_significance': quant_data.get('statistical_significance')
        }
        
        return session.run(extraction_query, parameters)
    
    def create_relationship(self, session, relationship: Dict[str, Any]):
        """Create relationship between extractions"""
        query = """
        MATCH (source:Extraction {extraction_id: $source_id})
        MATCH (target:Extraction {extraction_id: $target_id})
        
        CALL apoc.create.relationship(source, $relationship_type, {
            relationship_id: $relationship_id,
            description: $description,
            confidence_score: $confidence_score,
            supporting_evidence: $supporting_evidence,
            created_timestamp: timestamp()
        }, target) YIELD rel
        
        RETURN rel
        """
        
        # Fallback query if APOC is not available
        fallback_query = """
        MATCH (source:Extraction {extraction_id: $source_id})
        MATCH (target:Extraction {extraction_id: $target_id})
        
        CREATE (source)-[r:RELATED_TO {
            relationship_id: $relationship_id,
            relationship_type: $relationship_type,
            description: $description,
            confidence_score: $confidence_score,
            supporting_evidence: $supporting_evidence,
            created_timestamp: timestamp()
        }]->(target)
        
        RETURN r
        """
        
        parameters = {
            'source_id': relationship.get('source_extraction_id'),
            'target_id': relationship.get('target_extraction_id'),
            'relationship_type': relationship.get('relationship_type', 'RELATED_TO').upper().replace(' ', '_'),
            'relationship_id': relationship.get('relationship_id'),
            'description': relationship.get('relationship_description'),
            'confidence_score': relationship.get('confidence_score', 0.0),
            'supporting_evidence': relationship.get('supporting_evidence')
        }
        
        try:
            # Try with dynamic relationship type first
            return session.run(query, parameters)
        except Exception as e:
            self.logger.warning(f"APOC not available, using fallback: {e}")
            return session.run(fallback_query, parameters)
    
    def import_paper_data(self, paper_data: Dict[str, Any]):
        """Import a complete paper with all extractions and relationships"""
        paper_id = paper_data.get('paper_id') or ""
        
        with self.driver.session() as session:
            try:
                # Create paper node
                self.logger.info(f"Creating paper node: {paper_id}")
                self.create_paper_node(session, paper_data)
                
                # Create extraction nodes
                extractions = paper_data.get('extractions', [])
                self.logger.info(f"Creating {len(extractions)} extraction nodes")
                
                for extraction in extractions:
                    self.create_extraction_node(session, paper_id, extraction)
                
                # Create relationships
                relationships = paper_data.get('relationships', [])
                self.logger.info(f"Creating {len(relationships)} relationships")
                
                for relationship in relationships:
                    try:
                        self.create_relationship(session, relationship)
                    except Exception as e:
                        self.logger.error(f"Failed to create relationship {relationship.get('relationship_id')}: {e}")
                
                self.logger.info(f"Successfully imported paper: {paper_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to import paper {paper_id}: {e}")
                raise
    
    def import_from_json_file(self, file_path: str):
        """Import data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            if isinstance(data, list):
                # Multiple papers
                for paper_data in data:
                    self.import_paper_data(paper_data)
            else:
                # Single paper
                self.import_paper_data(data)
                
        except Exception as e:
            self.logger.error(f"Failed to import from file {file_path}: {e}")
            raise
    
    def import_from_json_string(self, json_string: str):
        """Import data from JSON string"""
        try:
            data = json.loads(json_string)
            
            if isinstance(data, list):
                for paper_data in data:
                    self.import_paper_data(paper_data)
            else:
                self.import_paper_data(data)
                
        except Exception as e:
            self.logger.error(f"Failed to import from JSON string: {e}")
            raise
    
    def get_graph_statistics(self):
        """Get basic statistics about the imported graph"""
        queries = {
            'papers': "MATCH (p:Paper) RETURN count(p) as count",
            'extractions': "MATCH (e:Extraction) RETURN count(e) as count",
            'relationships': "MATCH ()-[r]->() WHERE r.relationship_id IS NOT NULL RETURN count(r) as count",
            'first_level_classes': "MATCH (flc:FirstLevelClass) RETURN count(flc) as count",
            'second_level_classes': "MATCH (slc:SecondLevelClass) RETURN count(slc) as count"
        }
        
        stats = {}
        with self.driver.session() as session:
            for name, query in queries.items():
                result = session.run(query)
                stats[name] = result.single()['count']
        
        return stats


# Example usage
def main():
    # Neo4j connection parameters
    NEO4J_URI = "neo4j+s://cd0249a9.databases.neo4j.io"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD ="BZfXOLWT_K5plBV68ieeD8RKlplS_bADuJhT7re042I"
    
    # Initialize importer
    importer = Neo4jKnowledgeGraphImporter(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    file_path = '/home/aditya/REU/Code/Graph_RAG/dataPreparation/ontology_outputs_json/v1/mandli-et-al-coupling-coastal-and-hydrologic-models-through-next-generation-national-water-model-framework.json'
    try:
        # Create indexes
        importer.create_indexes()
        
        # Import from JSON file
        importer.import_from_json_file(file_path=file_path)
        
        # Or import from JSON string
        # json_data = '''{"paper_id": "example", ...}'''
        # importer.import_from_json_string(json_data)
        
        # Get statistics
        stats = importer.get_graph_statistics()
        print("Graph Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Import failed: {e}")
    finally:
        importer.close()


if __name__ == "__main__":
    main()
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
import openai
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class GraphSchema(BaseModel):
    node_labels: List[str]
    relationship_types: List[str]
    node_properties: List[str]
    relationship_properties: List[str]
    
class TSSchema(BaseModel):
    primary_relationships: List[str]
    max_hops : str
    include_limitations: str

class QueryAnalyzerSchema(BaseModel):
    query_intent:str
    key_entities: List[str]
    starting_nodes: List[str]
    traversal_strategy: TSSchema
    complexity: str

class GraphContext(BaseModel):
    nodes: List[Dict]
    relationships: List[Dict]
    subgraph_summary: str
    confidence_scores: List[float]

class QueryAnalyzer:
    """Node 1: Analyzes user query to determine intent and entities"""
    
    def __init__(self, llm_client, graph_schema):
        self.llm = llm_client
        self.graph_schema = graph_schema
    
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """Analyze query to extract intent, entities, and query type"""
        
        # analysis_prompt = f"""
        # Analyze this user query for a knowledge graph search:
        # Query: "{user_query}"
        
        # Extract:
        # 1. Query Intent (factual, exploratory, comparative, causal)
        # 2. Key Entities (specific terms to search for)
        # 3. Query Type (single-hop, multi-hop, path-finding, aggregation)
        # 4. Graph Traversal Depth (1-3 hops recommended)
        # 5. Required Confidence Level (1-10)
        
        # Return as JSON.
        # """

        analysis_prompt = f"""
                You are analyzing a user query for a hydrology research knowledge graph. Your task is to determine the optimal traversal strategy to retrieve relevant information from scientific papers.

                GRAPH SCHEMA:
                {self.graph_schema}

                ANALYSIS STEPS:

                1. CLASSIFY QUERY INTENT:
                - Methodological: seeking methods, models, experimental designs
                - Conceptual: understanding processes, mechanisms, theory
                - Empirical: looking for results, findings, performance data
                - Application: practical use, management, policy implications
                - Literature: comparative analysis, research trends, gaps
                - Meta-research: limitations, uncertainties, future directions

                2. IDENTIFY KEY ENTITIES:
                - Hydrological processes (runoff, infiltration, evapotranspiration, etc.)
                - Methods/models mentioned
                - Geographic/temporal aspects
                - Performance metrics or indicators

                3. DETERMINE STARTING NODES:
                - Process queries → Hydrological_Process_* nodes
                - Method queries → Research_Methodology_*, Models_Methods_* nodes
                - Results queries → Results_Findings_* nodes
                - Application queries → Applications_Management_* nodes

                4. PLAN TRAVERSAL STRATEGY:
                - 1-hop: Direct concept matches
                - 2-hop: Related processes, methods, validation
                - 3-hop: Broader context, limitations, applications
                - Key relationships: causes→influences→affects, validates→supports→confirms

                5. PRIORITIZE INFORMATION:
                - High confidence scores
                - Validated results (follows 'validates', 'supports' relationships)
                - Include uncertainties and limitations for balance

                OUTPUT FORMAT:
                Return a JSON object with:
                {{
                "query_intent": "methodological|conceptual|empirical|application|literature|meta-research",
                "key_entities": ["entity1", "entity2"],
                "starting_nodes": ["primary_node_types"],
                "traversal_strategy": {{
                    "primary_relationships": ["relationship_types"],
                    "max_hops": (string number from 1 to 3),
                    "include_limitations": (string true or false)
                }},
                "complexity": "simple|moderate|complex",
                }}

                QUERY TO ANALYZE: 
                """
        
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": analysis_prompt },
                      {"role": "user", "content": user_query}],
            temperature=0.1
        )
        print(type(response.choices[0].message.content)) 
        return json.loads(response.choices[0].message.content)

class CypherGenerator:
    """Node 2: Converts analyzed query into optimized Cypher queries"""
    
    def __init__(self, llm_client, graph_schema: GraphSchema):
        self.llm = llm_client
        self.graph_schema = graph_schema
    
    def generate_cypher(self, query_analysis: QueryAnalyzerSchema) -> List[str]:
        """Generate multiple Cypher queries based on analysis"""
        
        # schema_context = f"""
        # Graph Schema:
        # - Node Labels: {self.graph_schema.node_labels}
        # - Relationship Types: {self.graph_schema.relationship_types}
        # - Node Properties: {self.graph_schema.node_properties}
        # - Relationship Properties:{self.graph_schema.relationship_properties} 
        # """
        
        # cypher_prompt = f"""
        # {schema_context}
        
        # Query Analysis: {json.dumps(query_analysis, indent=2)}
        
        # Generate 2-3 Cypher queries that could answer this query:
        # 1. Primary query (most direct path)
        # 2. Backup query (alternative approach)
        # 3. Exploratory query (broader context)
        
        # Consider:
        # - Confidence score filtering
        # - Proper LIMIT clauses
        # - Efficient path traversal
        
        # Return as JSON array of query objects with 'query' and 'purpose' fields.
        # """

        cypher_generation_prompt = f"""
            You are a Neo4j Cypher query generator for a hydrology research knowledge graph. enerate 1 to 3 Cypher queries depending on the complexity of the user query. If multiple plausible paths or interpretations exist, include distinct queries that cover those. Use varied traversal strategies, start nodes, or relationship chains where applicable. 
            GRAPH SCHEMA:
            {self.graph_schema}

            QUERY ANALYSIS RESULTS:
            Query Intent: {query_analysis.query_intent}
            Key Entities: {query_analysis.key_entities}
            Starting Nodes: {query_analysis.starting_nodes}
            Primary Relationships: {query_analysis.traversal_strategy.primary_relationships}
            Max Hops: {query_analysis.traversal_strategy.max_hops}
            Include Limitations: {query_analysis.traversal_strategy.include_limitations}
            Complexity: {query_analysis.complexity}

            CYPHER GENERATION RULES:

            1. STARTING POINT:
            - Use MATCH clauses for the starting node types
            - Filter nodes using WHERE clauses with keywords/content matching
            - Use CONTAINS or regex for flexible text matching

            2. TRAVERSAL STRATEGY:
            - For simple queries (1-2 hops): Direct MATCH patterns
            - For moderate queries (2-3 hops): Chained MATCH or variable-length relationships
            - For complex queries: Multiple MATCH clauses with UNION if needed

            3. TEXT MATCHING:
            - Use: WHERE n.content CONTAINS 'keyword' OR n.keywords CONTAINS 'keyword'
            - For multiple entities: Use OR conditions or separate MATCH clauses
            - Case-insensitive: toLower(n.content) CONTAINS toLower('keyword')

            4. RELATIONSHIP TRAVERSAL:
            - Use OPTIONAL MATCH for relationships to avoid empty results
            - Direct: OPTIONAL MATCH (n1)-[r:RELATIONSHIP_TYPE]->(n2)
            - Variable length: OPTIONAL MATCH (n1)-[r:RELATIONSHIP_TYPE*1..{query_analysis.traversal_strategy.max_hops}]->(n2)
            - Multiple types: OPTIONAL MATCH (n1)-[r:TYPE1|TYPE2|TYPE3]->(n2)
            - Fallback: If specific relationships fail, use generic traversal: (n1)-[r*1..{query_analysis.traversal_strategy.max_hops}]->(n2)

            5. RESULT COLLECTION:
            - Return relevant nodes and their properties
            - Include relationship information when useful
            - Order by relevance (confidence_score DESC)
            - Limit results appropriately (LIMIT 20-50)

            6. LIMITATIONS HANDLING:
            - If include_limitations=true, add OPTIONAL MATCH for Uncertainty_Limitations nodes
            - Connect limitations using 'relates_to' or similar relationships

            EXAMPLE PATTERNS:

            Simple Query:
            ```
            MATCH (n:NodeType)
            WHERE toLower(n.content) CONTAINS toLower('keyword') 
            OR toLower(n.keywords) CONTAINS toLower('keyword')
            RETURN n.content, n.evidence, n.confidence_score
            ORDER BY n.confidence_score DESC
            LIMIT 20
            ```

            Moderate Query with Relationships:
            ```
            MATCH path = (start:StartNodeType)-[:RELATIONSHIP_TYPE*1..2]->(related)
            WHERE toLower(start.content) CONTAINS toLower('keyword')
            WITH start, related, relationships(path)[0] AS rel
            RETURN start.content, type(rel) AS relationship_type, related.content, rel.description
            ORDER BY start.confidence_score DESC
            LIMIT 30
            ```

            Complex Query with Multiple Paths:
            ```
            MATCH (start:StartType)
            WHERE toLower(start.content) CONTAINS toLower('keyword1')
            MATCH path1 = (start)-[:REL_TYPE1]->(intermediate)
            MATCH path2 = (intermediate)-[:REL_TYPE2]->(end)
            OPTIONAL MATCH (end)-[:relates_to]->(limitations:Uncertainty_Limitations)
            WITH start, intermediate, end, limitations,
                relationships(path1)[0] AS rel1,
                relationships(path2)[0] AS rel2
            RETURN 
            start.content, 
            intermediate.content, 
            end.content, 
            limitations.content AS limitations,
            type(rel1) AS rel1_type,
            type(rel2) AS rel2_type
            ORDER BY start.confidence_score DESC
            LIMIT 25
            ```

            CURRENT TASK:
            Generate a Cypher query based on the analysis results above. Focus on:
            1. Matching the starting node types with appropriate keyword filtering
            2. Following the specified relationship paths for the given number of hops
            3. Including limitations if requested
            4. Returning comprehensive but focused results

            OUTPUT: Provide only the Cypher query, no additional explanation.
            """

        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": cypher_generation_prompt}],
            temperature=0.2
        )
        print(response.choices[0].message.content) 
        return 

class GraphRetriever:
    """Node 3: Executes Cypher queries and retrieves graph data"""
    
    def __init__(self, neo4j_uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
    
    def execute_queries(self, cypher_queries: List[Dict]) -> GraphContext:
        """Execute multiple queries and merge results"""
        
        all_nodes = []
        all_relationships = []
        all_confidences = []
        
        with self.driver.session() as session:
            for query_obj in cypher_queries:
                try:
                    result = session.run(query_obj['query'])
                    nodes, rels, confidences = self._process_result(result)
                    all_nodes.extend(nodes)
                    all_relationships.extend(rels)
                    all_confidences.extend(confidences)
                except Exception as e:
                    print(f"Query failed: {query_obj['purpose']} - {e}")
                    continue
        
        # Remove duplicates and rank by confidence
        unique_nodes = self._deduplicate_nodes(all_nodes)
        unique_rels = self._deduplicate_relationships(all_relationships)
        
        return GraphContext(
            nodes=unique_nodes,
            relationships=unique_rels,
            subgraph_summary=self._create_summary(unique_nodes, unique_rels),
            confidence_scores=all_confidences
        )
    
    def _process_result(self, result):
        """Process Neo4j result into structured data"""
        nodes = []
        relationships = []
        confidences = []
        
        for record in result:
            for key, value in record.items():
                if hasattr(value, 'labels'):  # Node
                    node_data = dict(value)
                    node_data['labels'] = list(value.labels)
                    nodes.append(node_data)
                    if 'confidence_score' in node_data:
                        confidences.append(node_data['confidence_score'])
                        
                elif hasattr(value, 'type'):  # Relationship
                    rel_data = dict(value)
                    rel_data['type'] = value.type
                    relationships.append(rel_data)
                    if 'confidence_score' in rel_data:
                        confidences.append(rel_data['confidence_score'])
        
        return nodes, relationships, confidences
    
    def _deduplicate_nodes(self, nodes: List[Dict]) -> List[Dict]:
        """Remove duplicate nodes based on extraction_id"""
        seen = set()
        unique = []
        for node in nodes:
            node_id = node.get('extraction_id')
            if node_id and node_id not in seen:
                seen.add(node_id)
                unique.append(node)
        return unique
    
    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Remove duplicate relationships"""
        seen = set()
        unique = []
        for rel in relationships:
            rel_id = rel.get('relationship_id')
            if rel_id and rel_id not in seen:
                seen.add(rel_id)
                unique.append(rel)
        return unique
    
    def _create_summary(self, nodes: List[Dict], relationships: List[Dict]) -> str:
        """Create a summary of the retrieved subgraph"""
        return f"Retrieved {len(nodes)} nodes and {len(relationships)} relationships"

class ContextFormatter:
    """Node 4: Formats graph data for LLM consumption"""
    
    def format_context(self, graph_context: GraphContext, max_tokens: int = 4000) -> str:
        """Format graph data into readable context for LLM"""
        
        context_parts = []
        
        # Add summary
        context_parts.append(f"Graph Context Summary: {graph_context.subgraph_summary}")
        # context_parts.append(f"Average Confidence: {sum(graph_context.confidence_scores)/len(graph_context.confidence_scores):.2f}")
        
        # Add high-confidence nodes first
        sorted_nodes = sorted(graph_context.nodes, 
                            key=lambda x: x.get('confidence_score', 0), 
                            reverse=True)
        
        context_parts.append("\n=== KEY ENTITIES ===")
        for node in sorted_nodes[:10]:  # Top 10 nodes
            content = node.get('extracted_content', node.get('content', 'No content'))
            confidence = node.get('confidence_score', 'N/A')
            context_parts.append(f"• {content} (Confidence: {confidence})")
        
        # Add relationships
        context_parts.append("\n=== RELATIONSHIPS ===")
        for rel in graph_context.relationships[:10]:  # Top 10 relationships
            rel_type = rel.get('relationship_type', rel.get('type', 'RELATED'))
            description = rel.get('relationship_description', 'No description')
            confidence = rel.get('confidence_score', 'N/A')
            context_parts.append(f"• {rel_type}: {description} (Confidence: {confidence})")
        
        # Truncate if too long
        full_context = "\n".join(context_parts)
        if len(full_context) > max_tokens * 4:  # Rough token estimation
            return full_context[:max_tokens * 4] + "...\n[Context truncated]"
        
        return full_context

class ResponseGenerator:
    """Node 5: Generates final response using formatted context"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def generate_response(self, user_query: str, formatted_context: str) -> str:
        """Generate final response using graph context"""
        
        response_prompt = f"""
        You are a knowledgebase assistant. Answer the user's question using the provided graph context.
        
        User Question: {user_query}
        
        Graph Context:
        {formatted_context}
        
        Instructions:
        1. Answer directly and concisely
        2. Cite confidence scores when making claims
        3. Mention if information has low confidence
        4. If context is insufficient, say so clearly
        5. Use the relationship information to provide connected insights
        
        Answer:
        """
        
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": response_prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content

class GraphRAGPipeline:
    """Main orchestrator that connects all nodes"""
    
    def __init__(self, neo4j_uri: str, neo4j_username: str, neo4j_password: str, 
                 openai_api_key: str, graph_schema:GraphSchema):
        
        # Initialize OpenAI client
        openai.api_key = openai_api_key
        self.llm = openai
        
        # Initialize all nodes
        self.query_analyzer = QueryAnalyzer(self.llm, graph_schema)
        self.cypher_generator = CypherGenerator(self.llm, graph_schema)
        self.graph_retriever = GraphRetriever(neo4j_uri, neo4j_username, neo4j_password)
        self.context_formatter = ContextFormatter()
        self.response_generator = ResponseGenerator(self.llm)
    
    def query(self, user_query: str) -> Dict[str, Any]:
        """Execute full GraphRAG pipeline"""
        
        # Step 1: Analyze query
        print("🔍 Analyzing query...")
        query_analysis = self.query_analyzer.analyze_query(user_query)
        print('Query Analyzed: ', query_analysis)

        return{} 
    
        # Step 2: Generate Cypher queries
        print("⚡ Generating Cypher queries...")
        cypher_queries = self.cypher_generator.generate_cypher(QueryAnalyzerSchema(**query_analysis))
        print('Cypher Queries: ', cypher_queries)

        # Step 3: Retrieve graph data
        print("📊 Retrieving graph data...")
        graph_context = self.graph_retriever.execute_queries(cypher_queries)
        print('Graph Context: ', graph_context)

        # Step 4: Format context
        print("📝 Formatting context...")
        formatted_context = self.context_formatter.format_context(graph_context)
        print('Formatted context: ', formatted_context)

        # Step 5: Generate response
        print("🤖 Generating response...")
        final_response = self.response_generator.generate_response(user_query, formatted_context)
        print('Final_response', final_response)

        return {
            "response": final_response,
            "query_analysis": query_analysis,
            "cypher_queries": cypher_queries,
            "graph_context": graph_context,
            "formatted_context": formatted_context
        }

# Example usage
if __name__ == "__main__":
    # Define your graph schema
    schema_file = './graph_schema.json'
    with open(schema_file, 'r') as f:
        schema_json = json.load(f) 
    graph_schema = schema_json
    # Initialize pipeline
    pipeline = GraphRAGPipeline(
        neo4j_uri=os.getenv('NEO4J_URI'),
        neo4j_username=os.getenv('NEO4J_USERNAME'),
        neo4j_password=os.getenv('NEO4J_PASSWORD'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        graph_schema=GraphSchema(**graph_schema)
    )
    
    # Query the system
    result = pipeline.query("What are the research process in this research?")
    print("\n" + "="*50)
    print("FINAL RESPONSE:")
    print("="*50)
    print(result["response"])
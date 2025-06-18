# Smart GraphRAG Retrieval System
# Converts user queries to optimized Cypher queries using your existing schema

class HydrologyGraphRAG:
    def __init__(self):
        # Your existing ontology structure
        self.first_level_classes = [
            "Study-Location", "Research-Methodology", "Data-Analysis", 
            "Model-Development", "Results-Findings", "Environmental-Impact",
            "Technology-Tools", "Temporal-Analysis", "Validation-Verification"
        ]
        
        self.second_level_classes = {
            "Study-Location": ["watershed-characteristics", "geographic-scope", "climate-conditions"],
            "Research-Methodology": ["data-collection-methods", "experimental-design", "sampling-strategy"],
            "Data-Analysis": ["statistical-methods", "preprocessing-techniques", "quality-assessment"],
            "Model-Development": ["model-selection", "parameter-estimation", "calibration-approach"],
            "Results-Findings": ["performance-metrics", "key-outcomes", "comparative-analysis"],
            "Environmental-Impact": ["ecological-effects", "water-quality-impact", "sustainability-assessment"],
            "Technology-Tools": ["software-platforms", "measurement-instruments", "computational-resources"],
            "Temporal-Analysis": ["time-series-analysis", "trend-identification", "seasonal-patterns"],
            "Validation-Verification": ["model-validation", "uncertainty-analysis", "sensitivity-testing"]
        }
        
        self.relationship_types = [
            "validates", "uses", "compares", "builds_on", "contradicts", 
            "supports", "extends", "applies", "measures", "analyzes"
        ]
    
    def generate_cypher_query(self, user_query: str) -> str:
        """
        Convert natural language query to Cypher using ontology knowledge
        """
        
        # Query analysis prompt for LLM
        analysis_prompt = f"""
        Given this user query: "{user_query}"
        
        Available first-level classes: {self.first_level_classes}
        Available second-level classes: {self.second_level_classes}
        Available relationships: {self.relationship_types}
        
        Generate an optimized Cypher query that:
        1. Identifies relevant classes from the ontology
        2. Uses appropriate relationship types
        3. Filters based on user intent
        4. Returns comprehensive results
        
        Graph Schema:
        - (paper:Paper) contains extractions
        - (extraction:Extraction) has first_level_class, second_level_class, content
        - (extraction)-[rel:RELATIONSHIP_TYPE]->(extraction)
        
        Return only the Cypher query, optimized for performance.
        """
        
        return self.llm_generate_cypher(analysis_prompt)
    
    def execute_smart_retrieval(self, user_query: str):
        """
        Complete retrieval pipeline
        """
        # Step 1: Generate optimized Cypher
        cypher_query = self.generate_cypher_query(user_query)
        
        # Step 2: Execute against graph database
        raw_results = self.execute_cypher(cypher_query)
        
        # Step 3: Post-process and rank results
        processed_results = self.rank_and_filter_results(raw_results, user_query)
        
        # Step 4: Generate contextual response
        response = self.generate_response(processed_results, user_query)
        
        return response

# Example Usage and Query Patterns

class QueryPatterns:
    """
    Common query patterns that work with your existing structure
    """
    
    @staticmethod
    def cross_paper_method_discovery():
        """Find papers using similar methodologies"""
        return """
        MATCH (p1:Paper)-[:CONTAINS]->(e1:Extraction {first_level_class: 'Research-Methodology'})
        MATCH (p2:Paper)-[:CONTAINS]->(e2:Extraction {first_level_class: 'Research-Methodology'})
        WHERE p1 <> p2 
        AND e1.second_level_class = e2.second_level_class
        AND e1.extracted_content CONTAINS $method_keyword
        RETURN p1, p2, e1, e2, 
               apoc.text.sorensenDiceSimilarity(e1.extracted_content, e2.extracted_content) as similarity
        ORDER BY similarity DESC
        """
    
    @staticmethod
    def location_based_research():
        """Find research in specific geographic areas"""
        return """
        MATCH (p:Paper)-[:CONTAINS]->(loc:Extraction {first_level_class: 'Study-Location'})
        WHERE loc.extracted_content CONTAINS $location_term
        OPTIONAL MATCH (p)-[:CONTAINS]->(method:Extraction {first_level_class: 'Research-Methodology'})
        OPTIONAL MATCH (p)-[:CONTAINS]->(results:Extraction {first_level_class: 'Results-Findings'})
        RETURN p, loc, collect(DISTINCT method) as methods, collect(DISTINCT results) as findings
        """
    
    @staticmethod
    def model_validation_chain():
        """Trace model development and validation"""
        return """
        MATCH (p:Paper)-[:CONTAINS]->(model:Extraction {first_level_class: 'Model-Development'})
        MATCH (p)-[:CONTAINS]->(validation:Extraction {first_level_class: 'Validation-Verification'})
        OPTIONAL MATCH (model)-[rel:validates|supports|extends]->(validation)
        RETURN p, model, validation, rel,
               p.year as publication_year
        ORDER BY publication_year DESC
        """
    
    @staticmethod
    def technology_evolution():
        """Track technology and tool usage over time"""
        return """
        MATCH (p:Paper)-[:CONTAINS]->(tech:Extraction {first_level_class: 'Technology-Tools'})
        WHERE tech.extracted_content CONTAINS $technology_term
        RETURN p.year, p.title, tech.extracted_content, tech.second_level_class
        ORDER BY p.year ASC
        """

# Smart Query Enhancement
class QueryEnhancer:
    """
    Enhances basic queries with domain knowledge
    """
    
    def enhance_with_synonyms(self, query: str) -> str:
        """Add hydrology domain synonyms"""
        synonyms = {
            "streamflow": ["discharge", "river flow", "water flow"],
            "rainfall": ["precipitation", "rain", "rainfall data"],
            "watershed": ["basin", "catchment", "drainage area"],
            "machine learning": ["ML", "artificial intelligence", "neural networks"]
        }
        # Expand query with synonyms
        enhanced_query = query
        for term, syns in synonyms.items():
            if term.lower() in query.lower():
                enhanced_query += f" OR {' OR '.join(syns)}"
        return enhanced_query
    
    def add_context_filters(self, base_query: str, user_preferences: dict) -> str:
        """Add user-specific filters"""
        filters = []
        
        if user_preferences.get("recent_only"):
            filters.append("p.year >= 2020")
        
        if user_preferences.get("high_confidence"):
            filters.append("extraction.confidence_score >= 8.0")
        
        if user_preferences.get("geographic_region"):
            region = user_preferences["geographic_region"]
            filters.append(f"loc.extracted_content CONTAINS '{region}'")
        
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)
            return base_query + "\n" + where_clause
        
        return base_query

# Example intelligent queries your system could handle:

example_queries = [
    {
        "user_input": "Show me machine learning applications in Amazon Basin",
        "generated_cypher": """
        MATCH (p:Paper)-[:CONTAINS]->(loc:Extraction {first_level_class: 'Study-Location'})
        MATCH (p)-[:CONTAINS]->(method:Extraction {first_level_class: 'Research-Methodology'})
        WHERE loc.extracted_content CONTAINS 'Amazon' 
        AND (method.extracted_content CONTAINS 'machine learning' 
             OR method.extracted_content CONTAINS 'neural network'
             OR method.extracted_content CONTAINS 'random forest')
        RETURN p, loc, method
        ORDER BY p.year DESC
        """
    },
    {
        "user_input": "What validation methods are used for SWAT model?",
        "generated_cypher": """
        MATCH (p:Paper)-[:CONTAINS]->(model:Extraction {first_level_class: 'Model-Development'})
        MATCH (p)-[:CONTAINS]->(validation:Extraction {first_level_class: 'Validation-Verification'})
        WHERE model.extracted_content CONTAINS 'SWAT'
        OPTIONAL MATCH (model)-[rel]->(validation)
        RETURN p, model, validation, type(rel) as relationship_type
        """
    }
]
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv


load_dotenv()

print(os.getenv)

neo4j_uri=os.getenv('NEO4J_URI')
neo4j_username=os.getenv('NEO4J_USERNAME')
neo4j_password=os.getenv('NEO4J_PASSWORD')
openai_api_key=os.getenv('OPENAI_API_KEY')

print('Type: ', type(neo4j_username))
print('Username: ', neo4j_username)
print('Password: ', neo4j_password )
driver = GraphDatabase.driver(uri=neo4j_uri, auth=(neo4j_username, neo4j_password))

cypher = 'MATCH (n:Research_Methodology_experimental_design)-[r]->(neighbor) RETURN n,r,neighbor LIMIT 5;'

with driver.session() as session:
    response = session.run(cypher)
    print(response)
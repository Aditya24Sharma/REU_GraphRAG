"""
Main entry point for the project
"""

import os
import json
import logging
from pathlib import Path

from utils import setup_logging, json_to_txt
from database import Neo4j, Chromadb
from llm import LLM

setup_logging(log_level="INFO")


logger = logging.getLogger(__name__)
logger.info("Application started")

if __name__ == "__main__":
    llm = LLM()
    neo4j = Neo4j()
    chromadb = Chromadb()
    #
    project_root = Path(__file__).parent
    # print(project_root)
    # print(type(project_root))
    #
    # # get the system prompt to extract the ontology from the files
    # sys_prompt_file_path = project_root / "kg_prompts" / "prompts" / "prompt_v2.txt"
    #
    # # file to extract the ontology from
    # file_path = "/home/aditya/REU/Code/Graph_RAG/structured/data/markdowns/Establishing_flood_thresholds_for_sea_level_rise_impact_communication.md"
    #
    # output_folder = project_root / "data" / "ontology_outputs" / "v3"
    # output_folder_json = project_root / "data" / "ontology_outputs_json" / "v3"
    #
    # llm.generate_ontology(
    #     file_name=file_path,
    #     system_prompt_file=str(sys_prompt_file_path),
    #     output_folder=str(output_folder),
    #     output_folder_json=str(output_folder_json),
    # )
    #
    # # sending all the file from ontology_output_json to be converted to knowledge graph
    # input_json_folder = project_root / "data" / "ontology_outputs_json" / "v3"

    # file_path = ""
    # for file in os.listdir(input_json_folder):
    # file = os.listdir(input_json_folder)[1]
    # file_path = os.path.join(input_json_folder, file)
    # neo4j.create_knowledge_graph(file_path=file_path)
    #
    # # Storing the extractions to Chroma
    # collection_name = "P001_002"
    # chromadb.store_to_db(
    #     input_json_folder=str(input_json_folder), collection_name=collection_name
    # )
    #
    # chromadb.delete_collection(collection_name="P001_002")

    # Querying
    while True:
        print("Type q to quit or type your query")
        query = input("Enter your query: ")
        if query == "q":
            break
        print(f"Available collecitons: {[c.name for c in chromadb.list_collections()]}")
        collection_name = input("Enter collection to serach in: ")

        # creating texts to be chunked
        similar_chunks = chromadb.retrieve_similar_chunks(
            query=query, collection_name=collection_name, top_k=8
        )
        # print('Similar chunks for the given query: ', similar_chunks),
        context = similar_chunks

        answer = llm.extract_relevant_ids(context=similar_chunks, query=query)
        print("Got answer: ", answer)

        if answer:
            context = neo4j.retrieve_neighbors(nodes=answer)

        print(llm.query_with_context(context=context, query=query))

    # for file in os.listdir(input_json_folder):
    #     file_path = os.path.join(input_json_folder, file)
    #     paper_id = ""
    #     with open(file_path, "r") as f:
    #         obj = json.load(f)
    #         paper_id = obj['paper_id']
    #     contents = json_to_txt(file_name=str(file_path))
    #
    #     total_chunks = []
    #     for idx, c in enumerate(contents):
    #         #since the text(c) is small we are not going to split the text into chunks
    #         chunk = {
    #             "chunk": c,
    #             "source": paper_id,
    #             "chunk_id": paper_id + str(idx)
    #         }
    #         total_chunks.append(chunk)
    #
    #     collection_name = 'P001_002'
    #     if chromadb.store_chunks(total_chunks, collection_name=collection_name):
    #         pass
    #

    # print("Successfully read file from", file_path)

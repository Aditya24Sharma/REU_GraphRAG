"""
Main entry point for the project
"""

import os
import json
import logging
from pathlib import Path

from utils import setup_logging
from database import Neo4j, Chromadb
from llm import LLM
from query import Query

setup_logging(log_level="INFO")


logger = logging.getLogger(__name__)
logger.info("Application started")

if __name__ == "__main__":
    llm = LLM()
    neo4j = Neo4j()
    chromadb = Chromadb()
    query = Query()
    #
    project_root = Path(__file__).parent
    # print(project_root)
    # print(type(project_root))
    #
    # # get the system prompt to extract the ontology from the files
    sys_prompt_file_path = project_root / "kg_prompts" / "prompts" / "prompt_v3.txt"
    #
    # # file to extract the ontology from
    # file_path = "/home/aditya/REU/Code/Graph_RAG/structured/data/markdowns/Establishing_flood_thresholds_for_sea_level_rise_impact_communication.md"

    # file_path = "/home/aditya/REU/Code/Graph_RAG/structured/data/markdowns/mandli_et_al_coupling_coastal_and_hydrologic_models_through_next_generation_national_water_model_framework.md"
    # file_path = "/home/aditya/REU/Code/Graph_RAG/structured/data/markdowns/Rapid_intensification_of_tropical_cyclones_in_the_Gulf_of_Mexico_is_more_likely_during_marine_heatwaves.md"

    # file_path = "/home/aditya/REU/Code/Graph_RAG/structured/data/markdowns/A_data_driven_framework_for_an_efficient_block_level_coastal_flood_risk_assessment.md"

    # file_path = "/home/aditya/REU/Code/Graph_RAG/structured/data/markdowns/Earth_s_Future___2024___Radfar___Global_Predictability_of_Marine_Heatwave_Induced_Rapid_Intensification_of_Tropical.md"
    # output_folder = project_root / "data" / "ontology_outputs" / "v3"
    # output_folder_json = project_root / "data" / "ontology_outputs_json" / "v3"

    # llm.generate_ontology(
    #     file_name=file_path,
    #     system_prompt_file=str(sys_prompt_file_path),
    #     output_folder=str(output_folder),
    #     output_folder_json=str(output_folder_json),
    # )

    # # sending all the file from ontology_output_json to be converted to knowledge graph
    # input_json_folder = project_root / "data" / "ontology_outputs_json" / "v3"
    # input_markdown_folder = project_root / "data" / "text_outputs"
    # input_json_file = (
    #     project_root
    #     / "data"
    #     / "ontology_outputs_json"
    #     / "v3"
    #     / "mandli_et_al_coupling_coastal_and_hydrologic_models_through_next_generation_national_water_model_framework.json"
    # )

    # STORING DATA
    input_json_folder = project_root / "data" / "ontology_outputs_json" / "v3"
    input_markdown_folder = project_root / "data" / "text_outputs"
    file_path = ""
    for file in os.listdir(input_json_folder):
        file_path = os.path.join(input_json_folder, file)
        neo4j.create_knowledge_graph(file_path=file_path)
        chromadb.store_json_to_db(input_file=file_path, collection_name="Graph")
    #
    for file in os.listdir(input_markdown_folder):
        # print(file)
        file_path = os.path.join(input_markdown_folder, file)
        chromadb.store_text_to_db(input_file=file_path, collection_name="Vector")

    # file = os.listdir(input_json_folder)[1]
    # file_path = os.path.join(input_json_folder, file)
    # neo4j.create_knowledge_graph(file_path=file_path)

    # Storing the extractions to Chroma
    # collection_name = "Graph"
    # chromadb.store_json_to_db(
    #     input_file=str(input_json_file), collection_name=collection_name
    # )

    # collection_name = "Vector"
    # chromadb.store_text_to_db(input_file=file_path, collection_name=collection_name)

    # chromadb.delete_collection(collection_name="Graph")
    # chromadb.delete_collection(collection_name="Vector")

    # Querying
    # while True:
    # print("Type q to quit or type your query")
    # user_query = input("Enter your query: ")
    # if user_query == "q":
    #     break
    # available_collections = [c.name for c in chromadb.list_collections()]
    # print(f"Available collecitons: {available_collections}")
    # collection_name = input("Enter collection to serach in: ")
    # answer = query.query(user_query=user_query, collection_name=collection_name)
    # print(answer)

    # revised_query = json.loads(llm.revise_query(user_query))
    #
    #        if collection_name.lower() == "both":
    #     overall_context = []
    #     for c in available_collections:
    #         similar_chunks = set()
    #         for query in revised_query:
    #             similar = chromadb.retrieve_similar_chunks(
    #                 query=query, collection_name=c, top_k=8
    #             )
    #             for s in similar:
    #                 similar_chunks.add(s)
    #         if c == "Graph":
    #             answer = llm.extract_relevant_ids(
    #                 context=list(similar_chunks), query=user_query
    #             )
    #             # print("Got answer: ", answer)
    #             context = [""]
    #             if answer:
    #                 context = neo4j.retrieve_neighbors(nodes=answer)
    #             overall_context.extend(context)
    #         else:
    #             overall_context.extend(list(similar_chunks))
    #     print(llm.query_with_context(context=overall_context, query=user_query))
    # else:
    #     similar_chunks = chromadb.retrieve_similar_chunks(
    #         query=user_query, collection_name=collection_name, top_k=8
    #     )
    #     if collection_name.lower() == "graph":
    #         answer = llm.extract_relevant_ids(
    #             context=similar_chunks, query=user_query
    #         )
    #         # print("Got answer: ", answer)
    #         context = [""]
    #         if answer:
    #             context = neo4j.retrieve_neighbors(nodes=answer)
    #         print(llm.query_with_context(context=context, query=user_query))
    #     else:
    #         print(llm.query_with_context(context=similar_chunks, query=user_query))

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

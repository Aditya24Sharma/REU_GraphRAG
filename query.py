from vectorRAG import generate_response, retrieve_similar_chunks, listCollection, get_relevant_ext_ids
import json
import os
from dataPreparation import text_chunking
from typing import List
from graphRAG.main import CypherGenerator
import openai


collection_name = 'mandil_entitites_db'

query = ''

def text_from_json(file_name = str)->List[str]:
    """
    Get formatted extractions values from the json file of the extracted data\
    Args:
        file_name: name of the file containing the extracted json

    Returns:
        List of text for each extractions
    """
    texts = []
    with open(file_name, 'r') as f:
        json_obj = json.load(f)
    
    for obj in json_obj['extractions']:
        keywords = ', '.join([k for k in obj['keywords']])
        ext_id = obj['extraction_id']
        flc = obj['first_level_class']
        slc = obj['second_level_class']
        content = obj['extracted_content']
        relevant = f'This data is from {ext_id} containing {flc} on {slc}. The content is {content} and contains the keywords {keywords}'
        texts.append(relevant)

    return texts


 
if __name__ =='__main__':

    # file_name = '/home/aditya/REU/Code/Graph_RAG/vectorRAG/mandli_et_al_coupling_coastal_and_hydrologic_models_through_next_generation_national_water_model_framework.json'
    # contents = text_from_json(file_name=file_name)
    # total_chunks = []
    # for idx, c in enumerate(contents):
    #     #since the text(c) is small we are not going to split the text into chunks
    #     chunk = {
    #         "chunk": c,
    #         "source": 'mandli_et_al_coupling_coastal_and_hydrologic_models_through_next_generation_national_water_model_framework',
    #         "chunk_id": "P001_" + str(idx)
    #     }
    #     total_chunks.append(chunk)

    # collection_name = 'P001'    
    # if store_chunks(chunks=total_chunks, collection_name=collection_name):
    #     pass

    # file_name2 = '/home/aditya/REU/Code/Graph_RAG/dataPreparation/markdowns/mandli_et_al_coupling_coastal_and_hydrologic_models_through_next_generation_national_water_model_framework.md'
    # with open(file_name2, 'r') as f:
    #     content = f.read()
    
    # chunks = text_chunking(text=content, chunk_size=200, chunk_overlap=20)
    # total_chunks=[]
    # for idx, c in enumerate(chunks):
    #     chunk = {
    #         "chunk":c,
    #         "source":"mandil_et_al.md",
    #         "chunk_id": 'P001_md_' + str(idx)
    #     }
    #     total_chunks.append(chunk)

    # collection_name = 'P001_md'
    # store_chunks(chunks=total_chunks, collection_name=collection_name)
    openai.apikey = os.getenv('')
    cypher = CypherGenerator()
    while True:
        print('Type q to quit or type your query')
        query = input('Enter your query: ')
        print(f'Available collecitons: {[c.name for c in listCollection()]}')
        collection_name = input('Enter collection to serach in: ')
        if query == 'q':
            break
        
        #creating texts to be chunked
        similar_chunks = retrieve_similar_chunks(query=query, collection_name=collection_name, top_k=8)
        # print('Similar chunks for the given query: ', similar_chunks),
        answer = get_relevant_ext_ids(context=similar_chunks, query=query)
        print(type(answer))
        print('Extracted Ids:', answer)


        

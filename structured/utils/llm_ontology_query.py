import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Optional

from txt_to_json import convert_txt_to_json

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY '))

def generate_ontology(file_name:Optional[str],system_prompt_file:str, output_folder:str='ontology_outputs/',folder_name:str='markdowns/', model:str= 'gpt-4o')->List:
    """
    Generate ontology for the given file using LLM
    
    Args:
        file_name(str): File name from where to extract. If not provided all the files from the folder will be extracted
        system_prompt_file(str): File name for system prompt will be looking in (/prompts/) folder
        output_folder(str): Folder to output the response of LLM, file will be named same as file_name.txt
        folder_name(str): Name of folder where the file is located
        mode(str): ChatGPT model to use
    
    Returns:
        List(ontology): list of json file containing all the relevant ontology data 
    """
    system_prompt_folder = 'prompts/'
    system_prompt_file_path = os.path.join(system_prompt_folder, system_prompt_file)
    system_prompt = extract_content(file_path=system_prompt_file_path)

    if not file_name:
        print(f'No file specified')
        return []
        # for file in os.listdir(folder_name):
        #     content_file_path = os.path.join(folder_name, file)
        #     file_content = extract_content(file_path=content_file_path)
        #     response = llm_query(system_prompt=system_prompt, file_content=file_content)
            #TODO manage the response from llm
    else:
        content_file_path = os.path.join(folder_name, file_name)
        file_content = extract_content(file_path=content_file_path)
        response = llm_query(system_prompt=system_prompt, file_content=file_content)
        convert_txt_to_json(content=response, output_folder=output_folder) 

    return []

def write_to_output(content:str, file_name:str, output_folder:str='ontology_outputs/')->None:
    """
    Writes the provided content to the provided folder with the same name as the file name.txt

    Args:
        content(str): content to write to the file
        file_name(str): name of the original file from where the contents were extracted
        output_folder(str): name of the folder to output the content

    Returns:
        None
    """
    output_file_name = (file_name.split('.')[0]) + '.txt'
    output_path = os.path.join(output_folder, output_file_name)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print('Success: Saved content to file ', output_file_name)
    except Exception as e:
        print('Error: Failed to save content of the file - ', e)

def extract_content(file_path:str)->str:
    """
    extract content from the provided file_name

    Args:
        file_path(str): Path of the file from where to extract the content
    
    Returns:
        content(str): Extracted conent
    """
    with open(file_path, 'r') as f:
        content = f.read()
    print('Extracted content form ', file_path)
    return content

def llm_query(system_prompt:str, file_content:str, model:str='gpt-4o')->str:
    """
    LLM querying
    Args:
        system_prompt(str): System prompt to send to the LLM
        file_content(str): Extracted file content to send to the LLM
        model(str): LLM model
    Returns:
        content(str): Content extracted from the llm
    """
    try:
       start = time.time()
       response = client.chat.completions.create(model=model, messages=[
           {"role": "system", "content":system_prompt},
           {"role": "user", "content": file_content},
       ])
       answer = response.choices[0].message.content
       end = time.time()
       if answer:
        print(f'Time taken for the response {(end - start):.2f} seconds')
        return answer
       else:
        print("Warning: Didn't Get anything from the LLM")
        return ""
    except Exception as e:
        print('Error: Error extracting ontology from OpenAI - ', e)

    return ""


if __name__ == "__main__":
    file_name = 'mandli-et-al-coupling-coastal-and-hydrologic-models-through-next-generation-national-water-model-framework.md'
    generate_ontology(file_name=file_name, system_prompt_file='prompt_v2.txt', output_folder='ontology_outputs/v2/')
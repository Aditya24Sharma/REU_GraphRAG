import os
import json
# import ast
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from chunking import text_chunking

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class ResponseFormat(BaseModel):
    section_type: str = Field(..., description="Type of the section")
    categories: list[str] = Field(..., description="Categories associated with the section")
    content: str = Field(..., description="Content of the section")


def llm_section_preprocess(text: str, model: str = 'gpt-3.5-turbo') -> dict:
    """
    Preprocesses the text using LLM to extract sections and their important contents.

    Args:
        text (str): The text to be preprocessed.
        model (str): The LLM model to use for preprocessing.

    Returns:
        dict: A dictionary containing section titles, categories, and content.
    """
    try:
        # print('Preprocessing text with LLM...')
        system_prompt = """
        You are an AI assistant proficient in Hydrology domain and research. I am providing you with a text document. Your task is to categorize the text into possible sections of research. Follow these instructions:
        1. Put high priority to the given options as one of the sections:
        ["Introduction", "Methods", "Results", "Discussion", "Conclusion", "References"]
        2. If the text does not fit into any of these sections, categorize it as "Others".
        3. Do not categorize very small sections like small sentences or phrases that do not provide enough information.
        4. For each section, remove any unnecessary contents.
        5. DO NOT remove any important information or data from the sections.
        6. For each section, identify the important categories that the section belongs to. Do not write more than 3 categories for each section.
        7. Provide the output in the following json array format:
        {
            "section_type": "Introduction",
            "categories": ["Gulf of Mexico", "impact"],
            "content": "The Gulf of Mexico is highly susceptible to rapid intensification of hurricanes..."
        },
        {
            "section_type": "Results",
            "categories": ["statistical insight", "climate driver"],
            "content": "RI is, on average, 50% more likely during MHWs in the Gulf of Mexico..."
        },
        {
            "section_type": "Methods",
            "categories": ["timeframe","data sources"],
            "content": "We used ERA5 SST data and IBTrACS hurricane data between 1950 and 2022..."
        },
        8. Make sure you output proper JSON. Check the format for content section as it might have some problems like single quotes and other issues. Make sure to use double quotes for JSON keys and values.
        Text:
        """

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
        )
        output = response.choices[0].message.content
        # print(f'LLM output: {output}')
        output_json = [ json.loads(out) for out in [str(output)]]
        print(f'LLM output JSON: {output_json}')
        json_output = output_json[0] if output_json else {}
        # if output:
        #     print(f'Got output of type: {type(output)}')
        #     json_output = json.loads([output])
        #     # print(f'Got output of type: {type(json_output)}')
        # print(f'LLM output JSON: {json_output}')
        # print(f'Type of LLM output: {type(json_output[0])}')
        return json_output[0] if json_output else {}
    except Exception as e:
        print(f'Error during LLM preprocessing: {e}')
        return {}

if __name__ == "__main__":
    folder_path = "markdowns/"
    sample_file = os.listdir(folder_path)[4]
    print(f"Processing file: {sample_file}")
    text = ""
    with open(os.path.join(folder_path, sample_file), 'r', encoding='utf-8') as f:
        text = f.read()

    chunks = text_chunking(text=text, chunk_size=4000,
                           chunk_overlap=400)
    # print(f"Number of chunks: {len(chunks)}")

    # section = llm_section_preprocess(text=chunks[0])
    # print(section)
    collections = {
        "Introduction":{
            "categories": [],
            "content": ""
        },
        "Methods":{
            "categories": [],
            "content": ""
        },
        "Results":{
            "categories": [],
            "content": ""
        },
        "Discussion":{
            "categories": [],
            "content": ""
        },
        "Conclusion":{
            "categories": [],
            "content": ""
        },
        "References":{
            "categories": [],
            "content": ""
        },
        "Others":{
            "categories": [],
            "content": ""
        }
    }

    for chunk in chunks:
        section = llm_section_preprocess(text=chunk)
        # print(f'Type of section: {type(section)}')
        # print(f"Number of sections returned: {len(section)}")
        # print(section)
        # print(f"Processing section: {section.keys()}")
        if section and section['section_type'] in collections:
            collections[section['section_type']]['categories'].extend(section['categories'])
            collections[section['section_type']]['content'] += section['content']


    for section, data in collections.items():
        print(f"Section: {section}")
        print(f"Categories: {data['categories']}")
        print(f"Content: {data['content'][:100]}...")
    print("Processing completed.")

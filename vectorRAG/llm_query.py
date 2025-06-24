import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_response(context: list[str], query: str, model:str='gpt-4o-mini')->str:
    """
    Generates a response using the LLM for the given query
    with the provided context.
    Args:
        context(list[str]): similar chunks to the query
        query(str): The question being asked by the user
        model(str): LLM model to query to 

    Returns:
        answer(str): Answer provided by the LLM for the given query with the provided context
    """
    try:
        print('Generating LLM response...')
        system_prompt = f"""
        You are an AI assistant proficient in Hydrology domain. Anser the queryion based on the provided docment excerpts. 
        Document_context:
        {context}

        Question:{query}
        Answer:
        """

        response = client.chat.completions.create(
            model = model,
            messages=[
                {"role":"system", "content":system_prompt},
                {"role":"user", "content":query}
            ],
        )
        answer = response.choices[0].message.content or ""
        return answer
    except Exception as e:
        print(f'Error generating response from LLM: {e}')
        return ""

def get_relevant_ext_ids(context:list[str], query:str, model:str='gpt-4o-mini')->str:
    """
    From the given context and query filter only the context that will be highly relevant to the given query.
    
    Args:
        context(list[str]): similar chunks to the query
        query(str): The question being asked by the user
        model(str): LLM model to query to 

    Returns:
        str: String containing list of extraction_ids that are relevant to the given query
    """
    try:
        print('Extracting relevant extraction ids')
        system_prompt = f"""
        You are an expert in Hydrology domain. For the query provided by the user, select only the relevant contexts from the context provided. From the selected context, extract the EXT_ids and return them as a list

        Points to focus on:
        1. The context is relevant to answer the question
        2. The output format should be in the format of the list and only contain the ids that are actuallly there in the context provided.

        Document_context:
        {context}

        Questions:
        {query}

        Answer:
        """
        response = client.chat.completions.create(
            model = model, 
            messages = [
                {"role":"system", "content":system_prompt}
                ]
                )
        answer = response.choices[0].message.content or ""
        return answer
    except Exception as e:
        print(f'Error extracting relevant ids from the LLM: {e}')
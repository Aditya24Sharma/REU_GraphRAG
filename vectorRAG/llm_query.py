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
    
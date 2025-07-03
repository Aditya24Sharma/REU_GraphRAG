import os
import tiktoken


def tokencount_from_text(text: str, llm_model: str = "gpt-4o") -> None:
    """
    Prints the number of tokens in each files. Useful to check before sending it to LLMs

    Args:
        source_path(str) : folder to get all the files from
        llm_model(str): Model for which to calculate the token
    Returns:
        None
    """
    encoding = tiktoken.encoding_for_model(llm_model)
    tokens = encoding.encode(text)
    print("Number of token for the provided text is", len(tokens))


def tokencount_from_file(source_path: str, llm_model: str = "gpt-4o") -> None:
    """
    Prints the number of tokens in each files. Useful to check before sending it to LLMs

    Args:
        source_path(str) : folder to get all the files from
        llm_model(str): Model for which to calculate the token
    Returns:
        None
    """
    for filename in os.listdir(source_path):
        filepath = os.path.join(source_path, filename)
        print("Extracted file", filename)
        title = filename.split(".")[0]
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        print("Extracted text is of type", type(text))
        encoding = tiktoken.encoding_for_model(llm_model)
        tokens = encoding.encode(text)
        print(f"Number of tokens for {title[:20]}... is {len(tokens)}")


if __name__ == "__main__":
    source_path = os.path.abspath("/home/aditya/REU/Code/Graph_RAG/graphRAG/")
    tokencount_from_file(source_path=source_path)

import os
import chromadb
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from typing import List, TypedDict

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

#initialize chormadb client
chroma_client = chromadb.PersistentClient(path='vectordb')

#initialize the embedding model 
embedding_model = OpenAIEmbeddings(model= "text-embedding-ada-002")


class ChunkDict(TypedDict):
    chunk : str
    source: str
    chunk_id: str

def store_chunks(chunks:List[ChunkDict], collection_name:str)->bool:
    """
    Stores the chunks with their respective file_name in db
    Args:
        chunks(List[ChunkDict]): list of chunks with text, source, and chunk Id
        collection_name(str): name of the collection to be store in the db
    Returns:
        bool: True if chunks are store else False
    """
    try:
        collection = chroma_client.create_collection(
            name = collection_name
        )
        ids = [chunk['chunk_id'] for chunk in chunks]
        texts = [chunk['chunk'] for chunk in chunks]
        embeddings = embedding_model.embed_documents(texts)
        metadatas = [{"text":c['chunk'], "source":c['source'], "chunk_id":c['chunk_id']} for c in chunks]

        collection.add(
            ids = ids,
            embeddings=embeddings,
            metadatas=metadatas
        )
        return True

    except Exception as e:
        print(f"Error storing chunks: {e}")
        return False

    
def retrieve_similar_chunks(query:str, collection_name:str, top_k:int = 5)->List[str]:
    """
    Retreive similar chunks from ChromaDB for the query
    
    Args:
        query(str): the query to retrieve the similar chunks from
        collection_name(str): collection name that we are searching on
        top_k(int): how many similar chunks to retrieve
    
    Returns:
        output(List[str]): list of similar chunks retrieved
    """
    try:
        print('Fetching similar chunks in db')
        collection = chroma_client.get_collection(collection_name)
        if collection:
            print(f'Found collection for {collection_name}')
        query_embedding = embedding_model.embed_query(query)
        results:QueryObject = collection.query(
            query_embeddings=[query_embedding],
            n_results = top_k
        )
        output = [results["text"] for results in results["metadatas"][0] if results["source"][0]]
        return output
    except Exception as e:
        print(f'Error fetching similar chunks: {e}')
        return []

def collectionExists(collection_name:str)->bool:
    """
    Checks if the collection already exists in the Chromadb

    Args:
        collection_name(str): name of the collection in the db
    
    Returns:
        (bool): True if collection already exists, else False
    """
    try:
        #returns valueError if collection doesn't exist
        chroma_client.get_collection(collection_name)
        print(f"Collection {collection_name} already exists, Skipping process")
        return True
    except Exception as e:
        print(f'Collection {collection_name} does not exist. Processing the file...')
        return False

def deleteCollection(collection_name:str)->None:
    """
    Deletes a collection

    Args:
        collection_name(str): Name of the collection to be deleted
    
    Returns:
        None
    """
    try:
        chroma_client.delete_collection(name=collection_name)
        print(f"Collection {collection_name} successfully deleted")
    except Exception as e:
        print(f'Failed to delete collection {collection_name}: {e}')
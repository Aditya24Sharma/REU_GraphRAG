"""
Chromadb module containing all the functions for chromadb
"""

import os
import json
from typing import List
import logging
import chromadb

# from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


from utils import json_to_txt
from . import config

logger = logging.getLogger(__name__)


class ChunkDict(BaseModel):
    chunk: str
    source: str
    chunk_id: str


class Chromadb:
    """
    Chromadb class defining all the functions
    """

    def __init__(self) -> None:
        """
            initialize the Chromadb with chroma client and embedding model
        Args:
            embedding_mode(str): embedding model to be used for OpenAI
        """
        logger.info("Initializing Chroma")
        openai_api_key = config.OPENAI_API_KEY
        self.chroma_client = chromadb.PersistentClient(path="vectordb")
        # self.embedding_model = OpenAIEmbeddings(model=embedding_model)
        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def store_chunks(self, chunks: List[ChunkDict], collection_name: str) -> bool:
        """
        Stores the chunks with their respective file_name in db
        Args:
            chunks(List[ChunkDict]): list of chunks with text, source, and chunk Id
            collection_name(str): name of the collection to be store in the db
        Returns:
            bool: True if chunks are store else False
        """
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )
            ids = [chunk["chunk_id"] for chunk in chunks]
            texts = [chunk["chunk"] for chunk in chunks]
            # embeddings = self.embedding_model.embed_documents(texts)
            embeddings = self.embedding_model.encode(texts)
            metadatas = [
                {"text": c["chunk"], "source": c["source"], "chunk_id": c["chunk_id"]}
                for c in chunks
            ]

            collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
            return True

        except Exception as e:
            print(f"Error storing chunks: {e}")
            return False

    def retrieve_similar_chunks(
        self, query: str, collection_name: str, top_k: int = 5
    ) -> List[str]:
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
            print("Fetching similar chunks in db")
            collection = self.chroma_client.get_collection(collection_name)
            if collection:
                print(f"Found collection for {collection_name}")
            # query_embedding = self.embedding_model.embed_query(query)
            query_embedding = self.embedding_model.encode(query)
            results = collection.query(
                query_embeddings=[query_embedding.tolist()], n_results=top_k
            )
            output = [
                results["text"]
                for results in results["metadatas"][0]
                if results["source"][0]
            ]
            return output
        except Exception as e:
            print(f"Error fetching similar chunks: {e}")
            return []

    def collection_exists(self, collection_name: str) -> bool:
        """
        Checks if the collection already exists in the Chromadb

        Args:
            collection_name(str): name of the collection in the db

        Returns:
            (bool): True if collection already exists, else False
        """
        try:
            # returns valueError if collection doesn't exist
            self.chroma_client.get_collection(collection_name)
            print(f"Collection {collection_name} already exists, Skipping process")
            return True
        except Exception as e:
            print(
                f"Collection {collection_name} does not exist. Processing the file..."
            )
            return False

    def delete_collection(self, collection_name: str) -> None:
        """
        Deletes a collection

        Args:
            collection_name(str): Name of the collection to be deleted

        Returns:
            None
        """
        try:
            self.chroma_client.delete_collection(name=collection_name)
            print(f"Collection {collection_name} successfully deleted")
        except Exception as e:
            print(f"Failed to delete collection {collection_name}: {e}")

    def list_collections(self) -> List:
        """
        List all the collections avaiable in chromadb
        """
        collections = self.chroma_client.list_collections()
        return list(collections) or []

    def store_to_db(self, input_json_folder: str, collection_name: str) -> None:
        """
        store the contents from json file to the db

        Args:
            input_json_folder(str): folder to extract the json files from
            collection_nam(str): name of the collection of db
        Returns:
            None
        """
        try:
            # for file in os.listdir(input_json_folder):
            file = os.listdir(input_json_folder)[1]
            file_path = os.path.join(input_json_folder, file)
            paper_id = ""
            with open(file_path, "r") as f:
                obj = json.load(f)
                paper_id = obj["paper_id"]
                print("Accesing paper", paper_id)
            contents = json_to_txt(file_name=str(file_path))

            total_chunks = []
            for idx, c in enumerate(contents):
                # since the text(c) is small we are not going to split the text into chunks
                chunk = {
                    "chunk": c,
                    "source": paper_id,
                    "chunk_id": paper_id + str(idx),
                }
                total_chunks.append(chunk)
            if self.store_chunks(total_chunks, collection_name=collection_name):
                logger.info(
                    f"Succesfully stored to db under collection name: {collection_name}"
                )
        except Exception as e:
            logger.error("Failed to store to db: %s", e)

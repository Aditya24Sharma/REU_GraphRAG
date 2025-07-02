"""
Query class for a single user query session
"""

import os
import json
import logging
from pathlib import Path

from utils import json_to_txt, chunking
from database import Neo4j, Chromadb
from llm import LLM

logger = logging.getLogger(__name__)


class Query:
    """
    Query class to handle a single user query session

    """

    def __init__(self):
        self.messages = []  # Store all the context for previous messages
        self.llm = LLM()
        self.chromadb = Chromadb()
        self.neo4j = Neo4j()

    def query(self, user_query: str, collection_name: str = "") -> str:
        """
        function to query the LLM
        Args:
            user_query(str): question to ask to the LLM
            collection_name(str): Collection name to query from. Set to none to query for all.
        Returns:
            Answer from the LLM
        """
        revisedQuery = self.llm.revise_query(query=user_query)
        if not collection_name:
            pass
        print(user_query)
        return ""

"""
Query class for a single user query session
"""

import os
from typing import List
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
        self.papers = []
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
        revised_query = json.loads(self.llm.revise_query(query=user_query))
        output = ""
        available_collections = [c.name for c in self.chromadb.list_collections()]
        if collection_name.lower() == "both":
            overall_context = {"Vector": [], "Graph": []}
            for c in available_collections:
                similar_chunks = set()
                for query in revised_query:
                    similar = self.chromadb.retrieve_similar_chunks(
                        query=query, collection_name=c, top_k=10
                    )
                    for s in similar:
                        similar_chunks.add(s)
                if c == "Graph":
                    answer = self.llm.extract_relevant_ids(
                        context=list(similar_chunks), query=user_query
                    )

                    context = [""]
                    if answer:
                        context = self.neo4j.retrieve_neighbors(nodes=answer)
                    overall_context["Graph"].extend(context)
                else:
                    overall_context["Vector"].extend(list(similar_chunks))
            output = self.llm.query_with_context(
                context=overall_context, query=user_query
            )
        else:
            similar_chunks = self.chromadb.retrieve_similar_chunks(
                query=user_query, collection_name=collection_name, top_k=10
            )
            if collection_name.lower() == "graph":
                answer = self.llm.extract_relevant_ids(
                    context=similar_chunks, query=user_query
                )
                context = [""]
                if answer:
                    context = self.neo4j.retrieve_neighbors(nodes=answer)
                output = self.llm.query_with_context(context=context, query=user_query)
            else:
                output = self.llm.query_with_context(
                    context=similar_chunks, query=user_query
                )
        return output

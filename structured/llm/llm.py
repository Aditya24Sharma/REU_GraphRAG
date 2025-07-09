"""
LLM module that contains all the functions to be called for the llm being used
"""

import os
import re
import logging
import time
from typing import Any, List, Optional
from openai import OpenAI

from utils import convert_txt_to_json
from . import config

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


class LLM:
    """
    LLM class to use all the functions from
    """

    def __init__(self) -> None:
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.MODEL_NAME
        self.cwd = os.path.dirname(__file__)

    def simple_query(self, query: str) -> str:
        """
        Simple convertational query with the llm

        Args:
            query(str): question to be asked

        Returns:
            answer(str): response from the llm
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": query}]
            )
            answer = response.choices[0].message.content
            return answer or ""
        except Exception as e:
            logger.error(f"Failed to generate simple query: {e}")
            return ""

    def revise_query(self, query: str) -> str:
        """
        Revise the user query to be later provided to the llm
        Args:
            query(str): question asked by the user

        Returns:
            revised(str): revised question that was asked by the user
        """
        try:
            logger.info("LLM generating revised query")

            prompt_path = os.path.join(self.cwd, "prompts", "revise_query.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
            )
            answer = response.choices[0].message.content or ""
            # print(answer)
            return answer
        except Exception as e:
            logger.error(f"Failed to generate revised query: {e}")
            return ""

    def query_with_context(self, context: Any, query: str) -> str:
        """
        Generates a response using the LLM for the given query with the provided context.
        Args:
            context(Any): similar chunks to the query
            query(str): The question being asked by the user

        Returns:
            answer(str): Answer provided by the LLM for the given query with the provided context
        """
        try:
            logger.info("LLM generating answer with the provided context")

            prompt_path = os.path.join(self.cwd, "prompts", "general_context.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()

            system_prompt = system_prompt.format(context=context)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
            )
            answer = response.choices[0].message.content or ""

            return answer

        except Exception as e:
            logger.error(f"Failed to generated answer with the provided context: {e}")
            return ""

    def extract_relevant_ids(self, context: List[str], query: str) -> List[str]:
        """
        From the given context and query filter only the context that will be highly relevant to the given query.

        Args:
            context(list[str]): similar chunks to the query
            query(str): The question being asked by the user

        Returns: list[str]: List of strings containing list of extraction_ids that are relevant to the given query
        """
        try:
            logger.info("LLM extracting relevant ids from provided context")

            prompt_path = os.path.join(self.cwd, "prompts", "extract_relevant_ids.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()

            system_prompt = system_prompt.format(context=context)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
            )
            answer = response.choices[0].message.content or ""

            formatted = re.findall(r"\bP\d{3}_EXT_\d+\b", answer)
            return formatted or [""]
        except Exception as e:
            logger.error(f"Failed to extract relevant ids from provided context: {e}")
            return [""]

    def generate_ontology(
        self,
        file_name: Optional[str],
        system_prompt_file: str,
        output_folder: str,
        output_folder_json: str,
        folder_name: str = "../data/markdowns/",
        model: str = "gpt-4o",
    ):
        """
        Generate ontology for the given file using LLM

        Args:
            file_name(str): File name from where to extract. If not provided all the files from the folder will be extracted
            system_prompt_file(str): File name for system prompt will be looking in (/prompts/) folder
            output_folder(str): Folder to output the response of LLM, file will be named same as file_name.txt
            folder_name(str): Name of folder where the file is located
            mode(str): ChatGPT model to use

        Returns:
            None
        """
        system_prompt_folder = "../kg_prompts/prompts/"
        system_prompt_file_path = os.path.join(system_prompt_folder, system_prompt_file)
        system_prompt = self.extract_content(file_path=system_prompt_file_path)
        try:
            logger.info("Generating Ontology")
            if not file_name:
                logger.info("No file provided so extracted from Folder")
                for file in os.listdir(folder_name):
                    content_file_path = os.path.join(folder_name, file)
                    file_content = self.extract_content(file_path=content_file_path)
                    response = self.llm_ontology(
                        system_prompt=system_prompt,
                        file_content=file_content,
                        model=model,
                    )
                    convert_txt_to_json(
                        file_name=file,
                        content=response,
                        output_folder=output_folder_json,
                    )
                logger.info(f"Generated complete ontology for {folder_name}")
            else:
                content_file_path = os.path.join(folder_name, file_name)
                file_content = self.extract_content(file_path=content_file_path)
                response = self.llm_ontology(
                    system_prompt=system_prompt, file_content=file_content
                )
                convert_txt_to_json(
                    file_name=file_name,
                    content=response,
                    output_folder=output_folder_json,
                )
                logger.info(f"Generated complete ontology for{file_name}")
        except Exception as e:
            logger.error("Failed to Generate Ontolgy")

    def write_to_output(
        self, content: str, file_name: str, output_folder: str = "ontology_outputs/"
    ) -> None:
        """
        Writes the provided content to the provided folder with the same name as the file name.txt

        Args:
            content(str): content to write to the file
            file_name(str): name of the original file from where the contents were extracted
            output_folder(str): name of the folder to output the content

        Returns:
            None
        """
        output_file_name = (file_name.split(".")[0]) + ".txt"
        output_path = os.path.join(output_folder, output_file_name)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Success: Saved content to file {output_file_name}")
        except Exception as e:
            logger.error(f"Error: Failed to save content of the file - {e}")

    def extract_content(self, file_path: str) -> str:
        """
        extract content from the provided file_name

        Args:
            file_path(str): Path of the file from where to extract the content

        Returns:
            content(str): Extracted conent
        """
        with open(file_path, "r") as f:
            content = f.read()
        return content

    def llm_ontology(
        self, system_prompt: str, file_content: str, model: str = "gpt-4o"
    ) -> str:
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
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": file_content},
                ],
            )
            answer = response.choices[0].message.content
            end = time.time()
            if answer:
                logger.info(f"Time taken for the response {(end - start):.2f} seconds")
                return answer
            else:
                logger.info("Warning: Didn't Get anything from the LLM")
                return ""
        except Exception as e:
            logger.error(f"Error: Error extracting ontology from OpenAI - {e}")

        return ""

"""
This is config file from where we manage all the variables to be used in the llm folder
"""

import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gpt-4o-mini"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

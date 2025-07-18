"""
    Logging module
"""

import logging

def setup_logging(log_level:str='INFO'):
    """
    Function to setup logging

    Args:
        log_level(str): logging level
    Returns:
        None
    """
#TODO: Add log_file to save all the logs
    logging.basicConfig(
        level = getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = [logging.StreamHandler()]
    )

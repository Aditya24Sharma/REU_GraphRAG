import json
from typing import List


def json_to_txt(file_name: str) -> List[str]:
    """
    Get formatted extractions values from the json file of the extracted data\
    Args:
        file_name: name of the file containing the extracted json

    Returns:
        List of text for each extractions
    """
    texts = []
    with open(file_name, "r") as f:
        json_obj = json.load(f)

    for obj in json_obj["extractions"]:
        keywords = ", ".join([k for k in obj["keywords"]])
        ext_id = obj["extraction_id"]
        flc = obj["first_level_class"]
        slc = obj["second_level_class"]
        content = obj["extracted_content"]
        relevant = f"This data is from {ext_id} containing {flc} on {slc}. The content is {content} and contains the keywords {keywords}"
        texts.append(relevant)

    return texts

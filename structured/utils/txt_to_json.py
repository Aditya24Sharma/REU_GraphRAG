import json
import os
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def convert_txt_to_json(
    file_name: str = "",
    folder_name: str = "",
    output_folder: str = "ontology_outputs_json/",
    content: Optional[str] = "",
):
    """
    converts provided txt to json
    Args:
        file_name(str): name of file to extract the text from
        folder_name(str): name of the folder from where to extract the txt from
        output_folder(str): output folder where the json file should be stored
        content:Optional[str]: you can provide content instead of file_name and folder_name
    """
    try:
        output_file_name = file_name.split(".")[0] + ".json"
        output_path = os.path.join(output_folder, output_file_name)

        if not content and not (file_name and folder_name):
            raise ValueError(
                "Either `content` or both `file_name` and `folder_name` must be provided"
            )

        # if content is not provided then can extract it from the file
        if not content:
            file_path = os.path.join(folder_name, file_name)
            with open(file_path, "r") as f:
                content = f.read()

        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            formatted_json = json.loads(match.group(1))
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(formatted_json, f, indent=2)
            logger.info(f"Output created in {output_path}")
        else:
            raise ValueError("No valid JSON block found")
    except Exception as e:
        logger.error(f"Failed to convert {file_name} to json:{e}")


if __name__ == "__main__":
    file_name = "mandli-et-al-coupling-coastal-and-hydrologic-models-through-next-generation-national-water-model-framework.txt"
    folder_name = "ontology_outputs/v2/"
    output_folder = "ontology_outputs_json/v2/"
    json_format = convert_txt_to_json(
        file_name=file_name, folder_name=folder_name, output_folder=output_folder
    )

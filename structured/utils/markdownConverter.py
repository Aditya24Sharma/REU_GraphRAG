import os
import re
import unicodedata
from pathlib import Path
from markitdown import MarkItDown


def markdownConverter(source_path: str, destination_path: str):
    """
    Converts all the files from a folder to markdown files
    Args:
        source_path(str) : folder to get all the files from
        destination_path(str) : folder to store all your converted markdown files to

    Returns:
        None
    """
    os.makedirs(
        destination_path, exist_ok=True
    )  # create the destination folder if it doesn't exist

    for filename in os.listdir(source_path):
        filepath = os.path.join(source_path, filename)
        title = sanitize_filename(file_name=filename)
        md = MarkItDown(enable_plugins=False)
        results = md.convert(filepath)

        output_path = os.path.join(destination_path, f"{title}.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(str(results))

        print(f"Converted {title[:10]} ... to md")


def sanitize_filename(file_name: str, replacement: str = "_") -> str:
    """
    returns proper sanitized filename that can be used in making safe file for use in a file system
    Args:
        file_name(str): name of the file to be sanitized
        replacement(str): string to replace the invalid characters with

    Returns:
        sanitized_name(str): sanitized name of the file to be used in a file system
    """
    # removing file extension
    path = Path(file_name)
    name = path.stem

    # Normalize unicode characters
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")

    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)

    # Collapase multiple replacement/spaces
    name = re.sub(rf"[{re.escape(replacement)}\s]+", replacement, name)

    return name.strip(replacement)


if __name__ == "__main__":
    source_path = "../papers"
    destination_path = os.path.abspath("markdowns/")
    markdownConverter(source_path=source_path, destination_path=destination_path)

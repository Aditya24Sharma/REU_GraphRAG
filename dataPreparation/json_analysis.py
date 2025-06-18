import json
import os
from typing import Optional, Dict

from collections import defaultdict, deque

def analysis(folder_name:str, file_name:Optional[str]=""):

    #TODO make this functional for all the files in the directory
    for file in os.listdir(folder_name):
        file_path = os.path.join(folder_name, file)
        with open(file_path, "r", encoding='utf-8') as f:
            content = f.read()
        
        content_json = json.loads(content)
        analyze_fields(content_json)
        

def analyze_fields(data):
    if not isinstance(data, dict):
        #if it is not a dictionary and it doesn't have any value i.e empty list or string return false
        #There can be a dictionary inside a list
        if not data:
            return False

        if isinstance(data, list):
            analyze_fields(data[0])

    else:
        #Now if it is a dictionary
        for key in data.keys():
            if not analyze_fields(data[key]):
                print(f'{key} field is empty')

    return True

if __name__ == "__main__":
    folder_name = 'ontology_outputs_json/'
    analysis(folder_name=folder_name)
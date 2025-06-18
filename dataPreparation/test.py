import json
import os
from pathlib import Path

folder = './ontology_outputs_json/v2/'

for files in os.listdir(folder):
    prev_name = files
    new_name = files.replace('-', '_')
    print('Previous Name: ', prev_name)
    print('New Name: ', new_name)
    os.rename((folder+prev_name), (folder+new_name))
    print('successfull renamed')





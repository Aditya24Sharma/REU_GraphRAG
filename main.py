import os


from dataPreparation import text_chunking
from vectorRAG import store_chunks, collectionExists, deleteCollection


files_path = 'dataPreparation/markdowns/'

total_chunks = []
for file in os.listdir(files_path)[:2]:
    print('Created db for', file)
    file_path = os.path.join(files_path, file)

    with open(file_path, 'r') as f:
        contents = f.read()
        # print(f'{file[:15]} has {len(text_chunking(contents, chunk_size=700, chunk_overlap=40))} chunks')
        chunks = text_chunking(contents, chunk_size=200, chunk_overlap=20)
        for idx, chunk in enumerate(chunks):
            total_chunks.append({
                "chunk": chunk,
                "source": file,
                "chunk_id": f"{file}_chunk_{idx}"
            })

print('total_chunks: ', len(total_chunks))

# collection_name = 'cs_700_co_40'
collection_name = 'only1_doc'
# deleteCollection(collection_name=collection_name)

if collectionExists(collection_name=collection_name):
    pass
else:
    print('Storing chunks in the db')
    store_chunks(chunks=total_chunks, collection_name=collection_name)

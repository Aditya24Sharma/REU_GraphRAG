from vectorRAG import generate_response, retrieve_similar_chunks

# collection_name = 'cs_700_co_40'
collection_name = 'only1_doc'
query = ''
while True:
    print('Type q to quit or type your query')
    query = input('Enter your query: ')
    if query == 'q':
        break

    similar_chunks = retrieve_similar_chunks(query=query, collection_name=collection_name, top_k=8)
    answer = generate_response(context=similar_chunks, query=query)
    print(answer)

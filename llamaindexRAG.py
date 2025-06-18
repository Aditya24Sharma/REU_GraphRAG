import os
# import abc
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from dotenv import load_dotenv

load_dotenv()

os.getenv('OPENAI_API_KEY')

llm = OpenAI(model="gpt-4", temperature=0.1)
embed_model = OpenAIEmbedding()

def create_rag_system(data_path):
    """
    Create a RAG system from documents in the specified directory
    
    Args:
        data_path (str): Path to directory containing documents
    
    Returns: # How to synthesize the response
       
        query_engine: LlamaIndex query engine for RAG
    """
    try:
        # Load documents from directory
        print(f"Loading documents from {data_path}...")
        documents = SimpleDirectoryReader(data_path).load_data()
        print(f"Loaded {len(documents)} documents")
        
        # Create vector store index
        print("Creating vector index...")
        index = VectorStoreIndex.from_documents(documents=documents)
        
        # Create query engine
        query_engine = index.as_query_engine(
            similarity_top_k=10,  # Number of similar chunks to retrieve 
            )
        
        print("RAG system ready!")
        return query_engine
        
    except Exception as e:
        print(f"Error creating RAG system: {e}")
        return None

def query_rag_system(query_engine, question):
    """
    Query the RAG system with a question
    
    Args:
        query_engine: LlamaIndex query engine
        question (str): Question to ask
    
    Returns:
        str: Response from the RAG system
    """
    try:
        print(f"Querying: {question}")
        response = query_engine.query(question)
        return str(response)
    except Exception as e:
        print(f"Error querying RAG system: {e}")
        return None

# # Main execution
if __name__ == "__main__":
    # Path to your documents
    data_directory = './dataPreparation/markdowns/'
    
    # Create the RAG system
    rag_engine = create_rag_system(data_directory)
    
    if rag_engine:
        # Example queries
        sample_queries = [
            "What is the main topic discussed in the documents?",
            "Can you summarize the key points?",
            "What are the most important concepts mentioned?"
        ]
        
        # Interactive query loop
        print("\n" + "="*50)
        print("RAG System Ready - Enter your questions!")
        print("Type 'quit' to exit")
        print("="*50)
        
        while True:
            user_query = input("\nYour question: ")
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if user_query:
                response = query_rag_system(rag_engine, user_query)
                if response:
                    print(f"\nAnswer: {response}")
                    print("-" * 50)
            else:
                print("Please enter a valid question.")

# Alternative: Simple function-based approach
def simple_rag_query(data_path, query_string):
    """
    Simple one-function approach to RAG
    
    Args:
        data_path (str): Path to documents directory
        query_string (str): Question to ask
    
    Returns:
        str: Response from RAG system
    """
    # Configure settings
    llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
    embed_model = OpenAIEmbedding()
    
    # Load and index documents
    documents = SimpleDirectoryReader(data_path).load_data()
    index = VectorStoreIndex.from_documents(documents=documents)
    query_engine = index.as_query_engine()
    
    # Query and return response
    response = query_engine.query(query_string)
    return str(response)

# Example usage of simple approach:
# while True:
#     user_query = input('Enter User Query: ')
#     if user_query == 'q':
#         break
#     result = simple_rag_query('./dataPreparation/markdowns/', user_query)
#     print('Answer: ',result)
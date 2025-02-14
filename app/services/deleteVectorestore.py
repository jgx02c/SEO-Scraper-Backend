import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get Pinecone API key from .env
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing from environment variables")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

async def delete_vectorstore(vectorstore_name: str):
    """Deletes a Pinecone vectorstore."""
    print(f"Deleting Pinecone vectorstore: {vectorstore_name}")

    # List all existing indexes
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    
    if vectorstore_name in existing_indexes:
        print(f"Deleting index: {vectorstore_name}")
        pc.delete_index(vectorstore_name)
        print(f"Index {vectorstore_name} deleted successfully.")
    else:
        print(f"Index {vectorstore_name} does not exist. Skipping deletion.")

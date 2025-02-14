import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get Pinecone API key from .env
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing from environment variables")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Initialize Google embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

async def create_embeddings(vectorstore_name: str):
    """Creates a Pinecone vectorstore with Google embeddings."""
    print(f"Creating Pinecone vectorstore: {vectorstore_name}")

    # Ensure the index does not already exist
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    
    if vectorstore_name not in existing_indexes:
        print(f"Creating new Pinecone index: {vectorstore_name}")
        pc.create_index(
            name=vectorstore_name,
            dimension=768,  # Adjust based on the embedding model
            metric="cosine",  # Use cosine similarity
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    else:
        print(f"Index {vectorstore_name} already exists. Skipping creation.")

    # Initialize Pinecone vector store
    index = pc.Index(vectorstore_name)
    vectordb = PineconeVectorStore(index=index, embedding=embeddings)

    return vectordb  # Return the vector store instance

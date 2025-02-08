import uuid
import pinecone
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document

# Initialize Pinecone (make sure you've done this once in your script)
pinecone.init(api_key="6d324250-d2de-411e-9bbe-31986b58d074", environment="us-west1-gcp")

# Initialize the OpenAI embeddings model
embeddings = OpenAIEmbeddings()

# Define the Pinecone index name
index_name = "leaps"

# Initialize the Pinecone index and vector store
index = pinecone.GRPCIndex(index_name)
vectorstore = Pinecone(index=index, embedding_function=embeddings.embed_query)

# Function to upsert a document into Pinecone
def upsert_document(document: Document, doc_id: str = None):
    try:
        # Assign a unique ID if not provided
        if not doc_id:
            doc_id = str(uuid.uuid4())  # Generate a random unique ID

        # Create a list of documents with the ID
        document_with_id = Document(
            page_content=document.page_content,
            metadata=document.metadata
        )

        # Upsert the document with the unique ID
        vectorstore.add_documents([document_with_id])

        print(f"Document upserted successfully with ID: {doc_id}")
        return doc_id  # Return the document ID for later use
    except Exception as e:
        print(f"Error during upsert: {e}")

# Function to remove a document by its ID
def remove_document(doc_id: str):
    try:
        # Delete the document from Pinecone using its ID
        index.delete(ids=[doc_id])

        print(f"Document with ID {doc_id} removed successfully!")
    except Exception as e:
        print(f"Error during deletion: {e}")

# Example document
doc = Document(
    page_content="This is a sample document to be upserted.",
    metadata={"source": "source_1", "author": "Author Name"}
)

# Upsert the document and get its unique ID
doc_id = upsert_document(doc)

# Later, when you need to delete the document
remove_document(doc_id)

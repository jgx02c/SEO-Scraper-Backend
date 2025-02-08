import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from uuid import uuid4
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document  # Ensure you import the Document class

# Initialize Pinecone
pc = Pinecone(api_key="6d324250-d2de-411e-9bbe-31986b58d074")

# Initialize embeddings
embeddings = OpenAIEmbeddings()

def create_embeddings(txt_paths, persist_directory):
    os.makedirs(persist_directory, exist_ok=True)

    all_documents = []

    for txt_path, prefix in txt_paths.items():
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()

        # Split the text into chunks
        text_splitter = CharacterTextSplitter(
            separator=".",
            chunk_size=250,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(text)

        # Create a Document object for each chunk
        for chunk in chunks:
            # Create a Document object for each text chunk
            doc = Document(page_content=chunk, metadata={'source': prefix})
            all_documents.append(doc)  # Append the Document object

    # Ensure the index is created only once
    index_name = "leaps"

    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

    # Create the Pinecone index
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=1536,  # Use the model's dimension
            metric="cosine",  # Replace with your model metric
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            ) 
        )

    index = pc.Index(index_name)

    # Initialize the Pinecone vector store
    vectordb = PineconeVectorStore(index=index, embedding=embeddings)

    # Add documents to the vector store
    vectordb.add_documents(documents=all_documents)

    return len(all_documents)


def generate_vectorestore():
    TXT_PATHS = {
        "./new_scripts/Witness_Statement_Rachel_Green.txt": "POLICEREPORTRACHELGREEN",
        "./new_scripts/Police_Report_Officer_James_Mitchell.txt": "POLICEREPORTSUMMARY",
        "./new_scripts/Injury_Report_John_Smith.txt": "INJURY",
        "./new_scripts/Medical_Records_John_Smith.txt": "JOHNSMITHMEDICAL",
        "./new_scripts/Insurance_Claim_John_Smith.txt": "JOHNSMITHINSURANCE",
        "./new_scripts/Driver_Statement_James_Wilson.txt": "JACKTOMPSONSTATEMENT",
        "./new_scripts/Accident_Reconstruction_Report.txt": "ACCIDENTRECONSTRUCTION",
    }
    PERSIST_DIRECTORY = "embeddings_db"
    
    try:
        num_chunks = create_embeddings(TXT_PATHS, PERSIST_DIRECTORY)
        print(f"Created embeddings for {num_chunks} text chunks from multiple text files")
    except Exception as e:
        print(f"An error occurred: {str(e)}")



#if __name__ == "__main__":
#    TXT_PATHS = {
#        "./new_scripts/Witness_Statement_Rachel_Green.txt": "POLICEREPORTRACHELGREEN",
#        "./new_scripts/Police_Report_Officer_James_Mitchell.txt": "POLICEREPORTSUMMARY",
#        "./new_scripts/Injury_Report_John_Smith.txt": "INJURY",
#        "./new_scripts/Medical_Records_John_Smith.txt": "JOHNSMITHMEDICAL",
#        "./new_scripts/Insurance_Claim_John_Smith.txt": "JOHNSMITHINSURANCE",
#        "./new_scripts/Driver_Statement_James_Wilson.txt": "JACKTOMPSONSTATEMENT",
#        "./new_scripts/Accident_Reconstruction_Report.txt": "ACCIDENTRECONSTRUCTION",
#    }
#    PERSIST_DIRECTORY = "embeddings_db"
#    
#    try:
#        num_chunks = create_embeddings(TXT_PATHS, PERSIST_DIRECTORY)
#        print(f"Created embeddings for {num_chunks} text chunks from multiple text files")
#    except Exception as e:
#        print(f"An error occurred: {str(e)}")
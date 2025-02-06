import json
import base64
import sys
import re
import os

from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict
from langchain_core.runnables import RunnablePassthrough

from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore

# Ensure the index is created only once

pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
llm = ChatOpenAI(model="gpt-4o", streaming=True)
embeddings = OpenAIEmbeddings()
index_name = "dialogica"
index = pc.Index(index_name)
PineconeVectorStore(index=index, embedding=embeddings)

def parse_retriever_input(params: Dict):
    last_message_content = params["messages"][-1].content
    if isinstance(last_message_content, list):
        return " ".join([item.get("text", "") for item in last_message_content if item["type"] == "text"])
    return last_message_content  # In case it's already a string

def process_transcription( text_chunk, vectordb):
    image_message = HumanMessage(
        content=f"{text_chunk}"  # Change this to just the text string
    )
    
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})
    
    SYSTEM_TEMPLATE = """
    **Instruction**: Given the Users Message, complete the task using the context provided.

    ---
    **Context**:
    {context}
    """
    
    question_answering_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SYSTEM_TEMPLATE,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    
    document_chain = create_stuff_documents_chain(llm, question_answering_prompt)
    retrieval_chain = RunnablePassthrough.assign(
        context=parse_retriever_input | retriever,
    ).assign(
        answer=document_chain
    )
    
    response_stream = retrieval_chain.stream({"messages": [image_message]})

    for chunk in response_stream:
        if 'answer' in chunk:
            yield chunk['answer']  # Yield each chunk as it's processed


def generate_insight_prompt(message):

    text_chunk = message

    vectordb = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)

    try:
        for result_chunk in process_transcription(text_chunk, vectordb):
            yield result_chunk  # Yield each chunk as it's processed
    except Exception as e:
        print(f"Error during transcription processing: {str(e)}")
        yield "Error: Could not generate insight."



#if __name__ == "__main__":
#    prompt_message = "What are the past medical records of John Smith?"
#    result = generate_insight_prompt(prompt_message)

    # Collect insights in a list
#    insights = []
#    for insight in result:
#        insights.append(insight)

    # Join the insights with a space or any other delimiter you prefer
#    output = " ".join(insights)  # You can change the delimiter here if needed
#    print(output)

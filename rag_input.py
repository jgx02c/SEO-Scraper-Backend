import json
import base64
import sys
import re
import os
from typing import Dict, Generator

from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore

def parse_retriever_input(params: Dict):
    last_message_content = params["messages"][-1].content
    if isinstance(last_message_content, list):
        return " ".join([item.get("text", "") for item in last_message_content if item["type"] == "text"])
    return last_message_content

def process_transcription(text_chunk: str, vectordb: PineconeVectorStore, llm: ChatOpenAI, system_prompt: str) -> Generator[str, None, None]:
    image_message = HumanMessage(content=text_chunk)
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})
    
    question_answering_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    document_chain = create_stuff_documents_chain(llm, question_answering_prompt)
    retrieval_chain = RunnablePassthrough.assign(
        context=parse_retriever_input | retriever,
    ).assign(answer=document_chain)
    
    try:
        response_stream = retrieval_chain.stream({"messages": [image_message]})
        for chunk in response_stream:
            if 'answer' in chunk:
                yield chunk['answer']
    except Exception as e:
        print(f"Error in process_transcription: {str(e)}")
        yield f"Error: {str(e)}"

def generate_insight_prompt(message: str, vector_store: str, model: str, temperature: float, 
                          presence_penalty: float, system_prompt: str) -> Generator[str, None, None]:
    # Initialize Pinecone
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=model,
        streaming=True,
        temperature=temperature,
        presence_penalty=presence_penalty,
    )
    
    # Initialize embeddings with hardcoded model
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Initialize vector store
    vectordb = PineconeVectorStore.from_existing_index(
        index_name=vector_store,
        embedding=embeddings
    )
    
    try:
        yield from process_transcription(message, vectordb, llm, system_prompt)
    except Exception as e:
        print(f"Error during insight generation: {str(e)}")
        yield "Error: Could not generate insight."

def get_insight_for_input(message: str, vector_store: str, model: str, temperature: float, 
                         presence_penalty: float, system_prompt: str) -> str:
    result = generate_insight_prompt(
        message=message,
        vector_store=vector_store,
        model=model,
        temperature=temperature,
        presence_penalty=presence_penalty,
        system_prompt=system_prompt
    )
    
    insights = []
    for insight in result:
        insights.append(insight)
    
    return " ".join(insights)
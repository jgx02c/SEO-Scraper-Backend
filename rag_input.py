import json
import base64
import sys
import re
import os
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, Generator
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore

def parse_retriever_input(params: Dict):
    last_message_content = params["messages"][-1].content
    if isinstance(last_message_content, list):
        return " ".join([item.get("text", "") for item in last_message_content if item["type"] == "text"])
    return last_message_content

def process_transcription(text_chunk, vectordb, llm, system_prompt):
    image_message = HumanMessage(content=f"{text_chunk}")
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})
    
    question_answering_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    document_chain = create_stuff_documents_chain(llm, question_answering_prompt)
    retrieval_chain = RunnablePassthrough.assign(
        context=parse_retriever_input | retriever,
    ).assign(answer=document_chain)
    
    response_stream = retrieval_chain.stream({"messages": [image_message]})
    
    for chunk in response_stream:
        if 'answer' in chunk:
            yield chunk['answer']

def initialize_llm(model, temperature, presence_penalty):
    return ChatOpenAI(
        model=model,
        streaming=True,
        temperature=temperature,
        presence_penalty=presence_penalty,
    )

def generate_insight_prompt(message, vectordb, llm, system_prompt):
    text_chunk = message
    
    try:
        for result_chunk in process_transcription(text_chunk, vectordb, llm, system_prompt):
            yield result_chunk
    except Exception as e:
        print(f"Error during transcription processing: {str(e)}")
        yield "Error: Could not generate insight."

def get_insight_for_input(
    message: str,
    model: str,
    temperature: float,
    presence_penalty: float,
    vectordb: PineconeVectorStore,
    system_prompt: str
) -> Generator[str, None, None]:
    # Initialize LLM with settings
    llm = initialize_llm(model, temperature, presence_penalty)
    
    result = generate_insight_prompt(
        message,
        vectordb,
        llm,
        system_prompt
    )
    for chunk in result:
        yield chunk
import openai

openai.api_key = 'your-api-key'  # Add your OpenAI API key here

# Function for streaming the response
def stream_openai_response(prompt: str):
    # Create a chat completion request with streaming enabled and use web search in the context
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Adjust based on the model you're using
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        stream=True,  # Enable streaming
        functions=[
            {
                "name": "websearch",
                "parameters": {
                    "query": prompt  # Dynamically pass the prompt as a search query
                }
            }
        ]
    )

    # Process the streaming response
    for chunk in response:
        # Check for the choice and message content in the response
        if 'choices' in chunk:
            for choice in chunk['choices']:
                if 'message' in choice:
                    print(choice['message']['content'], end='')  # Stream the response as it's received

# Example usage
prompt = "What are the latest trends in artificial intelligence?"
stream_openai_response(prompt)

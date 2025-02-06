# controllers/chatData.py
from fastapi import WebSocket, HTTPException
from fastapi.responses import PlainTextResponse
from ..services.rag_service import generate_insight_prompt  # Assuming this is where you have the function

# This will be a function that can be called from the route
async def chatData(chat_message: str, websocket: WebSocket):
    message = chat_message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="No message provided")

    try:
        # Emit the 'insight_start' message to clients
        await websocket.send_text("insight_start")

        # Call the generate_insight_prompt function
        insight_generator = generate_insight_prompt(message)  # This returns a generator

        # Process the generated chunks and emit them
        insight_chunks = []
        async for insight_chunk in insight_generator:
            insight_chunks.append(insight_chunk)
            await websocket.send_text(f"insight_data: {insight_chunk}")  # Emit each chunk to clients

        # Join the chunks to create the full insight
        full_insight = ''.join(insight_chunks)

        # Emit that the insight generation is finished
        await websocket.send_text("insight_finished")
        
        # Return the full insight as plain text
        return full_insight

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insight: {str(e)}")

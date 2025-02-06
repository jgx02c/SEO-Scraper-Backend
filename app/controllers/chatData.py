from fastapi import APIRouter, HTTPException, WebSocket
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from ..services.rag_service import generate_insight_prompt  # Assuming this is where you have the function
from fastapi import WebSocket, WebSocketDisconnect

router = APIRouter()

# Define a model for the incoming message
class ChatMessage(BaseModel):
    message: str

# Route for handling chat data
@router.post("/chat-data", response_class=PlainTextResponse)
async def handle_chat_data(chat_message: ChatMessage, websocket: WebSocket):
    message = chat_message.message.strip()

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


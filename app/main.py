import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.model.suggestion_model import get_suggestion
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI()

@app.get("/")
async def get_root():
    return {"Hello": "World"}

@app.websocket("/ws")
async def get_suggestion_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive text data
            data = await websocket.receive_text()
            
            try:
                # Parse JSON data
                message = json.loads(data)
                prefix_text = message.get("prefix_text", "")
                suffix_text = message.get("suffix_text", "")
                
                # Get complete suggestion
                suggestion = await get_suggestion(prefix_text, suffix_text)
                
                if suggestion and not suggestion.startswith("Error:"):
                    # Send the complete suggestion
                    response = {"suggestion": suggestion}
                    await websocket.send_text(json.dumps(response))
                else:
                    # Send error if occurred
                    error_message = suggestion[6:] if suggestion.startswith("Error:") else "Generation error"
                    error_response = {"error": error_message}
                    await websocket.send_text(json.dumps(error_response))
                
            except json.JSONDecodeError:
                error_response = {"error": "Invalid JSON format"}
                await websocket.send_text(json.dumps(error_response))
                
            except Exception as e:
                error_response = {"error": f"Processing error: {str(e)}"}
                await websocket.send_text(json.dumps(error_response))
                # Don't break the loop - continue listening for more messages
                
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        # Cleanup if needed
        print("WebSocket connection closed")



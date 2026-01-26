import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.model.suggestion_model import suggestion_chain
from fastapi import FastAPI, WebSocket
import json

app = FastAPI()

@app.get("/")
async def get_root():
    return {"Hello": "World"}

@app.websocket("/ws")
async def get_suggestion(websocket: WebSocket):
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
                
                # Get suggestion
                suggestion = suggestion_chain.invoke({
                    "prefix_text": prefix_text, 
                    "suffix_text": suffix_text
                })
                
                # Send JSON response
                response = {"suggestion": suggestion.suggestion}
                await websocket.send_text(json.dumps(response))
                
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



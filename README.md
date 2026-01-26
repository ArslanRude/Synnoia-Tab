# Synnoia-Tab

**Intelligent Line Completion Engine for Document Editors**

Synnoia-Tab is a powerful AI-powered line completion system that provides context-aware text suggestions to enhance writing productivity. Built with FastAPI and powered by Groq's LLaMA models, it offers real-time text completion through a clean WebSocket API.

## 🚀 Features

- **Real-time Suggestions**: Get instant text completions as you type
- **Context-Aware**: Understands both prefix and suffix context for accurate suggestions
- **WebSocket API**: Efficient, low-latency communication
- **JSON Responses**: Clean, structured output format
- **Error Handling**: Robust error management and recovery
- **FastAPI Backend**: Modern, high-performance web framework

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **AI Model**: Groq LLaMA-3.3-70b-Versatile
- **Language**: Python 3.8+
- **API Protocol**: WebSocket
- **Data Format**: JSON

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Groq API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Synnoia-Tab
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate.bat
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   ```

## 🚀 Quick Start

1. **Start the server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Test the API**
   - Open `http://localhost:8000` in your browser to see the API status
   - Use WebSocket client to connect to `ws://localhost:8000/ws`

## 📡 API Documentation

### WebSocket Endpoint

**URL**: `ws://localhost:8000/ws`

#### Request Format
```json
{
  "prefix_text": "Text before cursor",
  "suffix_text": "Text after cursor"
}
```

#### Response Format
```json
{
  "suggestion": "AI-generated completion text"
}
```

#### Error Response
```json
{
  "error": "Error description"
}
```

### HTTP Endpoints

#### GET `/`
Returns API status and basic information.

```json
{
  "Hello": "World"
}
```

## 💻 Usage Examples

### JavaScript/TypeScript Client

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    console.log('Connected to Synnoia-Tab');
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    if (response.suggestion) {
        console.log('Suggestion:', response.suggestion);
        // Apply suggestion to your editor
    }
};

// Send request for suggestion
function getSuggestion(prefix, suffix) {
    const message = {
        prefix_text: prefix,
        suffix_text: suffix
    };
    ws.send(JSON.stringify(message));
}

// Example usage
getSuggestion("Hello ", "world");
```

### Python Client

```python
import asyncio
import websockets
import json

async def get_suggestion(prefix, suffix):
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        message = {
            "prefix_text": prefix,
            "suffix_text": suffix
        }
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        result = json.loads(response)
        return result.get("suggestion", "")

# Usage
suggestion = asyncio.run(get_suggestion("Hello ", "world"))
print(f"Suggestion: {suggestion}")
```

### cURL Testing

```bash
# Install wscat for WebSocket testing
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws

# Send message (after connecting)
{"prefix_text": "Hello ", "suffix_text": "world"}
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app
```

### Manual Testing

1. **Start the server**: `uvicorn app.main:app --reload`
2. **Open test HTML**: Open `test_websocket.html` in browser
3. **Run Python client**: `python test_client.py`

## 🏗️ Project Structure

```
Synnoia-Tab/
├── app/
│   ├── main.py                 # FastAPI application and WebSocket endpoint
│   ├── model/
│   │   └── suggestion_model.py # AI model configuration and chain
│   └── prompt/
│       └── prompts.py         # System prompts and templates
├── test_websocket.html        # HTML test client
├── test_client.py             # Python test client
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
└── README.md                  # This file
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key | Yes |

### Model Parameters

The AI model can be configured in `app/model/suggestion_model.py`:

- **Model**: `llama-3.3-70b-versatile`
- **Temperature**: 0.2 (lower for more deterministic output)
- **Max Tokens**: 64 (short completions)
- **Stop Sequences**: `["\n\n"]` (stop at double newline)

## 🚨 Error Handling

The WebSocket API includes comprehensive error handling:

- **JSON Parse Errors**: Invalid JSON format
- **Processing Errors**: AI model issues
- **Connection Errors**: WebSocket disconnection
- **Validation Errors**: Missing required fields

All errors are returned in JSON format with descriptive messages.

## 🔧 Development

### Adding New Features

1. **Model Updates**: Modify `app/model/suggestion_model.py`
2. **Prompt Changes**: Update `app/prompt/prompts.py`
3. **API Endpoints**: Add to `app/main.py`
4. **Testing**: Create tests in appropriate directories

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where applicable
- Add docstrings to functions and classes
- Keep functions small and focused

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include error logs and environment details

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for providing fast AI inference
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [LangChain](https://python.langchain.com/) for AI model integration

---

**Synnoia-Tab** - Making writing smarter, one suggestion at a time. 🚀

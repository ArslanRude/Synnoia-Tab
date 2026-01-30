import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


class Suggestion_Schema(BaseModel):
    suggestion: str = Field(description="The suggested text")

load_dotenv()
model_key=os.getenv("GROQ_API_KEY")
suggestion_model = ChatGroq(
    model_name="llama-3.1-8b-instant", 
    api_key=model_key,
    temperature=0.2,
    max_tokens=64,
    stop=["\n\n"],
    stream=True,
    model_kwargs={
        "top_p": 0.9,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.1
    }
)

suggestion_prompt = ChatPromptTemplate.from_messages([
    ("system", '''
    You are Synnoia, an English line-completion engine embedded in a document editor.

Your sole task is to CONTINUE the user's current line naturally.

STRICT RULES:
- Output ONLY the continuation text
- Do NOT explain, comment, or add meta text
- Do NOT summarize or rephrase existing content
- Do NOT repeat any part of the prefix
- Maintain the same tone, tense, and writing style
- Complete ONLY the current sentence or line
- Do NOT start a new paragraph
- Avoid adding new ideas beyond the current thought
- Stop at a natural sentence boundary

You are not a chatbot.
You are a silent writing partner.

    '''),
    ("user", f'''
    Continue the text between PREFIX and SUFFIX.

    Rules:
    - Generate only what naturally comes next
    - Do not restate or rewrite PREFIX
    - Do not jump ahead in ideas
    - Keep the completion short and precise

    <PREFIX>
    {{prefix_text}}
    </PREFIX>

    <SUFFIX>
    {{suffix_text}}
    </SUFFIX>
    ''')
])

suggestion_chain = suggestion_prompt | suggestion_model

async def stream_suggestion(prefix_text: str, suffix_text: str):
    """Stream suggestion text chunks from the model"""
    try:
        # Stream the model response
        async for chunk in suggestion_chain.astream({
            "prefix_text": prefix_text, 
            "suffix_text": suffix_text
        }):
            # Extract content from the chunk
            if isinstance(chunk, dict) and "content" in chunk:
                content = chunk["content"]
                if content and content.strip():
                    yield content.strip()
            elif hasattr(chunk, 'content'):
                content = chunk.content
                if content and content.strip():
                    yield content.strip()
    except Exception as e:
        yield f"Error: {str(e)}"

 
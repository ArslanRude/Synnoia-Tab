import sys
import os
import hashlib
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from cachetools import LRUCache

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from app.checkpoints.main import apply_checkpoints

class Suggestion_Schema(BaseModel):
    suggestion: str = Field(description="The suggested text")

load_dotenv()
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.3,
    thinking_budget=0,
    max_tokens=64,
    stop=["\n\n"],
    top_p=0.9,
    top_k=40
)

suggestion_model = model.with_structured_output(schema=Suggestion_Schema.model_json_schema(),method="json_schema")

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

# Global LRU cache and lock
cache = LRUCache(maxsize=500)
cache_lock = asyncio.Lock()

def _generate_cache_key(prefix_text: str, suffix_text: str) -> str:
    """Generate MD5 cache key from normalized prefix and suffix."""
    # Strip each part individually before combining
    normalized_prefix = prefix_text.strip().lower()
    normalized_suffix = suffix_text.strip().lower()
    normalized = f"{normalized_prefix}|||{normalized_suffix}"
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


async def get_suggestion(prefix_text: str, suffix_text: str):
    """Get complete suggestion from the model with LRU caching.
    
    Returns:
        tuple: (suggestion_text, cache_hit_boolean)
    """
    cache_key = _generate_cache_key(prefix_text, suffix_text)
    
    async with cache_lock:
        cached_raw = cache.get(cache_key)
    
    if cached_raw is not None:
        # Apply checkpoints to cached result with current context (handles CP3 space injection)
        result = apply_checkpoints(cached_raw, prefix_text, suffix_text)
        return (result, True)
    
    # Cache miss - call the model
    try:
        raw = await suggestion_chain.ainvoke({
            "prefix_text": prefix_text,
            "suffix_text": suffix_text
        })
        raw_text = raw['suggestion']
        
        # Bypass checkpoints for errors
        if raw_text.startswith("Error:"):
            return (raw_text, False)
        
        # Apply all post-processing checkpoints
        result = apply_checkpoints(raw_text, prefix_text, suffix_text)
        
        # Cache the raw result (not checkpoint-processed) for consistent replay
        if raw_text is not None and not raw_text.startswith("Error:"):
            async with cache_lock:
                cache[cache_key] = raw_text
        
        return (result, False)
    except Exception as e:
        return (f"Error: {str(e)}", False)

# Cache statistics for monitoring
def get_cache_stats():
    """Get current cache statistics."""
    return {"size": cache.currsize, "maxsize": cache.maxsize}



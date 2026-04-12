import os
import re
import hashlib
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from cachetools import LRUCache


class Suggestion_Schema(BaseModel):
    suggestion: str = Field(description="The suggested text")

load_dotenv()
model = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
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

# Compiled regex patterns for checkpoints (performance)
_SENTENCE_END = re.compile(r'[.!?]\s*$')
_PARA_BREAK   = re.compile(r'\n{2,}')
_MULTI_SPACE  = re.compile(r'  +')

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

def _apply_checkpoints(suggestion: str, prefix: str, suffix: str) -> str | None:
    """Apply all post-processing checkpoints to the suggestion.
    
    Returns the cleaned suggestion string, or None if it should be discarded.
    """
    # CP1 — Empty or whitespace-only output
    if not suggestion or not suggestion.strip():
        return None
    
    # CP2 — Exact duplicate of prefix tail
    if prefix.rstrip().endswith(suggestion.strip()):
        return None
    
    # CP3 — Space injection / removal at boundaries
    # Handle prefix leading space
    if prefix:
        if prefix[-1] not in ' \t\n\r([{"\'':
            # Prefix doesn't end with space - suggestion needs leading space
            if suggestion and suggestion[0] not in ' \t\n\r':
                suggestion = " " + suggestion
        else:
            # Prefix ends with space - strip leading space from suggestion to avoid double space
            if suggestion and suggestion[0] in ' \t\n\r':
                suggestion = suggestion.lstrip()
    
    # Handle suffix trailing space
    if suffix:
        if suffix[0] not in ' \t\n\r.,;:!?)]}\'"':
            # Suffix doesn't start with space/punct - suggestion needs trailing space
            if suggestion and suggestion[-1] not in ' \t\n\r':
                suggestion = suggestion + " "
        else:
            # Suffix starts with space/punct - strip trailing space from suggestion to avoid double space
            if suggestion and suggestion[-1] in ' \t\n\r':
                suggestion = suggestion.rstrip()
    
    # CP4 — Capitalise after sentence-ending punctuation
    if _SENTENCE_END.search(prefix.rstrip()):
        lstripped = suggestion.lstrip()
        leading = suggestion[:len(suggestion) - len(lstripped)]
        if lstripped:
            suggestion = leading + lstripped[0].upper() + lstripped[1:]
    
    # CP5 — Prefix-repetition strip
    prefix_words = prefix.split()
    for n in range(min(4, len(prefix_words)), 0, -1):
        tail = " ".join(prefix_words[-n:])
        stripped_sugg = suggestion.lstrip()
        if stripped_sugg.lower().startswith(tail.lower()):
            leading = suggestion[:len(suggestion) - len(stripped_sugg)]
            suggestion = leading + stripped_sugg[len(tail):]
            break
    
    # Re-run CP1 after CP5
    if not suggestion or not suggestion.strip():
        return None
    
    # CP6 — Suffix-overlap strip
    if suffix:
        suffix_head = suffix.lstrip()[:40]
        for length in range(min(len(suffix_head), len(suggestion)), 2, -1):
            if suggestion.rstrip().endswith(suffix_head[:length]):
                suggestion = suggestion.rstrip()[:-length]
                break
    
    # Re-run CP1 after CP6
    if not suggestion or not suggestion.strip():
        return None
    
    # CP7 — Multi-paragraph and newline guard
    para_match = _PARA_BREAK.search(suggestion)
    if para_match:
        suggestion = suggestion[:para_match.start()]
    
    if "\n" in suggestion:
        suggestion = suggestion[:suggestion.index("\n")]
    
    # Re-run CP1 after CP7
    if not suggestion or not suggestion.strip():
        return None
    
    # CP8 — Whitespace normalisation
    suggestion = _MULTI_SPACE.sub(' ', suggestion)
    suggestion = suggestion.rstrip()
    
    # Re-apply suffix boundary check after CP8 (it may have stripped needed trailing space)
    if suffix and suffix[0] not in ' \t\n\r.,;:!?)]}\'"':
        if suggestion and suggestion[-1] not in ' \t\n\r':
            suggestion = suggestion + " "
    
    # CP9 — Minimum meaningful length
    if len(suggestion.strip()) < 3:
        return None
    
    return suggestion

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
        result = _apply_checkpoints(cached_raw, prefix_text, suffix_text)
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
        result = _apply_checkpoints(raw_text, prefix_text, suffix_text)
        
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


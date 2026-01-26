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
    model_name="llama-3.3-70b-versatile", 
    api_key=model_key,
    temperature=0.2,
    max_tokens=64,
    stop=["\n\n"],
    model_kwargs={
        "top_p": 0.9,
        "frequency_penalty": 0.8,
        "presence_penalty": 0.0
    }
)
suggestion_model = suggestion_model.with_structured_output(Suggestion_Schema, method="function_calling")

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




    

 
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class Suggestion_Schema(BaseModel):
    suggestion: str = Field(description="The suggested text")

load_dotenv()
model = ChatGoogleGenerativeAI(model="gemini-3-flash-preview",
                               api_key=os.getenv("GOOGLE_API_KEY"),
                               temperature= 0.3,
                               thinking_budget=0,
                               max_tokens= 64,
                               stop=["\n\n"],
                               top_p= 0.9,
                               top_k= 40)
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

result = suggestion_chain.invoke({
    "prefix_text": "My name is Arslan. I am a football player.",
    "suffix_text": ""
})
print(result["suggestion"])

# print(model.invoke("Hello"))
                               
                               


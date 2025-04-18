# src/table_generator.py
import openai
from config import OPENAI_API_KEY
from src.prompts import TABLES_DEFAULT_SYSTEM_PROMPT

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_tables(system_prompt=TABLES_DEFAULT_SYSTEM_PROMPT, image_base64=None, mime_type=None, user_prompt=""):
    full_prompt = system_prompt
    if user_prompt:
        full_prompt += f"\n\nAdditional Instructions: {user_prompt}"
    
    messages = [
        {"role": "system", "content": full_prompt},
        {"role": "user", "content": [
            {"type": "text", "text": "Here is the diagram:"},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}} if image_base64 and mime_type else {"type": "text", "text": "No image provided."}
        ]}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
        max_tokens=2000
    )
    return response.choices[0].message.content, messages

def refine_tables(messages, feedback):
    messages.append({"role": "user", "content": feedback})
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
        max_tokens=2000
    )
    return response.choices[0].message.content, messages
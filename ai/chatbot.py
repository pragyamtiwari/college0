import os
from openai import OpenAI
from ai.vector_store import query_vector_store

def get_chatbot_response(user_input, user_role='visitor'):
    # 1. Search Vector Store
    vector_answer = query_vector_store(user_input, user_role)
    if vector_answer:
        return vector_answer, False # is_llm = False
    
    # 2. LLM Fallback
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        return "I'm sorry, my LLM brain is not configured with an API key yet.", False

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are an AI assistant for College0, a graduate college. Answer the following user question. User role: {user_role}"},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content, True # is_llm = True
    except Exception as e:
        print(f"LLM Error: {e}")
        return "I'm sorry, I'm having trouble connecting to my brain right now.", False

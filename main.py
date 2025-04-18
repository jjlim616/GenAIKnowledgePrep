import google.generativeai as genai
from config import GEMINI_API_KEY 

# Configure the API client
genai.configure(api_key=GEMINI_API_KEY)

def fetch_accessible_models():
    # Get all models from the API
    all_models = genai.list_models()
    accessible_models = []

    # Simple test prompt
    test_prompt = "Hello, this is a test."

    # Test each model
    for model in all_models:
        if 'generateContent' in model.supported_generation_methods:  
            model_name = model.name  
            print(f"Testing model: {model_name}")
            try:
                gen_model = genai.GenerativeModel(model_name)
                response = gen_model.generate_content(test_prompt)
                accessible_models.append(model_name)
                print(f"✅ {model_name} is accessible with your API key")
            except Exception as e:
                print(f"❌ {model_name} not accessible: {str(e)}")

    return accessible_models

if __name__ == "__main__":
    print("Fetching models accessible with your API key...")
    accessible_models = fetch_accessible_models()
    print("\nAccessible models:")
    for model in accessible_models:
        print(f"- {model}")
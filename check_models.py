import os
import sys
from google import genai

# Add project root to path to get config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import ChatbotConfig
    config = ChatbotConfig()
    api_key = config.gemini_api_key
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        sys.exit(1)

    print(f"Checking models with API Key: {api_key[:4]}...{api_key[-4:]}")

    client = genai.Client(api_key=api_key)
    
    print("\nListing available models...")
    # List models that support generateContent
    for model in client.models.list():
        print(f"- {model.name}")
        
    print("\nPlease verify which of the above 'models/...' names you want to use.")

except Exception as e:
    print(f"\nError listing models: {e}")
    # Fallback to try legacy if new fails completely
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        print("\nTrying legacy client list_models...")
        for m in legacy_genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e2:
        print(f"Legacy list failed too: {e2}")

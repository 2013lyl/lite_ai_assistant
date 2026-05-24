import json

def return_data() -> dict:
    with open("data/model_data.json", mode="r", encoding="utf-8") as f:
        content = f.read()
        model_data = json.loads(content)
        model_name = model_data['model_name']
    
    with open("data/ollama_data.json", mode="r", encoding="utf-8") as f:
        content = f.read()
        ollama_data = json.loads(content)
        ollama_base_url = ollama_data['ollama_base_url']

    ans = {
        "model_name": model_name,
        'ollama_base_url': ollama_base_url
    }

    return ans

def write_data(new_model_data_settings, new_ollama_data_settings):
    with open("data/model_data.json", mode="w", encoding="utf-8") as writer:
        json.dump(new_model_data_settings, writer)

    with open("data/ollama_data.json", mode="w", encoding="utf-8") as writer:
        json.dump(new_ollama_data_settings, writer)

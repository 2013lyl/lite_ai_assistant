import json

def return_data() -> dict:
    with open("data/model_data.json", mode="r", encoding="utf-8") as f:
        content = f.read()
        model_data = json.loads(content)
        model_name = model_data['model_name']

    ans = {
        "model_name": model_name
    }

    return ans

def write_data(new_model_data_settings):
    with open("data/model_data.json", mode="w", encoding="utf-8") as writer:
        json.dump(new_model_data_settings, writer)

import requests
import json


def query_gpt(question):

    prompt = {
        "modelUri": "gpt://b1gtqld3kg7to2drbhru/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": "You're a smart museum assistant."
            },
            {
                "role": "assistant",
                "text": "You have to answer the user's questions"
            },
            {
                "role": "user",
                "text": question
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Api-Key "
    }

    response = requests.post(url, headers=headers, json=prompt)
    result = response.text

    return json.loads(result)["result"]["alternatives"][0]["message"]["text"]

    # print(text)

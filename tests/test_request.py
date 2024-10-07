import requests


if __name__ == "__main__":
    query = "I am a data engineer looking for a new job in Berlin in Zalando. Are there any relevant positions?"

    print("query: ", query)

    url = "http://localhost:8000/query"


    data = {"query": query}

    response = requests.post(url, json=data)

    print(response.json())


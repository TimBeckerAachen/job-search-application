import requests


if __name__ == "__main__":
    query = "I am a data scientist interested in the automotive industry. Is there currently a good job opportunity for me?"

    print("query: ", query)

    url = "http://localhost:8000/query"


    data = {"query": query}

    response = requests.post(url, json=data)

    print(response.json())
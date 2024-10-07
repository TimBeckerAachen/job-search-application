import requests


if __name__ == "__main__":
    # query = "I am a data scientist interested in the automotive industry. Is there currently a good job opportunity for me?"
    query = "I am a software developer interested in e-commerce. Which current job opening would you recommend to me?"
    print("query: ", query)

    url = "http://localhost:8000/query"
    data = {"query": query}
    resp_query = requests.post(url, json=data)

    print(resp_query.json())

    conversation_id = resp_query.json()["conversation_id"]

    url_feedback = "http://localhost:8000/feedback"
    feedback_data = {
        "conversation_id": conversation_id,
        "feedback": 1
    }
    resp_feedback = requests.post(url_feedback, json=feedback_data)

    print(resp_feedback.json())
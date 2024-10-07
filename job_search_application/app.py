import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

import job_search_application.db as db
from job_search_application.rag import rag


app = FastAPI()


class QueryRequest(BaseModel):
    query: str


class FeedbackRequest(BaseModel):
    conversation_id: str
    feedback: int


@app.post("/query")
async def handle_query(request: QueryRequest) -> Dict[str, Any]:
    if not request.query:
        raise HTTPException(status_code=400, detail="No query provided")

    conversation_id = str(uuid.uuid4())
    response_data = rag(request.query)

    result = {
        "conversation_id": conversation_id,
        "query": request.query,
        "response": response_data["response"],
    }

    db.save_conversation(
        conversation_id=conversation_id,
        query=request.query,
        response_data=response_data,
    )

    return result


@app.post("/feedback")
async def handle_feedback(request: FeedbackRequest) -> Dict[str, str]:
    if request.feedback not in [1, -1]:
        raise HTTPException(status_code=400, detail="Invalid input")

    db.save_feedback(
        conversation_id=request.conversation_id,
        feedback=request.feedback,
    )

    return {
        "message": f"Feedback received for conversation {request.conversation_id}: {request.feedback}"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
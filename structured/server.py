from fastapi import FastAPI, Query, responses
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import json
import asyncio
from pydantic import BaseModel


from query import Query

query_class = Query()


class QueryRequest(BaseModel):
    query: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/query/")
async def post_query(request: QueryRequest):
    """
    entry point for the user_query for the server

    Args:
        request: QueryRequest(query:str)

    Returns:
        response: {"answer":str}
    """
    try:
        print("Entered Query request")
        if not request.query:
            print("Empty query")
            return {"answer": "Please ask a valid question"}

        user_query = request.query
        COLLECTION = "both"
        answer = query_class.query(user_query=user_query, collection_name=COLLECTION)
        return {"answer": answer}
    except Exception as e:
        print(f"Error occured:{e}")
        return {"error": e, "message": "Sorry an Error occured"}

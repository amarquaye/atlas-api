from decouple import config

from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse

import requests

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


app = FastAPI(
    title="Atlas",
    summary="Hallucination-detecting API.",
    description="Search the web for queries and compare results with LLM to detect and mitigate hallucinations.\nDeveloped by Jesse Amarquaye.",
    version="0.0.1",
)


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/", response_class=PlainTextResponse)
async def home(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Page is currently under development...")


@app.get("/api")
@limiter.limit("3/minute")
async def search(
    request: Request,
    query: str = Query(None, description="Query to search the web"),
) -> dict:
    """Search the web.

    Crawls the web for queries and returns the results of he search in json.

    Parameters
    ----------
    query : str, optional
        Search query, by default Query(None, description="Query to search the web")

    Returns
    -------
    json
        Response from the search.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": config("GCSC_API_KEY"),
        "cx": config("GOOGLE_SEARCH_ENGINE_ID"),
    }

    response = requests.get(url, params=params).json()
    return {"query": query, "response": response["items"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

from decouple import config

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import requests

from .scraper import scraper

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


app = FastAPI(
    title="Atlas",
    summary="Hallucination-detecting API.",
    description="Search the web for queries and compare results with LLM to detect and mitigate hallucinations.\nDeveloped by Jesse Amarquaye.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="src/static"), name="static")

templates = Jinja2Templates(directory="src/templates")


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> HTMLResponse:
    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get("/api", tags=["Test endpoints"])
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

    response = requests.get(url, params=params).json()["items"]

    # Extracting the relevant information into a dictionary
    results = {}
    for index, item in enumerate(response, start=1):
        results[index] = {
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "link": item.get("link"),
        }

    return results


@app.get("/api/s", tags=["Test endpoints"])
@limiter.limit("3/minute")
async def scrape(
    request: Request,
    query: str = Query(None, description="Query to search the web"),
    index: int = Query(1, description="The search index", le=10),
) -> dict:
    """Scrape the web.

    Crawls the web for queries and returns the content of he search in json.

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

    response = requests.get(url, params=params).json()["items"]

    # Extracting the relevant information into a dictionary
    results = {}
    for idx, item in enumerate(response, start=1):
        results[idx] = {
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "link": item.get("link"),
        }

    # return results

    # Return the first result
    link1 = response[index]["link"]

    return {"content": await scraper(link1)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

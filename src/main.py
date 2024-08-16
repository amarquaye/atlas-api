import aiohttp

from decouple import config

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import primp

from .gemini import generate_query
from .utils import scraper, reader

# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded


app = FastAPI(
    title="Atlas API",
    summary="Hallucination-detecting API.",
    description="Search the web for queries and compare results with LLM to detect and mitigate hallucinations.\nDeveloped by Jesse Amarquaye.",
    version="0.3.0",
)

app.mount("/static", StaticFiles(directory="src/static"), name="static")

templates = Jinja2Templates(directory="src/templates")


# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> HTMLResponse:
    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get("/api", tags=["Endpoints"])
# @limiter.limit("3/minute")
async def search(
    request: Request,
    query: str = Query(None, description="Query to search the web"),
) -> dict:
    """Search the web.

    Crawls the web for queries and returns the results of he search in json.

    Parameters
    ----------
    query : str, optional
        Query to search the web.

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

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as response:
            response = await response.json()
            response = response["items"]

        return {
            idx: {
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link"),
            }
            for idx, item in enumerate(response, start=1)
        }


@app.get("/verify", tags=["Beta endpoints"])
async def verify(
    request: Request, query: str = Query(None, description="Enter query")
) -> dict:
    """Detect and mitigate hallucination.

    Scans through a query, compares result from LLM with search results from google to detect and mitigate hallucinations.

    Parameters
    ----------
    query : str, optional
        Query from user.

    Returns
    -------
    dict
        Verified results from the web.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": config("GCSC_API_KEY"),
        "cx": config("GOOGLE_SEARCH_ENGINE_ID"),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as response:
            response = await response.json()
            response = response["items"]
    # response = primp.get(url=url, params=params).json()["items"]

    resp = primp.get(response[0]["link"], impersonate="chrome_127")
    return {"result": resp.text_markdown, "source": response[0]["link"]}


@app.get("/api/scraper", tags=["Endpoints"])
# @limiter.limit("3/minute")
async def scrape(
    request: Request,
    query: str = Query(None, description="Query to search the web"),
    index: int = Query(1, description="The search index", le=10),
) -> dict:
    """Crawls the web and returns the content.

    Parameters
    ----------
    query : str, optional
        Query to search the web.
    index : int, optional
        The search index. Should be less than or equal to 10 (since the limit of the results is 10).

    Returns
    -------
    json
        Content of the site requested (index).
    """

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": config("GCSC_API_KEY"),
        "cx": config("GOOGLE_SEARCH_ENGINE_ID"),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as response:
            response = await response.json()
            response = response["items"]

    link = response[index]["link"]

    return {"content": scraper(link), "source": link}


# TODO: Remove these soon as they are just a proof of concept.
@app.get("/api/jina/search", tags=["Beta endpoints"])
# @limiter.limit("3/minute")
async def jina_search(
    request: Request,
    query: str = Query(None, description="Query to search the web"),
) -> dict:
    """Search the web.

    Crawls the web for queries and returns the results of he search in json.

    Parameters
    ----------
    query : str, optional
        Query to search the web.

    Returns
    -------
    json
        Response from the search.
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(url="https://s.jina.ai/" + query) as response:
            response = await response.text()
            return {"response": response}


@app.get("/api/scraper/jina/reader", tags=["Beta endpoints"])
# @limiter.limit("3/minute")
async def jina_reader(
    request: Request,
    query: str = Query(None, description="Query to search the web"),
    index: int = Query(1, description="The search index", le=10),
) -> dict:
    """Crawls the web and returns the content.

    Parameters
    ----------
    query : str, optional
        Query to search the web.
    index : int, optional
        The search index. Should be less than or equal to 10 (since the limit of the results is 10).

    Returns
    -------
    json
        Content of the site requested (index).
    """

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": config("GCSC_API_KEY"),
        "cx": config("GOOGLE_SEARCH_ENGINE_ID"),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as response:
            response = await response.json()
            response = response["items"]

    link = response[index]["link"]

    return {"content": reader(link), "source": link}


# TODO: This is a test feature, might be implemented in the future.
@app.get("/api/refine", tags=["Beta endpoints"])
# @limiter.limit("3/minute")
def refine_text(
    request: Request, query: str = Query(None, description="Search query")
) -> dict:
    return {"Query": generate_query(query)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

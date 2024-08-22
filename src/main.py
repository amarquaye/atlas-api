import aiohttp

from decouple import config

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import primp

from .gemini import cmp, generate_query

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


app = FastAPI(
    title="Atlas API",
    summary="Hallucination-detecting API.",
    description="Search the web for queries and compare results with LLM to detect and mitigate hallucinations.\nDeveloped by Jesse Amarquaye.",
    version="1.0.2",
)

origins = ["https://atlasproject-brown.vercel.app"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="src/static"), name="static")

templates = Jinja2Templates(directory="src/templates")


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request) -> HTMLResponse:
    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get("/try", response_class=HTMLResponse, include_in_schema=False)
def test(request: Request) -> HTMLResponse:
    context = {"request": request}
    return templates.TemplateResponse("try.html", context)


@app.get("/api", tags=["Endpoints"])
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


@app.get("/verify", tags=["Endpoints"])
@limiter.limit("3/minute")
async def verify(
    request: Request,
    llm_query: str = Query(None, description="Enter LLM input"),
    llm_response: str = Query(None, description="Enter LLM output"),
) -> dict:
    """Detect and mitigate hallucination.

    Scans through a query, compares result from LLM with search results from google to detect and mitigate hallucinations.

    Parameters
    ----------
    llm_query : str, optional
        Query from user.
    llm_response : str, optional
        Response from LLM.

    Returns
    -------
    json
        Verified results from the web.
    """
    query = generate_query(llm_query)
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

    if str(response[0]["link"]).startswith("https://www.quora.com"):
        resp = primp.get(
            url="https://r.jina.ai/" + str(response[0]["link"]),
            impersonate="chrome_127",
        )
    elif str(response[0]["link"]).startswith("https://www.findlaw.com"):
        resp = primp.get(
            url="https://r.jina.ai/" + str(response[0]["link"]),
            impersonate="chrome_127",
        )
    else:
        resp = primp.get(response[0]["link"], impersonate="chrome_127")

    return {
        "response": cmp(
            llm_response=llm_response, search_result=resp.text_markdown
        ),
        "source": response[0]["link"],
    }


@app.get("/search", tags=["Endpoints"])
@limiter.limit("3/minute")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

import aiohttp

from decouple import config

from fastapi import FastAPI, Query, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
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
    description="🌐Search the web for queries and compare results with LLM to detect and mitigate hallucinations.",
    version="1.0.5",
    contact={
        "name": "Jesse Amarquaye",
        "url": "https://atlasproject-phi.vercel.app",
        "email": "engineeramarquaye@gmail.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/amarquaye/atlas-api/blob/master/LICENSE",
    },
)

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

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


@app.get(
    "/api",
    name="api",
    tags=["Endpoints"],
    summary="Returns the results of a google search in json.",
)
@limiter.limit("3/minute")
async def search(
    request: Request,
    query: str = Query(description="Query to search the web"),
) -> dict:
    """
    **Search the web**.

    Returns the results from a _google search_ in json.

    Parameters
    ----------
    query : str,
        _Query to search the web._

    Returns
    -------
    json
        _Response from the google search._
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": config("GCSC_API_KEY"),
        "cx": config("GOOGLE_SEARCH_ENGINE_ID"),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params) as response:
                response = await response.json()
                response = response["items"]
    except KeyError:
        return {
            "response": "Oops, something went wrong... Please try again later!",
            "source": "Your search query couldn't yield any relevant results from the web.",
        }
    else:
        return {
            idx: {
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link"),
            }
            for idx, item in enumerate(response, start=1)
        }


@app.get(
    "/verify",
    name="verify",
    tags=["Endpoints"],
    summary="Detects and flags hallucinations in an LLM's response.",
)
@limiter.limit("3/minute")
async def verify(
    request: Request,
    llm_query: str = Query(title="LLM query", description="Enter LLM input"),
    llm_response: str = Query(
        title="LLM response", description="Enter LLM output"
    ),
) -> dict:
    """
    **Detect and mitigate hallucinations**.

    _Scans_ through a query, _compares_ result from LLM with search results from google to detect and mitigate hallucinations.

    Takes **two** parameters; the **first** one being the query given to the LLM and the **second** one being the response from the LLM.

    Parameters
    ----------
    llm_query : str,
        _Query from user._

    llm_response : str,
        _Response from LLM._

    Returns
    -------
    json
        _Verified results from the web._
    """
    query = generate_query(llm_query)
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": config("GCSC_API_KEY"),
        "cx": config("GOOGLE_SEARCH_ENGINE_ID"),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params) as response:
                response = await response.json()
                response = response["items"]
    except KeyError:
        return {
            "response": "Oops, something went wrong... Please try again later!",
            "source": "Your search query couldn't generate any results.",
        }

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
    elif str(response[0]["link"]).startswith("https://www.youtube.com"):
        resp = primp.get(
            url=response[1]["link"],
            impersonate="chrome_127",
        )
    else:
        resp = primp.get(response[0]["link"], impersonate="chrome_127")

    return StreamingResponse(
        content=cmp(
            llm_response=llm_response,
            search_result=resp.text_markdown,
            source=str(response[0]["link"]),
        ),
        media_type="application/json",
    )


@app.get(
    "/search",
    name="search",
    tags=["Endpoints"],
    summary="Perform a search using the Jina Search API.",
)
@limiter.limit("3/minute")
async def jina_search(
    request: Request,
    query: str = Query(description="Query to search the web"),
) -> dict:
    """
    **Search the web**.

    _Crawls_ the web for queries and returns the results in json.

    Enter a search query and it will respond with a json object containing your search results rendered in markdown for LLMs to parse or understand easily.

    This endpoint can also be useful when _training_ LLMs.

    Parameters
    ----------
    query : str
        _Query to search the web._

    Returns
    -------
    json
        _Response from the search._
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url="https://s.jina.ai/" + query
            ) as response:
                response = await response.text()
                return {"response": response}
    except Exception:
        return {
            "response": "Oops... Something went wrong. Please try agin later!"
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

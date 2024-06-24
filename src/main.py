from fastapi import FastAPI, Query

app = FastAPI(
    title="Atlas",
    summary="Hallucination-detecting API.",
    description="Search the web for queries and compare results with LLM to detect and mitigate hallucinations.",
    version="0.0.1",
)


@app.get("/api")
async def search(
    query: str = Query(
        ...,
        description="Query to search the web",
    ),
):
    """Search the web.

    Parameters
    ----------
    query : str
        Query to search the web.

    Returns
    -------
    json
        Results from searching the web.
    """
    return {"query": query}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

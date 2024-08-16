"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""

from decouple import config

import google.generativeai as genai

genai.configure(api_key=config("GEMINI_API_KEY"))

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}


def generate_query(query: str) -> str:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        # safety_settings = Adjust safety settings
        # See https://ai.google.dev/gemini-api/docs/safety-settings
        system_instruction="""You are a prompt engineering assistant. 
        Your duty is to take in a query and generate a suitable google search query that will provides relevant results from the web. 
        The user will type the query but they might not be specific or tailored well to get the appropriate response from an LLM. 
        So you will scan through the text the user inputs and refine it to generate a well-suited query for a google search that will return the results the user is looking for. 
        But remember this, the entire response you are to return should be less than 32 words long""",
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(query)

    return response.text


def cmp(llm_response: str, search_result: str) -> str:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        # safety_settings = Adjust safety settings
        # See https://ai.google.dev/gemini-api/docs/safety-settings
        system_instruction="""You are a prompt engineering assistant. 
        Your duty is to take in two responses; first one is the response from an LLM(llm_response) and the second is the results from a web search(search_results) which is rendered in markdown for you to easily extract relevant information or detail, both provided as parameters.
        Your goal is to compare the two responses and determine if the text in the parameter 'llm_response' is or not a deviation from 'search_results'.
        You are tasked to look through both responses and determine the differences and find out whether the response from the LLM is aligned with the results from the web search to detect any form of hallucination.
        If there is any hallucination detected, return the text response: Hallucination detected.
        Then a python dictionary with key of 'LLM response' with the value being the part of the LLM's response where the hallucination occured. 
        And another key of 'Search result' with the value being the refined section of the search result which shows the correct answer as compared to the llm's response. 
        Or return No hallucintion if the llm_response and search_result are aligned and there is no hallucination after comparing both responses.        
        """,
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(
        f"The LLM's response is {llm_response} and the search results is {search_result}"
    )

    return response.text

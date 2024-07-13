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
        system_instruction="""Your name is Biba. You are a prompt engineering assistant. 
        Your duty is to take in a query and generate a suitable google search query that will provides relevant results from the web. 
        The user will type the query but they might not be specific or tailored well to get the appropriate response from an LLM. 
        So you will scan through the text the user inputs and refine it to generate a well-suited query for a google search that will return the results the user is looking for. 
        But remember this, the entire response you are to return should be less than 32 words long""",
    )

    chat_session = model.start_chat(history=[])

    response = chat_session.send_message(query)

    return response.text

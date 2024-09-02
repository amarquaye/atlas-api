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
    "response_mime_type": "application/json",
}


def generate_query(query: str) -> str:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        # safety_settings = Adjust safety settings
        # See https://ai.google.dev/gemini-api/docs/safety-settings
        system_instruction="""You are a prompt engineering assistant.
        You are to follow the **INSTRUCTIONS** below:
        1. A string query will be provided to you as parameter.
        2. Your duty is to look through the query string from the beginning to the end and **generate a suitable search query for google**.
        3. The query string that you are to produce must **match or must be aligned** with what the user is trying to search for on google.
        4. **Do not deviate** or provide an irrelevant google search query.
        5. Sometimes the string query from the user might be **ambiguous** or indirect but you are discover what the user is looking for.
        6. The google search query you are to return can include some **google dorks techniques** like **intext**, **intitle** or any technique to find **exactly** what the user is looking for.  
        7. **Your response shouldn't contain** any words like **Google Search** or special characters like **\n**.
        8. Just return a **well suited** and relevant google search query that will return relevant results from the google search. 
        9. **Your response should not be longer than 32 words**.
        10. Keep it as precise as possible to return the **best** results from google. 
        """,
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(f"The user's string query is {query}")

    return response.text


def cmp(llm_response: str, search_result: str, source: str):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        # safety_settings = Adjust safety settings
        # See https://ai.google.dev/gemini-api/docs/safety-settings
        system_instruction="""You are a hallucination detecting assistant. 
        You are to follow the following **INSTRUCTIONS**:
        1. You duty is to take three parameters; an **llm_response**, **search_result** and **source**.
        2. **llm_response** is the response provided by an LLM.
        3. **search_result** is the results from searching the web which is usually rendered in markdown for you to easily extract all relevant content.
        4. And finally **source** is the source of the **search_results obtained.
        5. Your duty is scrutinize or look through thoroughly both contents of **llm response** and **search_result** to find out they are aligned or communicated the same or similar meaning or message.
        6. The end goal is to identify or flag any occurrence of hallucinations in the **llm_response**  by comparing it with **search_result**.
        7. Find out if the response from the **llm_response** is a complete deviation from the **search_result**.
        8. Our goal is to identify or establish facts from **llm_response** and inform the user.
        9. Do not raise an alert for hallucination when the **llm_response** and **search_result** communicate similar or the same meaning/result.
        10. Only raise the alert for hallucination detected when the content of **llm_response** is a complete deviation from **search_result**.
        11. You are to **return a json response**. 
        12. Your response should look like this:
                {
                    "response": "<response>",
                    "llm_response": "<The parts of the **llm_response** that are hallucinations>",
                    "search_result": "<The parts of the **search_result** that triggered the alert for hallucination detection>"
                    "source": "<The **source** or **url** of the **search_result**>"
                } 
        13. Use the json template for all of your responses.
        14. Replace the value of the response key with **Hallucination detected** when there is hallucination is the **llm_response**.
        15. And the value of the response key should be **No hallucination detected** when there is no hallucination or both **llm_response** and **search_result** are similar or communicate the same meaning.
        16. The value for the key **llm_response** should be replaced with the parts of the **llm_response** that are hallucinations.
        17. The value for the key **search_result** should be replaced with the parts of the **search_result** that triggered the hallucination detection if any occurred.
        18. Finally, the value for the key **source** should be replaced with the source({source} as a string).
        19. Do not flag any **llm_response** content that is not a hallucination as Hallucination Detected.
        20. Remember to use the template i have provided and only return a json response since your response will be consumed via an API.
        """,
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(
        f"The **llm_response** is {llm_response},the **search_result** is {search_result}, and the **source** is {source}",
        stream=True,
    )
    for chunk in response:
        yield chunk.text

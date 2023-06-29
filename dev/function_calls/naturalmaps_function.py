""" Run Overpass queries directly from chat GPT 3

The code follows the methodology described here https://platform.openai.com/docs/guides/gpt/function-calling, where
functions can be defined and fed to GPT3, which is finetuned to understand and run them.

It is quite buggy and will eventually be deleted. 
Returns:
    _type_: _description_
"""

import openai
import os
import json
import pandas as pd
import requests
from time import gmtime, strftime


def overpass_query(prompt, query):
    """Run an overpass query
    To improve chances of success, run this multiple times for simpler queries.
    eg. prompt: "Find bike parking near tech parks in Kreuzberg, Berlin"
    in this example, a complex query is likely to fail, so it is better to run
    a first query for bike parking in Kreuzberk and a second one for tech parks in Kreuzberg
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    response = requests.get(overpass_url, params={"data": query})
    if response.content:
        try:
            data = response.json()
        except:
            data = {"error": str(response)}
    else:
        print("Empty response from Overpass API")
        data = {
            "warning": "received an empty response from Overpass API. Tell the user."
        }
    print(data)
    data_str = json.dumps(data)

    # Write Overpass API Call to JSON
    timestamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    save_to_json(
        file_path="overpass_query_log.json",
        timestamp=timestamp,
        prompt=prompt,
        this_run_log={"query": query, "response": data_str},
    )
    return data_str


# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)


def run_conversation(messages: list):
    # Step 1: send the conversation and available functions to GPT
    functions = [
        {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
        {
            "name": "overpass_query",
            "description": """Run an overpass query
            To improve chances of success, run this multiple times for simpler queries.
            eg. prompt: "Find bike parking near tech parks in Kreuzberg, Berlin"
            in this example, a complex query is likely to fail, so it is better to run
            a first query for bike parking in Kreuzberk and a second one for tech parks in Kreuzberg""",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Serves no other purpose than logging",
                    },
                    "query": {
                        "type": "string",
                        "description": "The overpass QL query to execute",
                    },
                },
                "required": ["prompt", "query"],
            },
        },
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call="auto",  # auto is default, but we'll be explicit
        n=3,  # Adding n=3 to try and generate three responses
    )

    response_message = response["choices"][0]["message"]

    for choice in response["choices"]:
        response_message = choice["message"]
        # Step 2: check if GPT wanted to call a function
        if response_message.get("function_call"):
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                "get_current_weather": get_current_weather,
                "overpass_query": overpass_query,
            }  # only one function in this example, but you can have multiple

            function_name = response_message["function_call"]["name"]
            function_to_call = available_functions[function_name]
            print(f"Calling {function_name}")

            # Attempt to load JSON
            try:
                function_args = json.loads(
                    response_message["function_call"]["arguments"]
                )
                json_failed = False
            except json.JSONDecodeError as e:
                json_failed = True
                function_response = {
                    "invalid args": str(e),
                    "input": response_message["function_call"]["arguments"],
                }

            if not json_failed:
                if function_name == "overpass_query":
                    function_response = function_to_call(
                        prompt=function_args.get("prompt"),
                        query=function_args.get("query"),
                    )

                    data = json.loads(function_response)
                    if "elements" in data:
                        elements = data["elements"]
                    else:
                        continue
                    if elements == []:
                        continue

                elif (
                    function_name == "get_current_weather"
                ):  # Leftover from example as reference.
                    function_response = function_to_call(
                        location=function_args.get("location"),
                        unit=function_args.get("unit"),
                    )

            # Check which of the Overpass queries returned any data

            # Step 4: send the info on the function call and function response to GPT
            messages.append(
                response_message
            )  # extend conversation with assistant's reply
            messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response

        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
        )  # get a new response from GPT where it can see the function response
    else:
        function_response = None
        second_response = None

    timestamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    save_to_json(
        file_path="response_log.json",
        timestamp=timestamp,
        prompt=messages[0]["content"],
        this_run_log={
            "first response": response_message,
            "function response": function_response,
            "second response": second_response,
        },
    )
    return response_message


def run_prompt(prompt: str):
    # Get api_key (saved locally)
    api_key = os.getenv("OPENAI_KEY")
    openai.api_key = api_key
    assert openai.api_key, "Failed to find API keys"

    messages = [{"role": "user", "content": prompt}]
    response_object = run_conversation(messages)
    try:
        response_content = response_object.choices[0].message["content"]
        response_cost = round(response_object.usage["total_tokens"] * 0.0000015, 5)
        print(response_content)
        print(f"Cost: ${response_cost}-{2*response_cost}")
    except:
        response_content = response_object
        print(response_content)


if __name__ == "__main__":
    run_prompt("What are the coordinates and address of Rathaus Schöneberg?")

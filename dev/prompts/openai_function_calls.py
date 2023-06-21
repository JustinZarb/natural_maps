""" Run Overpass queries directly from chat GPT 3

The code follows the methodology described here https://platform.openai.com/docs/guides/gpt/function-calling, where
functions can be defined and fed to GPT3, which is finetuned to understand and run them.

Returns:
    _type_: _description_
"""

import openai
import os
import json
import pandas as pd
import requests
from time import gmtime, strftime


def overpass_query(query):
    """Run an overpass query"""
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

    data_str = json.dumps(data)

    save_to_json(
        file_path="overpass_query_log.json", this_run_name=query, this_run_log=data_str
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


def save_to_json(file_path: str, timestamp: str, prompt: str, this_run_log: dict):
    json_file_path = file_path
    # Check if the file exists
    if os.path.isfile(json_file_path):
        # If it exists, open it and load the JSON data
        with open(json_file_path, "r") as f:
            data = json.load(f)
    else:
        # If it doesn't exist, create an empty dictionary
        data = {}

    # Add data for this run
    this_run_name = f"{timestamp} | {prompt}"
    data[this_run_name] = {
        # "timestamp": timestamp,
        # "prompt": prompt,
        "log": this_run_log,
    }

    with open(json_file_path, "w") as f:
        json.dump(data, f, indent=4)


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
            "description": "runs a query through the overpass API",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The overpass QL query to execute",
                    },
                },
                "required": ["query"],
            },
        },
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call="auto",  # auto is default, but we'll be explicit
    )

    response_message = response["choices"][0]["message"]

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
        try:
            function_args = json.loads(response_message["function_call"]["arguments"])
            print(f"Calling {function_name}")

            if function_name == "overpass_query":
                function_response = function_to_call(query=function_args.get("query"))
                assert function_response, f"{function_name} failed to get a response."

            elif function_name == "get_current_weather":
                function_response = function_to_call(
                    location=function_args.get("location"),
                    unit=function_args.get("unit"),
                )

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

        except:
            # Throw an exception if the arguments do not conform to the expected format and skip the second API call
            second_response = {"error": f"invalid arguments for {function_name}"}

    # Log results
    timestamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    try:
        save_to_json(
            file_path="response_log.json",
            timestamp=timestamp,
            prompt=messages[0]["content"],
            this_run_log={
                "first response": response_message,
                "function response": function_response[:2000],
                "second response": second_response,
            },
        )
        return second_response
    except:
        save_to_json(
            file_path="response_log.json",
            timestamp=timestamp,
            prompt=messages[0]["content"],
            this_run_log={"first response": response_message, "second response": None},
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
    run_prompt("What is the address of Curry 36 in Berlin?")

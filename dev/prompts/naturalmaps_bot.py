import openai
import os
import json
import pandas as pd
import requests
from time import gmtime, strftime


class ChatBot:
    def __init__(self):
        self.get_openai_key_from_env()
        assert openai.api_key, "Failed to find API keys"

        self.messages = []
        self.functions = {
            "get_current_weather": self.get_current_weather,
            "overpass_query": self.overpass_query,
        }
        self.function_metadata = [
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

    def get_openai_key_from_env(self):
        # Get api_key (saved locally)
        api_key = os.getenv("OPENAI_KEY")
        openai.api_key = api_key

    def overpass_query(self, prompt, query):
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
        data_str = json.dumps(data)

        # Write Overpass API Call to JSON
        timestamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        self.save_to_json(
            file_path="~/naturalmaps_logs/overpass_query_log.json",
            timestamp=timestamp,
            prompt=prompt,
            this_run_log={"query": query, "response": data_str},
        )

        return data_str

    def get_current_weather(self, location, unit="fahrenheit"):
        """Get the current weather in a given location"""
        weather_info = {
            "location": location,
            "temperature": "72",
            "unit": unit,
            "forecast": ["sunny", "windy"],
        }
        return json.dumps(weather_info)

    def save_to_json(
        self, file_path: str, timestamp: str, prompt: str, this_run_log: dict
    ):
        json_file_path = file_path

        # Check if the folder exists and if not, create it.
        folder_path = os.path.dirname(json_file_path)
        folder_path = os.path.expanduser(folder_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

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
            "log": this_run_log,
        }

        with open(json_file_path, "w") as f:
            json.dump(data, f, indent=4)

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_function_message(self, function_name, content):
        self.messages.append(
            {"role": "function", "name": function_name, "content": content}
        )

    def process_messages(self, n=1):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=self.messages,
            functions=self.function_metadata,
            function_call="auto",
            n=n,
        )

        if n == 1:
            response_messages = [response["choices"][0]["message"]]

        else:
            response_messages = [choice["message"] for choice in response["choices"]]
        self.messages += response_messages
        return response_messages

    def execute_function(self, response_message):
        function_name = response_message["function_call"]["name"]
        function_args = response_message["function_call"]["arguments"]
        print(function_args)

        if function_name in self.functions:
            function_to_call = self.functions[function_name]
            try:
                function_args_dict = json.loads(function_args)
                print(function_args)
                json_failed = False
            except json.JSONDecodeError as e:
                json_failed = True
                function_response = {
                    "invalid args": str(e),
                    "input": function_args,
                }

            if not json_failed:
                if function_name == "overpass_query":
                    function_response = function_to_call(**function_args_dict)
                    data = json.loads(function_response)
                    if "elements" in data:
                        elements = data["elements"]
                        if elements == []:
                            function_response = "no result found"
                    else:
                        function_response = "no result found"

            self.add_function_message(function_name, function_response)
        else:
            print("Function not found:", function_name)

    def run_conversation(self):
        # Increase the n to 3 if this is the first user message, to increase chances of a working query
        print([message for message in self.messages if message["role"] == "user"])
        num_user_messages = sum(
            1 for message in self.messages if message["role"] == "user"
        )

        n = 3 if num_user_messages == 1 else 1
        print("n=", n)
        response_messages = self.process_messages(n)

        for response_message in response_messages:
            if response_message.get("function_call"):
                self.execute_function(response_message)

        response_message = self.process_messages()

        return response_message


chatbot = ChatBot()
chatbot.add_user_message("are there any public toilets in Monbijoupark?")
print(chatbot.run_conversation())
# chatbot.add_user_message("are there any ping pong tables in Monbijoupark? which one is closest to a toilet?")
# print(chatbot.run_conversation())

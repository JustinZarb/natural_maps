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
        self.overpass_queries = {}
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
                            "description": "The user message. Used for logging. Do not paraphrase.",
                        },
                        "query": {
                            "type": "string",
                            "description": "The overpass QL query to execute. Important: Ensure that this is a properly formatted .json string.",
                        },
                    },
                    "required": ["prompt", "query"],
                },
            },
        ]
        # Create a chatbot id using creation timestamp and first question
        self.id = self.get_timestamp()

    def save_to_json(self, file_path: str, timestamp: str, prompt: str, log: dict):
        json_file_path = file_path

        # Check if the folder exists and if not, create it.
        folder_path = os.path.dirname(json_file_path)
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
            "log": log,
        }

        with open(json_file_path, "w") as f:
            json.dump(data, f, indent=4)

    def get_timestamp(self):
        return strftime("%Y-%m-%d %H:%M:%S", gmtime())

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
        timestamp = self.get_timestamp()
        filepath = os.path.expanduser("~/naturalmaps_logs/overpass_query_log.json")
        success = True if "error" not in data_str else False
        returned_something = len(data["elements"]) > 0
        self.overpass_queries[query] = {
            "prompt": prompt,
            "success": success,
            "returned something": returned_something,
            "data": data_str,
        }
        self.save_to_json(
            file_path=filepath,
            timestamp=timestamp,
            prompt=prompt,
            log={
                "query": query,
                "response": data_str,
                "query_success": success,
                "returned_something": returned_something,
            },
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

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_function_message(self, function_name, content):
        self.messages.append(
            {"role": "function", "name": function_name, "content": content}
        )

    def is_valid_message(self, message):
        # Check if the message content is a valid string. Add other conditions if necessary.
        if message.get("function_call"):
            if message["function_call"].get("arguments"):
                function_args = message["function_call"]["arguments"]
                if isinstance(function_args, str):
                    try:
                        json.loads(function_args)  # Attempt to parse the JSON string
                        return True  # Return True if it's a valid JSON string
                    except json.JSONDecodeError:
                        return False  # Return False if it's not a valid JSON string
            return False
        else:
            return True

    def process_messages(self, n=1):
        """A general purpose function to prepare an answer based on all the previous messages

        Issues: currently modifying the original prompt

        Args:
            n (int, optional): Changes the number of responses from GPT.
            Increasing this raises the chances tha one answer will generate
            a valid api call from Overpass, but will also increase the cost.
            Defaults to 1. Set to 3 if the message is the first one, in the future
            this could be changed to run whenever the overpass_query function
            is called.

        Returns:
            _type_: _description_
        """

        # Fine tuning docs here: https://platform.openai.com/docs/api-reference/chat/create
        # This breaks if the messages are not valid
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=self.messages,
            functions=self.function_metadata,
            function_call="auto",
            n=n,
            temperature=0.7,  # recommended to NOT use both temperature and top_p
            # top_p=0.5,
        )

        if n == 1:
            response_messages = [response["choices"][0]["message"]]
        else:
            # create a list with n response messages
            response_messages = [choice["message"] for choice in response["choices"]]

        # Filter out invalid messages based on your condition
        valid_response_messages = [
            msg for msg in response_messages if self.is_valid_message(msg)
        ]
        invalid_response_messages = [
            "invalid args"
            for msg in response_messages
            if not self.is_valid_message(msg)
        ]

        self.messages += valid_response_messages
        return valid_response_messages, invalid_response_messages

    def execute_function(self, response_message):
        function_name = response_message["function_call"]["name"]
        function_args = response_message["function_call"]["arguments"]

        if function_name in self.functions:
            function_to_call = self.functions[function_name]
            try:
                function_args_dict = json.loads(function_args)
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
        print(
            "newest question:",
            [m["content"] for m in self.messages if m["role"] == "user"][-1],
        )

        # Increase the n to 3 if this is the first user message, to increase chances of a working query
        num_user_messages = sum(
            1 for message in self.messages if message["role"] == "user"
        )
        if num_user_messages == 1:
            n = 3
            # the chat id is {timestamp}_{first question}
            self.id = self.id + "_" + self.messages[0]["content"]
        else:
            n = 1
        save_path = os.path.expanduser(f"~/naturalmaps_logs/{self.id}.json")

        # Process first message
        response_messages, invalid_ = self.process_messages(n)
        # save response of first message
        timestamp = self.get_timestamp()
        self.save_to_json(
            file_path=save_path,
            timestamp=timestamp,
            prompt=None,
            log={"valid_messages": self.messages, "invalid_messages": invalid_},
        )

        # Check if response includes a function call, and if yes, run it.
        for response_message in response_messages:
            if response_message.get("function_call"):
                self.execute_function(response_message)

        response_message, invalid_ = self.process_messages()

        # Save the processed response
        timestamp = self.get_timestamp()
        self.save_to_json(
            file_path=save_path,
            timestamp=timestamp,
            prompt=None,
            log={
                "valid_messages": self.messages,
                "invalid_messages": invalid_,
                "overpass_queries": self.overpass_queries,
            },
        )
        return response_message


# Testing Chatbot messages here
chatbot = ChatBot()
# chatbot.add_user_message("are there any public toilets in Monbijoupark?")

# chatbot.add_user_message("show me the ping pong tables and toilets in Monbijoupark?")

chatbot.add_user_message("show me the ping pong tables in Gleisdreieck Park?")

print(chatbot.run_conversation())

# chatbot.add_user_message(
#     "are there any ping pong tables in Monbijoupark? which one is closest to a toilet?"
# )
# print(chatbot.run_conversation())

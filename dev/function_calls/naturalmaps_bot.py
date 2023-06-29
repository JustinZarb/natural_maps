import openai
import os
import json
import pandas as pd
import requests
from time import gmtime, strftime
import osmnx as ox


class ChatBot:
    def __init__(self):
        self.get_openai_key_from_env()
        assert openai.api_key, "Failed to find API keys"

        self.messages = []
        self.add_system_message(
            content="""Let's first understand the problem and devise a plan to solve the problem."
            " Please output the plan starting with the header 'Plan:' "
            "and then followed by a numbered list of steps. "
            "Please make the plan the minimum number of steps required "
            "to accurately complete the task. If the task is a question, "
            "the final step should almost always be 'Given the above steps taken, "
            "please respond to the users original question'. "
            "At the end of your plan, say '<END_OF_PLAN>'"""
        )

        self.overpass_queries = {}
        self.functions = {
            "" "overpass_query": self.overpass_query,
        }
        self.function_status_pass = False  # Used to indicate function success
        self.function_metadata = [
            {
                "name": "overpass_query",
                "description": """Run an overpass query
                    To improve chances of success, keep the queries simple.
                    You might have an idea where places are, but you sometimes guess wrong, so always use geocodeArea, which gives a more accurate location.
                    
                    eg. prompt: "Find toilets in Charlottenburg"
                    
                    [out:json][timeout:25];
                    /{/{geocodeArea:charlottenburg}}->.searchArea;
                    (
                    node["amenity"="toilets"](area.searchArea);
                    way["amenity"="toilets"](area.searchArea);
                    relation["amenity"="toilets"](area.searchArea);
                    );
                    out body;
                    >;
                    out skel qt;
                    """,
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

    def name_to_gdf(self, place_name):
        # Use OSMnx to geocode the location
        return ox.geocode_to_gdf(place_name)

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
        else:  # ToDo: check this.. it might not make sense
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

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_function_message(self, function_name, content):
        self.messages.append(
            {"role": "function", "name": function_name, "content": content}
        )

    def add_system_message(self, content):
        self.messages.append({"role": "system", "content": content})

    def execute_function(self, response_message):
        """Execute a function from self.functions

        Args:
            response_message (_type_): The message from the language model with the required inputs
            to run the function
        """
        # Return false if we decide that the function failed
        self.function_status_pass = False

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
                # Specific checks for self.overpass_query()
                if function_name == "overpass_query":
                    function_response = function_to_call(**function_args_dict)
                    data = json.loads(function_response)
                    if "elements" in data:
                        elements = data["elements"]
                        if elements == []:
                            function_response = "Overpass query returned no results"
                        else:
                            # Overpass query worked! Passed!
                            self.function_status_pass = True
                    else:
                        function_response = (
                            "Overpass Query does not contain any elements"
                        )

            self.add_function_message(function_name, function_response)
        else:
            print("Function not found:", function_name)

    def is_valid_message(self, message):
        """Check if the message content is a valid JSON string"""
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

        # This breaks if the messages are not valid
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=self.messages,
            functions=self.function_metadata,
            function_call="auto",
            n=n,
        )
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

        return valid_response_messages, invalid_response_messages

    def run_conversation(self):
        """Run this after every user message
        originally had the following structure:
        - create overpass query from user message
        - do a function call and return the query result
        - interpret the query result for the user.

        To reduce failures due to hallucinated query formats, three queries are generated in
        response to the first message and are run sequentially until one of them works.

        As user messages get more complex, this may need to be broken down into smaller steps.
        In its current form, the calls are built into a loop which feed each response from the
        large language model back into the conversation history, so that the next response has
        all the previous responses as context.
        """
        print(
            "newest question:",
            [m["content"] for m in self.messages if m["role"] == "user"][-1],
        )

        # Increase n to 3 if this is the first user message, to increase chances of a working query
        user_messages = [m for m in self.messages if m["role"] == "user"]
        num_user_messages = len(user_messages)
        if num_user_messages == 1:
            n = 1  # increase the number of initial responses to increase chances of success
            # the chat id is {timestamp}_{first question}
            self.id = self.id + "_" + user_messages[0]["content"]
        else:
            n = 1
        save_path = os.path.expanduser(f"./naturalmaps_logs/{self.id}.json")

        """
        ### UNDER CONSTRUCTION ###
        Change the code below to enable the language model
        to act as an agent and repeat actions until the goal is achieved
        """
        counter = 0
        while counter < 5:
            # Process messages
            response_messages, invalid_messages = self.process_messages(n)
            self.messages += response_messages

            # Check if response includes a function call, and if yes, run it.
            for response_message in response_messages:
                if response_message.get("function_call"):
                    if self.function_status_pass:
                        continue  # skips running the next API calls
                    self.execute_function(response_message)

            response_message, invalid_messages = self.process_messages()

            # Save the processed response
            print(response_message, invalid_messages)
            timestamp = self.get_timestamp()
            self.save_to_json(
                file_path=save_path,
                timestamp=timestamp,
                prompt=None,
                log={
                    "valid_messages": self.messages,
                    "invalid_messages": invalid_messages,
                    "overpass_queries": self.overpass_queries,
                },
            )
            counter += 1

            # if self.is_goal_achieved(response_message):
            #    break

        return response_message


chatbot = ChatBot()
chatbot.add_user_message(
    "are there any ping pong tables in Monbijoupark? which one is closest to a toilet?"
)

print(chatbot.run_conversation())

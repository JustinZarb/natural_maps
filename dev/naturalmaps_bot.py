import openai
import os
import json
import requests
from time import localtime, strftime
import osmnx as ox
import streamlit as st
import re
from streamlit_functions import (
    gdf_data,
    get_nodes_with_tags_in_bbox,
    count_tag_frequency,
    longest_distance_to_vertex,
)


class ChatBot:
    def __init__(self, log_path: str = None, openai_api_key=None):
        # Get OpenAI Key
        openai.api_key = openai_api_key
        assert openai.api_key, "Failed to find API keys"

        # Initialize Messages
        self.messages = []

        # Invalid messages cannot be added to the chat but should be saved For logging
        self.invalid_messages = []

        # Initialize Functions
        self.functions = {
            "overpass_query": self.overpass_query,
            # "get_place_info": self.get_place_info,
        }
        self.function_status_pass = False  # Used to indicate function success
        self.function_metadata = [
            {
                "name": "overpass_query",
                "description": """Run an overpass QL query.
                    Instructions:
                    - Keep the queries simple and specific.
                    - Always use Overpass built-in geocodeArea for locations like this {{geocodeArea:charlottenburg}}->.searchArea; 
                    - If running broad searches such as [node[~'^(amenity|leisure)$'~'.']({{bbox}});], stick to only nodes. 
                    - remember to use square brackets around nodes.
                    eg. "Find toilets in Charlottenburg"
                    [out:json][timeout:25];
                    {{geocodeArea:charlottenburg}}->.searchArea;
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
                        "human_prompt": {
                            "type": "string",
                            "description": "The user message. Used for logging. Do not paraphrase.",
                        },
                        "generated_query": {
                            "type": "string",
                            "description": "The overpass QL query to execute. Important: Ensure that this is a properly formatted .json string.",
                        },
                    },
                    "required": ["prompt", "query"],
                },
            },
        ]
        self.spare_function_metadata = [
            {
                "name": "get_place_info",
                "description": """Gets area and tag keys of a place using osmnx.geocode_to_gdf. Requires correctly spelt real places as input.
                Do not tell the user the area of the place unles it is relevant to the question. Use the tag keys as hints for better Overpass Queries.
                Args:
                    places (str(list)): A list of place names.
                Returns:
                    data (str): A JSON string containing a dictionary with projected_area, area_unit and keys. 
                    - projected_area: a dict of display_name:area for each of the locations in places_str
                    - area_units: a dict of display_name:area_units for each of the locations in places_str
                    - keys: a list of unique tag keys (includes all locations fed to the function). Sorted by frequency.
                 
                Convert from m² to km² when returning information about large areas.          
                    """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "places_str": {
                            "type": "string",
                            "description": "a place name or a comma-seperated list of place names",
                        },
                    },
                    "required": ["places_str"],
                },
            },
        ]

        # Store overpass queries in the class
        self.overpass_queries = {}
        # Store gdf files in the class
        self.gdf = {}
        # Store transformed gdf files

        # Logging parameters
        self.id = self.get_timestamp()
        if log_path is None:
            log_path = "~/naturalmaps_logs"
            self.log_path = os.path.expanduser(log_path)

    def get_place_info(self, places_str: str):
        """Get GDF and area from a place name.
        Can be called by the LLM
        Args:
            places (str(list)): A list of place names.
        Returns:
            data (str): A JSON string containing a dictionary with projected_area, area_unit and keys.
            projected_area: a dict of {display_name:area} for each of the locations in places_str
            area_units: a dict of {display_name:area_units} for each of the locations in places_str
            keys: a list of unique tag keys (includes all locations fed to the function). Sorted by frequency.
        """
        # Use OSMnx to geocode the location
        places = places_str.replace("[", "").replace("]", "").split(",")
        try:
            new_gdf = ox.geocode_to_gdf(places)  # geodataframe
            if not hasattr(self, "places_gdf"):
                self.places_gdf = new_gdf
            else:
                # add rows to self.places_gdf
                self.places_gdf = pd.concat(
                    [self.places_gdf, new_gdf], ignore_index=True
                )
        except ValueError as e:
            return e

        # Get a list of unique keys in all the areas provided, sorted by frequency.
        keys = []
        nodes = []
        bounding_boxes = self.places_gdf.loc[
            :,
            [
                "bbox_south",
                "bbox_west",
                "bbox_north",
                "bbox_east",
            ],
        ]
        for _, row in bounding_boxes.iterrows():
            nodes.append(get_nodes_with_tags_in_bbox(list(row)))
            keys = list(count_tag_frequency(nodes).keys())

        # add projected area to the gdf
        self.places_gdf[["projected_area", "area_unit"]] = self.places_gdf.apply(
            lambda row: gdf_data(row, self.places_gdf.crs), axis=1
        )

        # Add a column for each geometry with the longest distance from the centroid to the boundary
        self.places_gdf["longest_distance_to_vertex"] = self.places_gdf[
            "geometry"
        ].apply(longest_distance_to_vertex)

        # Return something useful to the LLM
        place_dict = {
            "area": dict(
                zip(self.places_gdf["display_name"], self.places_gdf["projected_area"])
            ),
            "area_unit": dict(
                zip(self.places_gdf["display_name"], self.places_gdf["area_unit"])
            ),
            "tag_keys": keys,
        }

        data = json.dumps(place_dict)
        return data

    def distance_calc(self, gdf, lat, lon):
        """Not yet properly implemented

        Args:
            gdf (_type_): _description_
            lat (_type_): _description_
            lon (_type_): _description_

        Returns:
            _type_: _description_
        """
        # Calculate the distance between two points
        gdf["distance"] = gdf.apply(
            lambda row: ox.distance.great_circle_vec(
                lat, lon, row["geometry"].y, row["geometry"].x
            ),
            axis=1,
        )
        return gdf

    def save_to_json(self, file_path: str, this_run_name: str, log: dict):
        json_file_path = (
            file_path if file_path.endswith(".json") else file_path + ".json"
        )
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
        data[this_run_name] = {
            "log": log,
        }

        with open(json_file_path, "w") as f:
            json.dump(data, f, indent=4)

    def get_timestamp(self):
        return strftime("%Y-%m-%d %H:%M:%S", localtime())

    def log_overpass_query(
        self, human_prompt, generated_query, cleaned_query, data_str
    ):
        # Write Overpass API Call to JSON
        timestamp = self.get_timestamp()
        this_run_name = f"{timestamp} | {human_prompt}"
        filepath = os.path.join(self.log_path, "overpass_query_log.json")
        success = True if "error" not in data_str else False
        data_dict = json.loads(data_str)
        returned_something = (
            True
            if ("elements" in data_dict and len(data_dict["elements"])) > 0
            else False
        )

        # This gets saved in the chat log
        self.overpass_queries[human_prompt] = {
            "temperature": self.temperature,
            "generated_oQL_query": generated_query,
            "cleaned_oQL_query": cleaned_query,
            "overpass_response": data_str,
            "valid_query": success,
            "returned_something": returned_something,
        }

        # This gets saved in a separate log for overpass ueries
        self.save_to_json(
            file_path=filepath,
            this_run_name=this_run_name,
            log=self.overpass_queries[human_prompt],
        )

    def overpass_query(self, human_prompt, generated_query):
        """Run an overpass query
        To improve chances of success, run this multiple times for simpler queries.
        eg. prompt: "Find bike parking near tech parks in Kreuzberg, Berlin"
        in this example, a complex query is likely to fail, so it is better to run
        a first query for bike parking in Kreuzberk and a second one for tech parks in Kreuzberg
        """
        overpass_url = "http://overpass-api.de/api/interpreter"

        # Check that the query is properly formatted
        cleaned_query = (
            generated_query.replace("\n", "").replace("_", "").replace("\\", "")
        )
        response = requests.get(overpass_url, params={"data": cleaned_query})
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
        self.log_overpass_query(human_prompt, generated_query, cleaned_query, data_str)
        return data_str

    def add_system_message(self, content):
        self.messages.append({"role": "system", "content": content})

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_function_message(self, function_name, content):
        self.messages.append(
            {"role": "function", "name": function_name, "content": content}
        )

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
                try:
                    function_response = function_to_call(**function_args_dict)
                except TypeError as e:
                    function_response = {
                        "invalid args": str(e),
                        "input": function_args,
                    }

                # Specific checks for self.overpass_query()
                if function_name == "overpass_query":
                    try:
                        data = json.loads(function_response)
                        if len(function_response) > 4096:
                            function_response = (
                                "Overpass query returned too many results."
                            )
                        if "elements" in data:
                            elements = data["elements"]
                            if elements == []:
                                function_response += (
                                    "-> Overpass query returned no results."
                                )
                            else:
                                # Overpass query worked! Passed!
                                self.function_status_pass = True
                    except TypeError as e:
                        function_response = e

        else:
            function_response = f"{function_name} not found"

        self.add_function_message(function_name, function_response)
        self.add_system_message(
            content=f"""Does the function response contain enough information to answer step {self.current_step}? 
            If yes: Return a message describing what you will do in step {self.current_step+1} and if necessarry call the next function.
            If not: Return a message saying the first attempt at step {self.current_step} failed and the best way to overcome this problem.
            If you do not have an adequate function to run the next step or if some steps failed,
            skip to the final step. Provide a response explaining what worked and what didn't, and
            any useful information from partial results. Start each message with '[step {self.current_step}]'.
            End your final message with <final_response>"""
        )

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

    def process_messages(self, n=1, temperature=0.1):
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
            temperature=self.temperature,
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

    def read_plan(self, plan):
        # Remove the "Here's the plan:" and "<END_OF_PLAN>" parts
        plan = plan.replace("Here's the plan:\n", "").strip()

        # Split the string at every number followed by a full stop, but keep the content together
        split_s = re.split(r"(\d+\.\s)", plan)

        # Combine the number and the following text into one string
        split_s = [
            split_s[i] + split_s[i + 1].strip() for i in range(1, len(split_s), 2)
        ]

        return split_s

    def start_planner(self):
        st.session_state["planner_message"] = st.chat_message("planner", avatar="📝")

    def start_assistant(self):
        st.session_state["assistant_message"] = st.chat_message(
            "assistant", avatar="🗺️"
        )

    def run_conversation_streamlit(self, num_iterations=4, temperature=0.1):
        """Same as run_conversation but designed to interactively work with Streamlit.
        Run this after every user message

        """
        # Set some logging variables
        self.latest_question = [
            m["content"] for m in self.messages if m["role"] == "user"
        ][-1]

        filename = f"{self.id} | {self.latest_question}"
        filepath = os.path.join(self.log_path, filename)

        # Set conversation parameters
        self.temperature = temperature
        self.remaining_iterations = num_iterations
        final_response = False

        # Give first instructions.
        self.add_system_message(
            content=f"""Let's first understand the problem and devise 
                break it down into simple steps. Fore example, if asked "Find child-friendly parks in Pankow, Berlin",
                first search for parks in Pankow, then check tag keys and values for child-friendliness. 
                Please output the plan starting with the header 'Here's the plan:' and then followed by a concise 
                numbered list of steps. Each step should correspond to a 
                specific function from the following list: {self.functions.keys()}. 
                You have {self.remaining_iterations} remaining.
                Avoid adding any steps that do not directly involve these functions or include 
                specific content of the function calls. 
                Avoid mentioning specific settings or parameters that will be used in the functions. 
                Remember, the goal is to complete the task using the available functions
                within the available number of iterations. Do not repeat or create a new 
                plan."""
        )

        while (self.remaining_iterations > 0) and (not (final_response)):
            # Process messages
            response_messages, invalid_messages = self.process_messages(n=1)
            self.messages += response_messages
            self.invalid_messages += invalid_messages
            self.plan = []
            self.current_step = 1

            st.session_state["message_history"] = []

            # Check if response includes a function call, and if yes, run it.
            for response_message in response_messages:
                # if the role is "assistant", write the content
                if response_message.get("role") == "assistant":
                    if response_message.get("content"):
                        s = response_message.get("content")
                        # Check for a plan (should only happen in the first response)
                        if s.startswith("Here's the plan:"):
                            # set class attribute
                            self.plan = self.read_plan(s)
                            # add to session state in streamlit
                            st.session_state["plan"] = s
                            if "planner_message" not in st.session_state:
                                self.start_planner()
                            st.session_state.planner_message.write(
                                st.session_state["plan"]
                            )

                        # Check if <End of Response>
                        elif s.endswith("<final_response>"):
                            final_response = True
                            st.session_state["message_history"].append(
                                s.replace("<final_response>", "")
                            )

                        else:
                            st.session_state["message_history"].append(s)

                        # Update current step (for the in-between system prompt)
                        if "step" in s:
                            match = re.search(r"\[step (\d+)\]", s)
                            if match:
                                self.current_step = int(match.group(1))

                    if st.session_state.message_history:
                        if "assistant_message" not in st.session_state:
                            self.start_assistant()
                        if not final_response:
                            for m in st.session_state["message_history"]:
                                st.session_state.assistant_message.write(m)

                if response_message.get("function_call"):
                    self.execute_function(response_message)

            self.remaining_iterations -= 1

        if self.overpass_queries:
            st.session_state["overpass_queries"] = self.overpass_queries

        self.user_feedback = (
            st.session_state.user_feedback
            if "user_feedback" in st.session_state
            else []
        )

        # If everything works, just save once at the end
        self.save_to_json(
            file_path=filepath,
            this_run_name=f"iteration {num_iterations-self.remaining_iterations}/{num_iterations} step {self.current_step}",
            log={
                "temperature": self.temperature,
                "valid_messages": self.messages,
                "invalid_messages": self.invalid_messages,
                "overpass_queries": self.overpass_queries,
                "user_feedback": self.user_feedback,
            },
        )

        return response_message

    def run_conversation_vanilla(self, num_iterations=4, temperature=0.1):
        """Designed to run in the terminal
        Run this after every user message

        """
        # Set some logging variables
        self.latest_question = [
            m["content"] for m in self.messages if m["role"] == "user"
        ][-1]

        filename = f"{self.id} | {self.latest_question}"
        filepath = os.path.join(self.log_path, filename)

        # Set conversation parameters
        self.temperature = temperature
        self.remaining_iterations = num_iterations
        final_response = False

        # Give first instructions.
        self.add_system_message(
            content=f"""Let's first understand the problem and devise 
                break it down into simple steps. Fore example, if asked "Find child-friendly parks in Pankow, Berlin",
                first search for parks in Pankow, then check tag keys and values for child-friendliness. 
                Please output the plan starting with the header 'Here's the plan:' and then followed by a concise 
                numbered list of steps. Each step should correspond to a 
                specific function from the following list: {self.functions.keys()}. 
                You have {self.remaining_iterations} remaining.
                Avoid adding any steps that do not directly involve these functions or include 
                specific content of the function calls. 
                Avoid mentioning specific settings or parameters that will be used in the functions. 
                Remember, the goal is to complete the task using the available functions
                within the available number of iterations. Do not repeat or create a new 
                plan."""
        )

        while (self.remaining_iterations > 0) and (not (final_response)):
            # Process messages
            response_messages, invalid_messages = self.process_messages(n=1)
            self.messages += response_messages
            self.invalid_messages += invalid_messages
            self.plan = []
            self.current_step = 1

            # st.session_state["message_history"] = []
            print(
                f"iteration {num_iterations-self.remaining_iterations}/{num_iterations} step {self.current_step}"
            )
            # Check if response includes a function call, and if yes, run it.
            for response_message in response_messages:
                # if the role is "assistant", write the content
                if response_message.get("role") == "assistant":
                    if response_message.get("content"):
                        s = response_message.get("content")
                        print(s)
                        # Check for a plan (should only happen in the first response)
                        if s.startswith("Here's the plan:"):
                            # set class attribute
                            self.plan = self.read_plan(s)

                        # Check if <End of Response>
                        elif s.endswith("<final_response>"):
                            final_response = True

                        # Update current step (for the in-between system prompt)
                        if "step" in s:
                            match = re.search(r"\[step (\d+)\]", s)
                            if match:
                                self.current_step = int(match.group(1))

                if response_message.get("function_call"):
                    self.execute_function(response_message)

            self.remaining_iterations -= 1

        # If everything works, just save once at the end
        self.save_to_json(
            file_path=filepath,
            this_run_name=f"iteration {num_iterations-self.remaining_iterations}/{num_iterations} step {self.current_step}",
            log={
                "temperature": self.temperature,
                "valid_messages": self.messages,
                "invalid_messages": self.invalid_messages,
                "overpass_queries": self.overpass_queries,
                # "user_feedback": self.user_feedback,
            },
        )


if __name__ == "__main__":
    chatbot = ChatBot(openai_api_key=os.getenv("OPENAI_API_KEY"))
    chatbot.add_user_message("Can I play table tennis around Monbijoupark?")

    print(chatbot.run_conversation_vanilla(temperature=0.9))

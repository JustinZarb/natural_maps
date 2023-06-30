"""Tool for the Overpass API.

Additional information:
- BaseTool defines the interface which LangChain tools must implement https://github.com/hwchase17/langchain/blob/master/langchain/tools/base.py

"""

from typing import Optional, Type

from pydantic import BaseModel, Field

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from langchain.tools.base import BaseTool
from utilities.overpass_query import OverpassQueryWrapper


class OverpassQuerySchema(BaseModel):
    query: str = Field(..., description="Query for Overpass API")


class OverpassQueryTool(BaseTool):
    """Tool that adds the capability to generate a prompt and query the Overpass API."""

    name = "overpass_query"
    description = (
        "A sequential chain for an LLM to generate "
        "an overpass query, run it and return the results. "
        "Useful for when you need to need to search  "
        "for things or places in the real world. "
        "Input should be a search query."
    )
    api_wrapper: OverpassQueryWrapper = Field(default_factory=OverpassQueryWrapper)
    args_schema: Type[BaseModel] = OverpassQuerySchema

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return self.api_wrapper.run(query)

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GooglePlacesRun does not support async")

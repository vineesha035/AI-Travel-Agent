import os
import operator
from typing import Annotated, TypedDict
from agents.utils import extract_text
from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage 
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agents.tools.flights_finder import flights_finder
from agents.tools.hotel_finder import hotels_finder
from agents.tools.itinerary_planner import itinerary_planner

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


TOOLS = [flights_finder, hotels_finder, itinerary_planner]

TOOLS_SYSTEM_PROMPT = """
You are an AI Travel Agent.
You can:
- Use flights_finder to find flights
- Use hotels_finder to find hotels
- Use itinerary_planner to generate a daily itinerary
Always combine tool outputs into a clear, well-organized trip summary for the user.
"""
class Agent:
    def __init__(self):
        self._tools = {t.__name__: t for t in TOOLS}
        self._tools_llm = ChatGoogleGenerativeAI(
            model="gemini-flash-lite-latest",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        ).bind_tools(TOOLS)

        builder = StateGraph(AgentState)
        builder.add_node("call_tools_llm", self.call_tools_llm)
        builder.add_node("invoke_tools", self.invoke_tools)
        builder.set_entry_point("call_tools_llm")

        builder.add_conditional_edges(
            "call_tools_llm",
            Agent.exists_action,
            {"more_tools": "invoke_tools", "done": END},
        )
        builder.add_edge("invoke_tools", "call_tools_llm")

        memory = MemorySaver()
        self.graph = builder.compile(checkpointer=memory)

    @staticmethod
    def exists_action(state: AgentState):
        result = state["messages"][-1]
        if len(result.tool_calls) == 0:
            return "done"
        return "more_tools"

    def call_tools_llm(self, state: AgentState):
        messages = [SystemMessage(content=TOOLS_SYSTEM_PROMPT)] + state["messages"]
        message = self._tools_llm.invoke(messages)
        return {"messages": [message]}

    def invoke_tools(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []
        for t in tool_calls:
            if t["name"] not in self._tools:
                result = "bad tool name, retry"
            else:
                result = self._tools[t["name"]](**t["args"])
            results.append(ToolMessage(tool_call_id=t["id"], name=t["name"], content=str(result)))
        return {"messages": results}
if __name__ == "__main__":
    print("Starting agent run...")
    agent = Agent()
    config = {"configurable": {"thread_id": "test-thread-1"}}
    user_query = (
        "I want to travel to Paris from JFK from 2026-09-01 to 2026-09-08. "
        "I'm interested in museums, fine dining, and nightlife."
    )
    result = agent.graph.invoke({"messages": [HumanMessage(content=user_query)]}, config=config)
    print("Got result, final message:")
    print(extract_text(result["messages"][-1].content))
import os 
from typing import TypedDict , Annotated
import operator

from langgraph.graph import START , END , StateGraph
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import (AnyMessage , HumanMessage , AIMessage , SystemMessage)

from tools.flight_tool import search_flight
from tools.tavily_tool import tavily_search

from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model = "gemini-3.5-flash-lite", 
    temperature = 0.7
)

class TravelState(TypedDict):
    message : Annotated[list[AnyMessage],operator.add]
    user_query : str
    flight_results : str 
    hotel_results : str
    itinerary: str
    llm_calls : str
    
def flight_agent(state : TravelState)->dict:
    query = state["user_query"]
    flight_data = search_flight(query=query)
    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content=f"Flight results fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
    

def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# Itinerary Agent
def itinerary_agent(state: TravelState):

    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}
    """

    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner"
        ),
        HumanMessage(content=prompt)
    ])
    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
    

def final_agent(state: TravelState):

    final_prompt = f"""
    Generate final travel response.

    Flights:
    {state['flight_results']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}
    """

    response = llm.invoke([
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
    
graph = StateGraph(TravelState)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)

conn = sqlite3.connect(
    "travel_agent.db",
    check_same_thread=False
)

checkpointer = SqliteSaver(conn)

app= graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": "user_surya"
        }
    }
    
    user_input = input("Enter travel request: ")
    
    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )
    
    print("\nFINAL RESPONSE:\n")

    for msg in result["messages"]:
        print(msg.content)
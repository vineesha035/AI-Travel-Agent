import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.utils import extract_text
load_dotenv()

ITINERARY_SYSTEM_PROMPT = """
You are a travel itinerary planner.
Given flight options, hotel options, user interests, and trip dates,
create a detailed daily itinerary.
Include morning, afternoon, and evening activities.
Ensure activities align with user interests (museums, nightlife, food, history, etc.).
Return the output in clean markdown format.
"""
def extract_text(content):
    """
    Some Gemini model versions return response.content as a plain string,
    others (like 3.x) return a list of content blocks. Normalize both cases
    to a single clean string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)

def itinerary_planner(destination: str, dates: list, interests: str, flights: dict, hotels: dict):
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-lite-latest",
        temperature=0.4,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    messages = [
        SystemMessage(content=ITINERARY_SYSTEM_PROMPT),
        HumanMessage(content=f"""
Destination: {destination}
Dates: {dates}
User interests: {interests}

Flights: {flights}
Hotels: {hotels}
"""),
    ]

    response = llm.invoke(messages)
    return {"itinerary": extract_text(response.content)}


if __name__ == "__main__":
    result = itinerary_planner(
        destination="Paris",
        dates=["2026-09-01", "2026-09-08"],
        interests="museums, fine dining, nightlife",
        flights={"summary": "Round trip JFK-LHR, $790, Aer Lingus"},
        hotels={"summary": "Hotel Trianon Rive Gauche, $2915/night"},
    )
    print(result["itinerary"])
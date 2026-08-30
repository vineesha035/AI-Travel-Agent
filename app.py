import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agents.agent import Agent
from agents.utils import extract_text

load_dotenv()


def initialize_agent():
    if "agent" not in st.session_state:
        st.session_state.agent = Agent()
def render_ui():
    st.title("✈️ AI Travel Agent")
    st.write("Enter your travel query with preferences:")
    user_input = st.text_area(
        "Travel Query",
        height=150,
        placeholder='E.g., "I want to travel to Paris from NYC from 2026-09-01 to 2026-09-08. '
                    'Interests: museums, fine dining, nightlife."',
    )
    return user_input


def process_query(user_input):
    if not user_input:
        st.error("Please enter a travel query.")
        return

    thread_id = str(uuid.uuid4())
    st.session_state.thread_id = thread_id
    config = {"configurable": {"thread_id": thread_id}}

    with st.spinner("Planning your trip..."):
        result = st.session_state.agent.graph.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

    final_text = extract_text(result["messages"][-1].content)
    st.session_state.travel_info = final_text

    st.subheader("Your Travel Plan")
    st.markdown(final_text)


def main():
    initialize_agent()
    user_input = render_ui()

    if st.button("Get Travel Information"):
        process_query(user_input)


if __name__ == "__main__":
    main()
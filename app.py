import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agents.agent import Agent
from agents.utils import extract_text
from langgraph.types import Command

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

    if "__interrupt__" in result:
        st.session_state.pending_itinerary = result["__interrupt__"][0].value["itinerary"]
        st.session_state.awaiting_email_decision = True
    else:
        st.session_state.pending_itinerary = extract_text(result["messages"][-1].content)
        st.session_state.awaiting_email_decision = False
def render_email_decision():
    st.subheader("Your Travel Plan")
    st.markdown(st.session_state.pending_itinerary)

    if not st.session_state.get("awaiting_email_decision"):
        return

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    send_email_option = st.radio("Do you want to send this itinerary via email?", ("No", "Yes"))

    if send_email_option == "No":
        if st.button("Confirm"):
            st.session_state.agent.graph.invoke(Command(resume={"send_email": False}), config=config)
            st.session_state.awaiting_email_decision = False
            st.rerun()
    else:
        with st.form(key="email_form"):
            sender_email = st.text_input("Sender Email")
            receiver_email = st.text_input("Receiver Email")
            subject = st.text_input("Email Subject", "Your Travel Itinerary")
            submitted = st.form_submit_button("Send Email")

        if submitted:
            if sender_email and receiver_email and subject:
                resume_value = {
                    "send_email": True,
                    "sender_email": sender_email,
                    "receiver_email": receiver_email,
                    "subject": subject,
                }
                with st.spinner("Sending email..."):
                    final_result = st.session_state.agent.graph.invoke(Command(resume=resume_value), config=config)
                    message = extract_text(final_result["messages"][-1].content)
                if "sent successfully" in message.lower():
                    st.success(message)
                else:
                    st.error(message)
                st.session_state.awaiting_email_decision = False
            else:
                st.error("Please fill out all email fields.")


def main():
    initialize_agent()
    user_input = render_ui()

    if st.button("Get Travel Information"):
        process_query(user_input)

    if "pending_itinerary" in st.session_state:
        render_email_decision()


if __name__ == "__main__":
    main()
import os

from dotenv import load_dotenv
import streamlit as st
import openai
from typing_extensions import override
from openai import AssistantEventHandler

st.title("OpenAI Assistants API UI")


load_dotenv()

user_input = os.environ.get("USER_INPUT", "True")

if user_input == "False":
    api_key = os.environ.get("API_KEY")
    instructions = os.environ.get("INSTRUCTIONS", "")
    assistant_id = os.environ.get("ASSISTANT_ID")


client = openai.OpenAI(api_key=api_key)


# List all assistants from your account
all_assistants = client.beta.assistants.list(
    order="desc",
    limit="20",
)
assistants_list = {}
for assistant in all_assistants.data:
    assistants_list[assistant.name] = assistant.id

# Select an assistant
selected_assistant = st.selectbox("Select Assistant", list(assistants_list.keys()))
selected_assistant_id = assistants_list[selected_assistant]


# Create a thread
thread = client.beta.threads.create()


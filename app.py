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
assistants_list = {None: None}
for assistant in all_assistants.data:
    assistants_list[assistant.name] = assistant.id

# Select an assistant
selected_assistant = st.selectbox("Select Assistant", list(assistants_list.keys()), index=0)
selected_assistant_id = assistants_list.get(selected_assistant)



class EventHandler(AssistantEventHandler):    
  @override
  def on_text_created(self, text) -> None:
    print(f"\nassistant > ", end="", flush=True)
      
  @override
  def on_text_delta(self, delta, snapshot):
    print(delta.value, end="", flush=True)
      
  def on_tool_call_created(self, tool_call):
    print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_tool_call_delta(self, delta, snapshot):
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)
 

# Confirm selection
if st.button("Confirm Selection"):

    # Create a thread
    thread = client.beta.threads.create()

    if "assistant_id" not in st.session_state:
        st.session_state["assistant_id"] = selected_assistant_id

    if "messages" not in st.session_state:
        st.session_state.messages = []


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
        


    if prompt := st.chat_input("Enter a messsage"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Send user message to assistant


        st.session_state.messages.append({"role": "assistant", "content": response})

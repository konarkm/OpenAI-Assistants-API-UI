import os

from dotenv import load_dotenv
import streamlit as st
import openai

st.title("OpenAI Assistants API UI")

# Load environment variables if user input is disabled
load_dotenv()

user_input = os.environ.get("USER_INPUT", "True")

# Check if user input is disabled
if user_input == "False":
    api_key = os.environ.get("OPENAI_API_KEY")
else:
    # Ask for user's OpenAI Key
    api_key = st.text_input("Enter your OpenAI Key", type="password")

# Authenticate with OpenAI
client = openai.OpenAI(api_key=api_key)

# List all assistants from your account
all_assistants = client.beta.assistants.list(
    order="desc",
    limit="20",
)
# Create a dictionary of assistant names and IDs
assistants_dict = {}
for assistant in all_assistants.data:
    assistants_dict[assistant.name] = assistant.id

# Select an assistant
selected_assistant = st.selectbox("Select Assistant", list(assistants_dict.keys()), index=0)

# Get the selected assistant ID
selected_assistant_id = assistants_dict.get(selected_assistant)

# Save the selected assistant ID to the session state
st.session_state["assistant_id"] = selected_assistant_id


# Check if a thread ID already exists in the session state, otherwise create a new thread
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id
else:
    thread = client.beta.threads.retrieve(st.session_state["thread_id"])

# Check if a messages list already exists in the session state, otherwise create a new list
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
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
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    # Run assistant with user input
    run = client.beta.threads.runs.create_and_poll(
       thread_id=thread.id,
       assistant_id=st.session_state["assistant_id"],
    #    instructions=""
    )

    # Get messages from the thread
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    # Get the latest assistant response
    response = messages.data[0].content[0].text.value

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

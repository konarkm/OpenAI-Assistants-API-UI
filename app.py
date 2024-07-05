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

# The assistant's vector store ID can be retrieved when creating the assistants_dict, but is being done here for code readability.
# Retrieve the selected assistant's information
selected_assistant_info = client.beta.assistants.retrieve(st.session_state["assistant_id"])

# Get the selected assistant's vector store ID
try:
    vector_store_id = selected_assistant_info.tool_resources.file_search.vector_store_ids[0]
except:
    st.error("Error retrieving the selected assistant's vector store ID. This can happen if the assistant does not have a vector store.")
    st.stop()
    

vector_store = client.beta.vector_stores.retrieve(
  vector_store_id=vector_store_id
)



def get_files_dict():
    # Get the list of files in the vector store
    vector_store_files = client.beta.vector_stores.files.list(
    vector_store_id=vector_store_id
    )

    # Create a list of file IDs
    vector_store_files_list = [file.id for file in vector_store_files.data]

    # This is necessary because currently, the list of vector store files has file IDs and "objects" but not the file names.
    # Create a dictionary of file names and IDs
    vector_store_files_dict = {}
    for file_id in vector_store_files_list:
        file = client.files.retrieve(file_id)
        vector_store_files_dict[file.filename] = file.id
    
    return vector_store_files_dict

# Display files
def display_files():
    # Display the list of files in the vector store
    st.sidebar.subheader("Files in Vector Store")
    if not vector_store_files_dict:
        st.sidebar.markdown("Vector Store is Empty")
    else:
        st.sidebar.markdown(f"Total Files: {len(vector_store_files_dict)}")
        for file in vector_store_files_dict:
            st.sidebar.markdown(f"- {file}")



# Upload file menu
def upload_file():
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0

    # File selection menu
    file_path = st.sidebar.file_uploader(
        "Upload a file",
        accept_multiple_files=False, # Not accepting multiple files for now. Support can be added with a for loop and some logic in the duplicate file check.  
        key=st.session_state["file_uploader_key"]
    )

    if file_path is not None:
        # Check if the file already exists in the vector store
        if file_path.name in vector_store_files_dict:
            st.sidebar.error("File already exists in the vector store")
        else:
            # Upload file to OpenAI
            uploaded_file = client.files.create(
                file=file_path,
                purpose="assistants"
            )

            # Link the uploaded file to the vector store
            vector_store_file = client.beta.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=uploaded_file.id
            )

            # Display success message
            st.sidebar.success("File uploaded successfully")
            # Increment the file uploader key to refresh the file uploader
            st.session_state["file_uploader_key"] += 1
            st.rerun()


def delete_file():
    # Select a file to delete
    selected_file = st.sidebar.selectbox("Select File to Delete", list(vector_store_files_dict.keys()))
    file_id_to_delete = vector_store_files_dict.get(selected_file)

    # Delete file button
    if st.sidebar.button("Delete File"):
        if file_id_to_delete:
            # Delete file from vector store
            client.beta.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id_to_delete)
            # Delete file from OpenAI Files
            client.files.delete(file_id=file_id_to_delete)
            st.sidebar.success("File deleted successfully")
            st.rerun()
        else:
            st.sidebar.error("No file selected")


# Add a streamlit sidebar
st.sidebar.title("Files")




vector_store_files_dict = get_files_dict()


display_files()


upload_file()




delete_file()

# Chat UI
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

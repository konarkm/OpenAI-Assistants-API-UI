import os

from dotenv import load_dotenv
import streamlit as st
import openai
import time



def get_client():
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

    return client

def initialize_assistant(client):
    
    vector_store = client.beta.vector_stores.create(
    name="Default Assistants Vector Store"
    )

    my_assistant = client.beta.assistants.create(
        instructions="You are a helpful assistant.",
        name="Default Assistant",
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        model="gpt-4o",
    )

    return

def select_assistant(client):
    # List all assistants from your account
    all_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )

    if all_assistants.data == []:
        st.error("No assistants found in your OpenAI account. Creating a default assistant and reloading in 5 seconds.")
        initialize_assistant(client)
        time.sleep(5)
        st.rerun()

    # Create a dictionary of assistant names and IDs
    assistants_dict = {}
    for assistant in all_assistants.data:
        assistants_dict[assistant.name] = assistant.id

    # Select an assistant
    selected_assistant = st.sidebar.selectbox("Select Assistant", list(assistants_dict.keys()), index=0)

    # Get the selected assistant ID
    selected_assistant_id = assistants_dict.get(selected_assistant)

    old_assistant_id = st.session_state.get("assistant_id")

    if old_assistant_id != selected_assistant_id:
        # Clear the session state if the assistant is changed
        for key in st.session_state.keys():
            del st.session_state[key]

    # Save the selected assistant ID to the session state
    st.session_state["assistant_id"] = selected_assistant_id

    return



def get_vector_store_id(client):

    # The assistant's vector store ID can be retrieved when creating the assistants_dict, but is being done here for code readability.

    # Check if an vector store ID exists in the session state, otherwise get it from the API
    if "vector_store_id" not in st.session_state:
        # Retrieve the selected assistant's information
        selected_assistant_info = client.beta.assistants.retrieve(st.session_state["assistant_id"])

        # Get the selected assistant's vector store ID
        try:
            vector_store_id = selected_assistant_info.tool_resources.file_search.vector_store_ids[0]
        except:
            st.error("Error retrieving the selected assistant's vector store ID. This can happen if the assistant does not have a vector store.")
            st.stop()      

        # vector_store = client.beta.vector_stores.retrieve(
        # vector_store_id=vector_store_id
        # )
    else:
        vector_store_id = st.session_state["vector_store_id"]

    return vector_store_id



def get_files_dict(client, vector_store_id):
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
def display_files(vector_store_files_dict):
    # Display the list of files in the vector store
    st.sidebar.subheader("Files in Vector Store:")
    if not vector_store_files_dict:
        st.sidebar.markdown("Vector Store is Empty")
    else:
        container = st.sidebar.container(border=True)
        for file in vector_store_files_dict:
            container.write(f"- {file}")
        st.sidebar.markdown(f"Total Files: {len(vector_store_files_dict)}")


# Upload file menu
def upload_file(client, vector_store_files_dict, vector_store_id):
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
            time.sleep(1)

            # Increment the file uploader key to refresh the file uploader
            st.session_state["file_uploader_key"] += 1
            st.rerun()

def upload_image(client, thread):
    if "image_uploader_key" not in st.session_state:
        st.session_state["image_uploader_key"] = 1000

    # Image selection menu
    image_path = st.file_uploader(
        "Upload an image",
        accept_multiple_files=False, # Not accepting multiple images for now. Support can be added with a for loop and some logic in the duplicate image check.  
        key=st.session_state["image_uploader_key"]
    )

    if image_path is not None:
        # Upload image to OpenAI
        uploaded_image = client.files.create(
            file=image_path,
            purpose="vision"
        )

        # Send user message to assistant
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=[
                {
                    "type": "image_file",
                    "image_file": {
                        "file_id": uploaded_image.id,
                        "detail": "high"
                        }
                }
            ]
        )

        # Display success message
        st.sidebar.success("Image uploaded successfully")
        time.sleep(1)

        # Increment the image uploader key to refresh the image uploader
        st.session_state["image_uploader_key"] += 1

        st.session_state.messages.append({"role": "user", "content": "Image: " + uploaded_image.filename})

        st.rerun()


def delete_file(client, vector_store_files_dict, vector_store_id):
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
            # Wait added to allow for OpenAI to process the deletion (before the code reruns and the file list is retrieved again)
            time.sleep(2)
            st.rerun()
        else:
            st.sidebar.error("No file selected")


def get_thread(client):
    # Check if a thread ID already exists in the session state, otherwise create a new thread
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id
    else:
        thread = client.beta.threads.retrieve(st.session_state["thread_id"])
    return thread


def display_messages():
    # Check if a messages list already exists in the session state, otherwise create a new list
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def chat(client, thread):
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



def main():
    
    # Set the title of the streamlit app
    st.title("Assistants UI")

    client = get_client()

    st.sidebar.title("Assistant")
    select_assistant(client)

    st.sidebar.title("Files")

    vector_store_id = get_vector_store_id(client)

    vector_store_files_dict = get_files_dict(client, vector_store_id)

    display_files(vector_store_files_dict)

    upload_file(client, vector_store_files_dict, vector_store_id)

    delete_file(client, vector_store_files_dict, vector_store_id)

    thread = get_thread(client)

    upload_image(client, thread)

    display_messages()

    chat(client, thread)


if __name__ == "__main__":
    main()
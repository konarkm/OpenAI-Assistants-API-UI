# OpenAI-Assistants-API-UI
### A simple Streamlit app for the Assistants API from OpenAI.

This Streamlit app is intended to provide a starting point for Assistants Development, Testing, and Proof of Concepts.

Something to note is that files upload into the chosen Assistants vector store (as opposed to just being temporary attachments in the current thread).


## Usage

1. Clone the repository
   
```bash
$ git clone https://github.com/konarkm/OpenAI-Assistants-API-UI.git
```

2. Get API key from OpenAI (https://platform.openai.com/api-keys)

3. Create a .env file in the main directory containing the following:
```bash
USER_INPUT = "False"

"OPENAI_API_KEY" = <Your OpenAI API Key>
```
> If you don't create this file, you will be prompted for an API key every time the page is reloaded.

4. Install dependencies
```bash
pip install -r /path/to/requirements.txt
```

5. Then change to the main directory and run using Streamlit
```bash
streamlit run app.py
```

> If you do not have any Assistants in your OpenAI account/keys project, a default assistant and linked vector store will be created for you.


## Custom Assistant Setup (Optional)

If you would like to use a custom assistant (allowing for custom instructions, etc.) you can set one up in the OpenAI portal (https://platform.openai.com/assistants). The Assistant(s) will then be available in the Assistant selection dropdown window in the app.

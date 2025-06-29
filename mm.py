import streamlit as st
import os
import uuid
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from gtts import gTTS
import base64
import re

# ---------------- Clean Text for TTS ----------------
def clean_text_for_tts(text):
    # Remove HTML tags like <br>, <b>, etc.
    text = re.sub(r'<.*?>', ' ', text)
    # Remove markdown and bullet symbols
    text = re.sub(r'[*_`#>\-•]', '', text)
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ---------------- Text to Speech ----------------
def text_to_audio(text):
    cleaned_text = clean_text_for_tts(text)
    tts = gTTS(cleaned_text, lang='en')
    tts.save("output.mp3")
    with open("output.mp3", "rb") as audio_file:
        audio_bytes = audio_file.read()
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
        <audio controls autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

# ---------------- Load API Key ----------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY is not set. Check .env file.")
    st.stop()

client = Groq(api_key=api_key)

# ---------------- Session State ----------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_history" not in st.session_state:
    st.session_state.session_history = {}

# ---------------- Page Config ----------------
st.set_page_config(page_title="AI Chatbot", page_icon="💬", layout="wide")

# ---------------- Sidebar ----------------
URL = "https://lang-guru-1.vercel.app/"
with st.sidebar:
    st.image('logo.png', width=200)

    theme = st.radio("🌗 Select Theme", ["Light", "Dark"], horizontal=True)

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0;">📝 Chat History</h3>
            <a href="{URL}" target="_self">
                <button class="custom-button">🔙 Back</button>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for session_key, session_data in st.session_state.session_history.items():
        session_label = session_data['title']
        if st.button(session_label):
            st.session_state.chat_history = session_data['history']
            st.session_state.selected_session = session_key
            st.session_state.session_summary = session_data.get('summary', None)

    if st.button("🆕 New Chat"):
        st.session_state.chat_history = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.selected_session = None
        st.session_state.session_summary = None

    if st.button("🗑️ Clear All Chats"):
        st.session_state.session_history = {}

    if st.button("📌 Summarize Session"):
        if st.session_state.chat_history:
            all_chats_text = "\n".join(
                [f"User: {chat['user']}\nBot: {' '.join(chat['bot'])}" for chat in st.session_state.chat_history]
            )
            try:
                summary_response = client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": f"Summarize this chat session:\n{all_chats_text}"}
                    ],
                    model="llama-3.3-70b-versatile",
                )
                if summary_response and summary_response.choices:
                    st.session_state.session_summary = summary_response.choices[0].message.content
                    st.success("Summary generated!")
            except Exception as e:
                st.error(f"Error summarizing: {e}")

# ---------------- CSS Styling ----------------
light_theme = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
body {
    background-color: #F4F6FA;
    color: #000;
    font-family: 'Poppins', sans-serif;
}
.custom-button {
    background: linear-gradient(135deg, #6A11CB 0%, #2575FC 100%);
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 8px;
    cursor: pointer;
}
.user-message {
    background-color: #DCF8C6;
    border-radius: 12px;
    padding: 10px;
    margin-left: auto;
    max-width: 70%;
}
.bot-message {
    background-color: #FFFFFF;
    border-radius: 12px;
    padding: 10px;
    margin-right: auto;
    max-width: 70%;
}
</style>
"""

dark_theme = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
body {
    background-color: #121212;
    color: #FFFFFF;
    font-family: 'Poppins', sans-serif;
}
.custom-button {
    background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%);
    color: black;
    border: none;
    padding: 6px 12px;
    border-radius: 8px;
    cursor: pointer;
}
.user-message {
    background-color: #4CAF50;
    border-radius: 12px;
    padding: 10px;
    margin-left: auto;
    max-width: 70%;
}
.bot-message {
    background-color: #1E1E1E;
    border-radius: 12px;
    padding: 10px;
    margin-right: auto;
    max-width: 70%;
}
</style>
"""

st.markdown(dark_theme if theme == "Dark" else light_theme, unsafe_allow_html=True)

# ---------------- Main Chat Area ----------------
st.title("💬 AI Chatbot")
st.write(f"Session ID: `{st.session_state.session_id}`")

if st.session_state.get("session_summary"):
    st.subheader("📌 Session Summary")
    st.markdown(st.session_state.session_summary)

if st.session_state.get("selected_session"):
    selected_session = st.session_state.selected_session
    if selected_session in st.session_state.session_history:
        chat_history = st.session_state.session_history[selected_session]['history']
        st.subheader("Previous Conversation")
        for chat in chat_history:
            st.write(f"**You:** {chat['user']}")
            st.write(f"**Bot:** {' '.join(chat['bot'])}")

st.markdown("---")
st.write("### 💬 Chat")

# ---------------- Chat History Display ----------------
chat_container = st.container()

for chat in st.session_state.chat_history:
    with chat_container:
        st.markdown(
            f"<div class='user-message'><b>You:</b> {chat['user']}</div>",
            unsafe_allow_html=True,
        )
        bot_response = '<br>'.join(chat['bot'])
        st.markdown(
            f"<div class='bot-message'><b>Bot:</b> {bot_response}</div>",
            unsafe_allow_html=True,
        )

        # 🔊 Voice Output Button
        if st.button(f"🔊 Play Response ({chat['date']})", key=f"audio-{chat['date']}"):
            text_to_audio(bot_response)

# ---------------- Chat Input Processing ----------------
def process_input():
    user_input = st.session_state.chat_input.strip()
    if user_input:
        with st.spinner("🤖 Thinking..."):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": f"You are a helpful assistant. {user_input} Give a short, bullet-pointed response.",
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                )

                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if chat_completion and chat_completion.choices:
                    response_content = chat_completion.choices[0].message.content
                    response_list = [line.strip() for line in response_content.split("\n") if line.strip()]

                    new_chat = {"date": current_date, "user": user_input, "bot": response_list}
                    st.session_state.chat_history.append(new_chat)

                    if st.session_state.session_id not in st.session_state.session_history:
                        st.session_state.session_history[st.session_state.session_id] = {
                            'history': [],
                            'summary': None,
                            'title': user_input
                        }
                    st.session_state.session_history[st.session_state.session_id]['history'].append(new_chat)

                    st.session_state.selected_session = st.session_state.session_id
                    st.session_state.chat_input = ""

            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- Chat Input ----------------
user_input = st.text_input(
    "Type a message...",
    key="chat_input",
    placeholder="Ask me anything...",
    on_change=process_input
)

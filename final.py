import streamlit as st
import os
import uuid
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from gtts import gTTS
import base64
import re
import speech_recognition as sr

# --------------- 🔥 PAGE CONFIG ---------------
st.set_page_config(page_title="💬 Voice AI Chatbot", page_icon="💬", layout="wide")

# --------------- 🌐 Load API Key ---------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("🚫 GROQ_API_KEY not set. Check your .env file.")
    st.stop()

client = Groq(api_key=api_key)

# --------------- 💾 Session Management ---------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_history" not in st.session_state:
    st.session_state.session_history = {}

# --------------- 🌍 Language Mapping ---------------
lang_map = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Kannada": "kn"
}

# --------------- 🚀 Functions ---------------
def clean_text_for_tts(text):
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[*_`#>\-•]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def text_to_audio(text):
    cleaned_text = clean_text_for_tts(text)
    tts = gTTS(cleaned_text, lang=selected_lang_code)
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

def transcribe_audio(language_code="en-IN"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening...")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio, language=language_code)
            st.success(f"🗣️ You said: {text}")
            return text
        except sr.UnknownValueError:
            st.error("❌ Could not understand.")
        except sr.RequestError as e:
            st.error(f"❌ Request Error: {e}")
    return ""

def process_input():
    user_input = st.session_state.chat_input.strip()
    if user_input:
        with st.spinner("🤖 Thinking..."):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": f"You are a helpful assistant. {user_input} Give a short, bullet-pointed response."
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
                st.error(f"❌ Error: {e}")

# --------------- 🎨 Sidebar ---------------
with st.sidebar:
    st.image("logo.png", width=220)

    st.title("⚙️ Settings")

    theme = st.radio("🎨 Theme", ["Light", "Dark"], horizontal=True)

    voice_lang = st.radio(
        "🎙️ Voice Language",
        ["English", "Hindi", "Telugu", "Kannada"]
    )
    selected_lang_code = lang_map[voice_lang]

    st.subheader("🎤 Voice Input")
    if st.button("🎙️ Speak"):
        voice_input = transcribe_audio(language_code=f"{selected_lang_code}-IN")
        if voice_input:
            st.session_state.chat_input = voice_input
            process_input()

    st.markdown("## 📜 Chat History")

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
                    st.success("✅ Summary generated!")
            except Exception as e:
                st.error(f"❌ Error summarizing: {e}")

    st.markdown("---")
    st.markdown("🔗 [Back to Home](https://lang-guru-1.vercel.app/)")

# --------------- ✨ CSS Styling ---------------
light_theme = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
body {
    background-color: #F9FAFB;
    color: #000000;
    font-family: 'Poppins', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    color: #111827;
}
.stMarkdown, .stTextInput label, .stButton, .stRadio label {
    color: #111827 !important;
}
.user-message {
    background-color: #E0F7FA;
    color: #000000;
    border-radius: 12px;
    padding: 10px;
    margin-left: auto;
    max-width: 70%;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
}
.bot-message {
    background-color: #FFFFFF;
    color: #000000;
    border-radius: 12px;
    padding: 10px;
    margin-right: auto;
    max-width: 70%;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
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

# 👉 Optional Floating Chat Input CSS
st.markdown("""
<style>
.input-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 10px;
}
.stTextInput>div>div>input {
    border-radius: 12px;
    padding: 10px 14px;
    border: 1px solid #ccc;
}
</style>
""", unsafe_allow_html=True)


# --------------- 🏠 Main Section ---------------
st.title("💬 Voice AI Chatbot")
st.caption(f"Session ID: `{st.session_state.session_id}`")

if st.session_state.get("session_summary"):
    st.subheader("📌 Session Summary")
    st.markdown(st.session_state.session_summary)

st.markdown("---")

# 💬 Chat messages display
chat_container = st.container()

for chat in st.session_state.chat_history:
    with chat_container:
        st.markdown(
            f"<div class='user-message'><b>🧑 You:</b> {chat['user']}</div>",
            unsafe_allow_html=True,
        )
        bot_response = '<br>'.join(chat['bot'])
        st.markdown(
            f"<div class='bot-message'><b>🤖 Bot:</b> {bot_response}</div>",
            unsafe_allow_html=True,
        )

        if st.button(f"🔊 Play ({chat['date']})", key=f"audio-{chat['date']}"):
            text_to_audio(bot_response)

# --------------- 🗣️ Chat Input Box at Bottom ---------------
st.text_input(
    "💬 Type a message or use voice...",
    key="chat_input",
    placeholder="Type your message here...",
    on_change=process_input,
    label_visibility="collapsed"  # Hide label for clean look
)

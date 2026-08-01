import os

os.environ["GRPC_VERBOSITY"] = "ERROR"

import asyncio
import base64
import re

import edge_tts
import speech_recognition as sr
import streamlit as st

from lib.main import query

st.set_page_config(page_title="Mouthy Man", page_icon="🎓", layout="centered")
st.title("Mouthy Man")

with st.container(border=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        typed_query = st.text_input(
            "Ask something", label_visibility="collapsed", placeholder="Ask something..."
        )
    with col2:
        audio_value = st.audio_input("Voice", label_visibility="collapsed")

    user_query = typed_query
    if audio_value:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_value) as source:
            audio = recognizer.record(source)
        user_query = recognizer.recognize_google(audio)
        st.caption(f"Transcribed: {user_query}")

    send = st.button("Send", use_container_width=True)


def clean_for_speech(text: str) -> str:
    text = re.sub(r"[*_#`]", "", text)
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", text).strip()


async def synthesize(text: str, path: str):
    await edge_tts.Communicate(text, voice="en-US-AriaNeural").save(path)


def speak(text: str):
    path = "response.mp3"
    asyncio.run(synthesize(clean_for_speech(text), path))
    st.audio(path, autoplay=True)


def show_pdf(path: str):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    with st.expander(os.path.basename(path), expanded=True):
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700"></iframe>',
            unsafe_allow_html=True,
        )


if send and user_query:
    with st.spinner("Thinking..."):
        result = query(user_query)

    with st.chat_message("assistant"):
        if result.pdf_paths:
            for path in result.pdf_paths:
                show_pdf(path)
        else:
            st.write(result.response)
            if result.intent == "general_doubt":
                speak(result.response)
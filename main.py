import asyncio
import time

import uvicorn
import threading
from fastapi import FastAPI

import api
from api import app
import streamlit as st
import streamlit.components.v1 as components


lock = threading.Lock()


if __name__ == "__main__":

    iframe_src = "https://youtube.com"
    components.iframe(iframe_src)
    st.write("""
        # My first app
        Hello *world!*
    """)

    for key, value in api.past_second.items():
        st.image(value)

    threading.Thread(target=lambda: uvicorn.run("api:app", host="0.0.0.0", port=8000)).start()


async def display_video(id_: int):
    # todo: move framerate to a constant
    for key, value in api.past_second.values():
        with lock.acquire():
            st.image(value)
            time.sleep(1/24)
import datetime
import json
import threading
from time import strftime, gmtime

import pandas as pd
import streamlit as st
import requests

lock = threading.Lock()

with open("config.json", "r") as f:
    config = json.load(f)
api_url = config["api_url"]
api_port = config["api_port"]


events = requests.get(f"{api_url}:{api_port}/api/events").json()
sorted_events = {key: [] for key in set([i["device"] for i in events])}

for event in events:
    sorted_events[event["device"]].append(event)
with open("log.txt", "w") as f:
    f.write(str(sorted_events))

devices = range(0, 6)

for device in sorted(sorted_events.keys()):
    st.header(f"Device {int(device)}")

    rows = []
    for i in sorted_events[device]:
        # rows.append([j.decode("utf-8") for i, j in i.items()])
        rows.append([j for i, j in i.items()])
    for event in rows:
        event[1] = datetime.datetime.fromtimestamp(int(event[1]))
        event[2] = datetime.datetime.fromtimestamp(int(event[2]))
        event.insert(3, strftime("%H:%M:%S", gmtime((event[2] - event[1]).total_seconds())))
        event[-1] = f"http://localhost:8000/events/videos/{event[-1]}"
    for i in range(len(rows)):
        del rows[i][0]

    st.subheader("Past Events")
    data = pd.DataFrame(
        columns=["Movement Start", "Movement End", "Time Elapsed", "Video Path"],
        data=rows
    )
    st.dataframe(
        data,
        column_config={
            "Video Path": st.column_config.LinkColumn()
        },
        hide_index=True
    )



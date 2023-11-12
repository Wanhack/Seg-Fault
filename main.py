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
api_url = f'{config["api_url"]}:{config["api_port"]}'


events = requests.get(f"{api_url}/api/events").json()
sorted_events = {key: [] for key in set([i["device"] for i in events])}

for event in events:
    sorted_events[event["device"]].append(event)
with open("log.txt", "w") as f:
    f.write(str(sorted_events))

devices = range(0, 6)

for device in sorted(sorted_events.keys()):
    st.markdown(f"## [Device {int(device)}]({api_url}/api/live/{int(device)})")

    rows = []
    for i in sorted_events[device]:
        rows.append([j for i, j in i.items()])
    for event in rows:
        elapsed = int(event[2]) - int(event[1])
        event[1] = datetime.datetime.fromtimestamp(int(event[1]))
        event[2] = datetime.datetime.fromtimestamp(int(event[2]))
        event.insert(3, strftime("%H:%M:%S", gmtime((event[2] - event[1]).total_seconds())))
        event[-1] = f"{api_url}/events/videos/{event[-1]}"
    for i in range(len(rows)):
        del rows[i][0]
    st.markdown("### Notable Events")
    rows = [i for i in rows if i[1].timestamp() - i[0].timestamp() > 60]

    st.dataframe(
        pd.DataFrame(
            columns=["Movement Start", "Movement End", "Time Elapsed", "Video Path"],
            data=rows
        ),
        column_config={
            "Video Path": st.column_config.LinkColumn()
        },
        hide_index=True
    )

    st.markdown("#### All Events")

    st.dataframe(
        data = pd.DataFrame(
            columns=["Movement Start", "Movement End", "Time Elapsed", "Video Path"],
            data=rows
        ),
        column_config={
            "Video Path": st.column_config.LinkColumn()
        },
        hide_index=True
    )



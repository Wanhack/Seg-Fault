import datetime
import json
import threading
from time import strftime, gmtime

import pandas as pd
import streamlit as st
import uvicorn
import api


events = {}

lock = threading.Lock()

with open("config.json", "r") as f:
    config = json.load(f)

if __name__ == "__main__":
    events = api.get_events()
    sorted_events = {key: [] for key in set([i[b"device"] for i in events])}

    for event in events:
        sorted_events[event[b"device"]].append(event)
    with open("log.txt", "w") as f:
        f.write(str(sorted_events))

    devices = range(0, 6)

    for device in sorted_events.keys():
        st.header(f"Device {int(device)}")

        rows = []
        for i in sorted_events[device]:
            rows.append([j.decode("utf-8") for i, j in i.items()])
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

    threading.Thread(target=lambda: uvicorn.run("api:app", host=config["api_host"], port=config["api_port"])).start()


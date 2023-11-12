import copy
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


st.set_page_config(page_title="WatchfulWiggles", page_icon=":baby:", layout="wide")

st.markdown("# WatchfulWiggles :baby:")
st.markdown("Here you can view your baby monitors' live feeds as well as past events.")
st.markdown("All of your registered devices are listed below. Click on a device to view its live feed,\
 and expand the device to view its past events.")
st.markdown("You can also view all events from all devices by clicking the button at the bottom of the page.")

events = requests.get(f"{api_url}/api/events").json()
sorted_events = {key: [] for key in set([i["device"] for i in events])}

for event in events:
    sorted_events[event["device"]].append(event)

for device in sorted(sorted_events.keys()):
    st.markdown(f"### [Device {int(device)}]({api_url}/api/live/{int(device)})")
    with st.expander("View Events"):
        rows = []
        for i in sorted_events[device]:
            rows.append([j for i, j in i.items()])
        for event in rows:
            event[1] = int(float(event[1]))
            event[2] = int(float(event[2]))
            elapsed = event[2] - event[1]
            event[1] = datetime.datetime.fromtimestamp(event[1])
            event[2] = datetime.datetime.fromtimestamp(event[2])
            event.insert(3, strftime("%H:%M:%S", gmtime((event[2] - event[1]).total_seconds())))
            event[-1] = f"{api_url}/events/videos/{event[-1]}"
        for i in range(len(rows)):
            del rows[i][0]
        st.markdown("### Notable Events")
        notable_rows = [i for i in rows if i[1].timestamp() - i[0].timestamp() > 60]

        st.dataframe(
            pd.DataFrame(
                columns=["Movement Start", "Movement End", "Time Elapsed", "Video Path"],
                data=notable_rows
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

st.markdown('### All events')

to_display = copy.deepcopy(events)
for event in to_display:
    event["duration"] = int(float(event['movement_end'])) - int(float(event['movement_start']))
    event['video_path'] = f"{api_url}/events/videos/{event['video_path']}"

with st.expander('View All Events'):
    st.dataframe(
        data=to_display,
        column_config={
            "video_path": st.column_config.LinkColumn()
        },
        hide_index=True
    )

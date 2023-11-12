# import the opencv library
import asyncio
import io
import sys
import traceback

import cv2
import aiohttp
import json

with open("config.json", "r") as f:
    config = json.load(f)


async def main():
    cv2.destroyAllWindows()
    async with aiohttp.ClientSession() as session:

        # define a video capture object
        vid = cv2.VideoCapture(0)
        vid.set(cv2.CAP_PROP_FPS, 24)
        try:
            while True:
                ret, frame = vid.read()
                cv2.resize(frame, (600,600))
                is_success, buffer = cv2.imencode(".jpg", frame)
                io_buf = io.BytesIO(buffer)
                async with session.post(f'{config["api_url"]}:{config["api_port"]}/api/frame/{config["device_id"]}', data={"file": io_buf}) as resp:
                    pass
        except Exception as e:
            traceback.print_exc()
            vid.release()
            cv2.destroyAllWindows()

asyncio.run(main())
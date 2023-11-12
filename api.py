import asyncio
import dataclasses
import json
import os
import shutil
import time
import ffmpeg
import cv2
import numpy as np
import redis
from fastapi import Request, UploadFile, File, FastAPI, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.templating import Jinja2Templates
import send_alert

with open("creds.json", "r") as f:
    creds = json.load(f)

with open("config.json", "r") as f:
    config = json.load(f)

r = redis.Redis(host=creds["host"], username=creds["username"], password=creds["password"], port=creds["port"], db=0)

templates = Jinja2Templates(directory="templates")

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclasses.dataclass
class DeviceParams:
    id: int = 0
    consecutive_detects: int = 0
    past_second: list = dataclasses.field(default_factory=list)
    motion_start: int = 0
    motion_end: int = 0
    capturing: bool = False
    captured_frames: list = dataclasses.field(default_factory=list)
    saving: bool = False


params = {}


@app.post("/api/frame/{device}")
async def post_frame(request: Request, device: int, file: UploadFile = File(...)):
    if device not in params:
        params[device] = DeviceParams()
    params[device].id = device
    request_object_content = await file.read()
    file_bytes = np.asarray(bytearray(request_object_content), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    params[device].past_second.append(img)
    if params[device].capturing:
        if len(params[device].captured_frames) == 0:
            params[device].captured_frames = [i for i in params[device].past_second]
        params[device].captured_frames.append(img)
    if len(params[device].past_second) > 24:
        del params[device].past_second[0]

    asyncio.create_task(detect_motion(device))
    print("returned!")
    return Response(content="OK")


@app.get("/api/movement/{device}")
async def get_movement(device: int):
    return {'motion': await detect_motion(device)}


@app.get("/api/events")
def get_events():
    resp = r.keys("*entry*")
    events = []
    for key in resp:
        events.append(r.hgetall(key))
    return events


# noinspection PyAsyncCall
async def detect_motion(device: int) -> bool:
    if params[device].consecutive_detects > config["threshold"] * 24:
        if params[device].motion_start == 0:
            params[device].motion_start = int(time.time() - 10)
            params[device].capturing = True

    movement_found = 0
    previous_frame = None
    for frame in params[device].past_second:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if previous_frame is None:
            previous_frame = gray
            continue
        frame_delta = cv2.absdiff(previous_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) < config["sensitivity"]:
                continue
            movement_found += 1
        previous_frame = gray
    if movement_found > config["frames_required"]:
        params[device].consecutive_detects += 1
        return True
    params[device].consecutive_detects = 0
    if params[device].capturing and not params[device].saving:
        params[device].capturing = False
        params[device].motion_end = int(time.time())
        filename = f"{device}_{params[device].motion_start}.mp4"
        r.hset(f"{device}_entry_{params[device].motion_start}", mapping={
            "device": device,
            "movement_start": params[device].motion_start,
            "movement_end": params[device].motion_end,
            "video_path": filename
        })
        if config["send_alerts"]:
            for i in config["email_recipients"]:
                send_alert.send_email(device, params[device].motion_start, i)
        asyncio.create_task(save_video(params[device], filename))
        params[device] = DeviceParams()

    return False


async def save_video(device: DeviceParams, filename: str):
    device.saving = True
    tmp_dir = "tmp"
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    for idx, frame in enumerate(device.captured_frames):
        cv2.imwrite(f"tmp/{device.id}_{idx:02}.jpg", frame)

    (ffmpeg.input(os.path.join(tmp_dir, "*.jpg"), pattern_type='glob', framerate=24)
     .output(os.path.join(os.path.join("events", "videos"), filename)).run())

    device.captured_frames = []
    shutil.rmtree(tmp_dir)
    del device


@app.get("/api/live/{device}")
async def live(request: Request, device: int):
    return templates.TemplateResponse("stream.html", {"request": request, "device": device})


@app.get('/api/stream/{device}')
async def stream(device: int):
    if device not in params:
        params[device] = DeviceParams()
    if len(params[device].past_second) == 0:
        return
    frame = params[device].past_second[-1]
    is_success, buffer = cv2.imencode(".jpg", frame)
    return Response(content=buffer.tobytes(), media_type="image/png")


@app.get("/events/videos/{filename}")
async def get_video(filename: str):
    return FileResponse(os.path.join("events", "videos", filename))
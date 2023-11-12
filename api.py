import cv2
import numpy as np
from fastapi import APIRouter, Request, UploadFile, File, FastAPI

app = FastAPI()
consecutive_detects = {}
past_second = {}


@app.post("/api/frame/{id_}")
async def post_frame(request: Request, id_: int, file: UploadFile = File(...)):
    if id_ not in consecutive_detects:
        consecutive_detects[id_] = 0
    if id_ not in past_second:
        past_second[id_] = []
    request_object_content = await file.read()
    file_bytes = np.asarray(bytearray(request_object_content), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    past_second[id_].append(img)
    if len(past_second[id_]) > 24:
        past_second[id_].pop(0)


@app.get("/api/movement/{id_}")
async def get_movement(id_: int):
    return {'motion': await detect_motion(id_)}


async def detect_motion(id_: int) -> bool:
    global consecutive_detects
    if id_ not in consecutive_detects:
        consecutive_detects[id_] = 0
    if id_ not in past_second:
        past_second[id_] = []
    movement_found = 0
    previous_frame = None
    for frame in past_second[id_]:
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
            if cv2.contourArea(contour) < 500:
                continue
            movement_found += 1
        previous_frame = gray
    if movement_found > 12:
        consecutive_detects[id_] += 1
        return True
    consecutive_detects[id_] = 0
    return False

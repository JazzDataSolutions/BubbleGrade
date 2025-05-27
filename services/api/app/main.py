
from fastapi import FastAPI, UploadFile, BackgroundTasks, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx, os, uuid, shutil, asyncio, aiofiles

app = FastAPI(title="BubbleGrade API")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "web")
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

OMR_URL = os.getenv("OMR_URL", "http://omr:8090/grade")

async def call_omr(scan_path: str, scan_id: str):
    async with httpx.AsyncClient() as client:
        with open(scan_path, "rb") as f:
            files = {"file": (os.path.basename(scan_path), f, "image/jpeg")}
            resp = await client.post(OMR_URL, files=files)
            resp.raise_for_status()
            result = resp.json()
    # TODO: store in DB; simplified demo
    outfile = f"{scan_id}.xlsx"
    with open(outfile, "wb") as out:
        out.write(b"dummy excel")
    return outfile

@app.post("/api/scans")
async def upload_scan(file: UploadFile, tasks: BackgroundTasks):
    scan_id = str(uuid.uuid4())
    dest = f"/tmp/{scan_id}_{file.filename}"
    async with aiofiles.open(dest, "wb") as out:
        content = await file.read()
        await out.write(content)
    tasks.add_task(call_omr, dest, scan_id)
    return {"id": scan_id, "status": "QUEUED"}

@app.get("/api/exports/{scan_id}")
async def export(scan_id: str):
    # demo path
    path = f"{scan_id}.xlsx"
    return FileResponse(path, filename=f"{scan_id}.xlsx")

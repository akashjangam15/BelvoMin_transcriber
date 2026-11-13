from fastapi import FastAPI
from pydantic import BaseModel
from nlp_module import process_meeting

app = FastAPI(
    title="BELVO MINUTES",
    description="AI-Powered Meeting Intelligence Platform",
    version="1.0"
)


class MeetingInput(BaseModel):
    transcript: str


@app.get("/")
def home():
    return {
        "message": "Welcome to BELVO MINUTES!",
        "status": "Running"
    }


@app.post("/process-meeting")
def process_audio_transcript(data: MeetingInput):

    if not data.transcript.strip():
        return {"error": "Transcript cannot be empty"}

    result = process_meeting(data.transcript)

    return {
        "project": "BELVO MINUTES",
        "summary": result["summary"],
        "decisions": result["decisions"],
        "transcript": result["transcript"]
    }
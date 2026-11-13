# Speech-to-Text Module: Setup and Demo Guide

This module converts meeting recordings (mp3 and other audio files) into a transcript with timestamps. It runs fully offline on your own machine using **faster-whisper**.

- **Input:** a path to an audio file
- **Output:** a JSON file (full text plus timestamped segments) and a readable `.txt` file
- **Not real time:** it processes a complete file after the meeting has ended

---

## 1. Prerequisites

| Requirement | Details |
|---|---|
| Python | 3.9 or newer. Check with `python --version` |
| Disk space | About 1 GB free for the model and packages |
| Internet | Needed once, to download the model on the first run |
| RAM | 4 GB minimum, 8 GB recommended for the `small` model |
| ffmpeg | Not needed. faster-whisper reads mp3 files on its own |
| GPU | Optional. It is used automatically if available |

---

## 2. Project setup

Create a folder and put `transcriber.py` in it.

```
speech_to_text/
├── transcriber.py
├── requirements.txt
├── audio/            <- put your mp3 files here
└── output/           <- transcripts are saved here
```

### Create a virtual environment

**Windows (PowerShell):**
```
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```
python3 -m venv venv
source venv/bin/activate
```

You should now see `(venv)` at the start of your terminal line.

### Install dependencies

Create `requirements.txt` containing these two lines:
```
faster-whisper
av<17
```

(`av<17` is needed because newer versions of `av` break faster-whisper's audio decoding.)

Then run:
```
pip install -r requirements.txt
```

---

## 3. First run (smoke test)

Use a short mp3 of 1 to 2 minutes. Copy it to `audio/sample.mp3`.

```
python transcriber.py audio/sample.mp3 --model base --out output/sample.json
```

What to expect:
- The first run downloads the model (roughly 150 MB for `base`). This is a one-time wait.
- You then see log lines such as `Loading model 'base' on cpu (int8)`.
- It finishes with `Saved output/sample.json and output/sample.txt`.

Open `output/sample.txt`. You should see timestamped lines like:
```
[00:00:03] Good morning everyone, let's start with the project update.
```

If this works, your setup is complete.

---

## 4. Choosing a model

| Model | Download size (approx.) | Speed on CPU | Accuracy | Best for |
|---|---|---|---|---|
| `tiny` | 75 MB | very fast | low | checking that setup works |
| `base` | 150 MB | fast | okay | quick tests |
| `small` | 480 MB | moderate | good | **recommended for the demo** |
| `medium` | 1.5 GB | slow | better | when `small` makes too many errors |
| `large-v3` | 3 GB | very slow on CPU | best | only with a GPU |

Run with a different model:
```
python transcriber.py audio/meeting.mp3 --model small --out output/meeting.json
```

Set the language if you know it (this is often more accurate than auto-detect):
```
python transcriber.py audio/meeting.mp3 --model small --language en
python transcriber.py audio/meeting.mp3 --model small --language hi
```

---

## 5. Demo script (about 5 minutes)

Prepare these before the demo:
1. A real meeting recording of 3 to 5 minutes, saved as `audio/demo.mp3`.
2. The `small` model already downloaded. Run the command in step 6 once beforehand so nothing downloads during the demo.
3. Your terminal font enlarged, and `output/` empty.

Walk through it in this order:

1. **Explain the goal.** "This takes the meeting recording and produces a timestamped transcript for the other modules."
2. **Run the command:**
   ```
   python transcriber.py audio/demo.mp3 --model small --out output/demo.json
   ```
3. **Show `output/demo.txt`.** Point out the timestamps and that punctuation is added automatically.
4. **Show `output/demo.json`.** Point out `full_text` (for summary, decisions and action items) and `segments` (for speaker identification and the dashboard timeline).
5. **Mention the performance.** The JSON includes `processing_seconds` and `duration_seconds`, so you can state exactly how fast it ran.
6. **Mention the limitations** (see section 8) honestly. Examiners usually appreciate that.

---

## 6. Using the module from code

```python
from transcriber import transcribe_audio

result = transcribe_audio("audio/meeting.mp3", model_size="small")
print(result["full_text"])
for seg in result["segments"]:
    print(seg["start"], seg["end"], seg["text"])
```

### Output format (share this with the team)

```json
{
  "audio_file": "meeting.mp3",
  "language": "en",
  "language_probability": 0.99,
  "duration_seconds": 1834.2,
  "model": "small",
  "processing_seconds": 412.5,
  "full_text": "Good morning everyone ...",
  "segments": [
    { "id": 0, "start": 0.0, "end": 4.2, "text": "Good morning everyone." }
  ]
}
```

| Field | Used by |
|---|---|
| `full_text` | summarisation, key decisions, action items |
| `segments[].start / end` | speaker identification (matching speakers by time), dashboard timeline |
| `language` | choosing the language for later steps |

### Notes for the backend

- **Run it as a background job.** A 30-minute recording can take several minutes on a CPU, so do not call it inside a normal web request.
- **The model loads once per process.** The first call is slower. Later calls reuse the loaded model.
- **Errors raised:** `FileNotFoundError` (path does not exist) and `ValueError` (empty file or unsupported format). The backend should catch both.
- **Supported formats:** mp3, wav, m4a, flac, ogg, mp4, webm.

---

## 7. Transcribing many files at once

**Mac / Linux:**
```
for f in audio/*.mp3; do python transcriber.py "$f" --model small --out "output/$(basename "$f" .mp3).json"; done
```

**Windows (PowerShell):**
```
Get-ChildItem audio\*.mp3 | ForEach-Object { python transcriber.py $_.FullName --model small --out "output\$($_.BaseName).json" }
```

Each file is processed one after another, and the model reloads every time with this approach. For many files, call `transcribe_audio` in a Python loop instead, which loads the model only once.

---

## 8. Known limitations (mention these in your report)

- Accuracy drops with background noise, overlapping speakers, strong accents and poor microphones.
- Whisper can occasionally repeat phrases or invent text on very noisy or silent sections. The built-in silence filter reduces this but does not remove it entirely.
- Mixed-language speech (for example Hindi and English in one sentence) is less accurate than a single language.
- Speaker names are not identified in this module. It only provides timestamps for the speaker-identification module to use.
- Processing on a CPU is slower than real time for the larger models.

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'faster_whisper'` | The virtual environment is not active, or the install failed. Activate `venv` and run `pip install faster-whisper` again. |
| `TypeError: open() got an unexpected keyword argument 'metadata_errors'` | The installed `av` version is too new. Run `pip install "av<17"` and try again. |
| Download is very slow or fails | Check your internet connection and retry. A partial download resumes on the next run. |
| Errors mentioning `cuda`, `cudnn` or `cublas` | The GPU libraries are missing. Force the CPU: Mac/Linux `export TRANSCRIBER_DEVICE=cpu`, Windows PowerShell `$env:TRANSCRIBER_DEVICE="cpu"`. Then run again. |
| `Audio file not found` | Check the path and the current folder. Use the full path if unsure. |
| `Unsupported audio format` | Convert the file to mp3 or wav. |
| Out of memory, or the machine freezes | Use a smaller model (`base`), and close other heavy applications. |
| Output is gibberish or in the wrong language | Pass `--language en` (or the correct code) instead of relying on auto-detect. |
| Transcript is empty | The audio may be silent or too quiet. Play the file to check, and try another recording. |
| Transcription is too slow | Use `--model base`, or run on a machine with an NVIDIA GPU. |

---

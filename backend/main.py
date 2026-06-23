import json
import os
import shutil
import requests
from datetime import datetime

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from dotenv import load_dotenv
from groq import Groq

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# Setup
# =========================

os.makedirs("backend_uploads", exist_ok=True)

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

last_report = {}

# =========================
# Analyze Endpoint
# =========================

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    global last_report

    try:

        # Save image
        file_path = f"backend_uploads/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # OCR.Space
        ocr_api_key = os.getenv("OCR_SPACE_API_KEY")

        with open(file_path, "rb") as image_file:

            ocr_response = requests.post(
                "https://api.ocr.space/parse/image",
                files={
                    "file": image_file
                },
                data={
                    "language": "eng",
                    "OCREngine": 2
                },
                headers={
                    "apikey": ocr_api_key
                }
            )

        ocr_result = ocr_response.json()

        if (
            "ParsedResults" in ocr_result
            and len(ocr_result["ParsedResults"]) > 0
        ):
            extracted_text = ocr_result["ParsedResults"][0]["ParsedText"]

        else:
            extracted_text = ""

        print("========== OCR TEXT ==========")
        print(extracted_text)
        print("==============================")

        if not extracted_text.strip():

            return {
                "ocr_text": "",
                "analysis": {
                    "error": "No text detected in screenshot"
                }
            }

        # Prompt
        prompt = f"""
You are ValorAI Coach, an elite Valorant analyst and coach.

OCR Extracted Text:
{extracted_text}

Determine whether this screenshot is related to Valorant.

If NOT related return ONLY:

{{
  "is_valorant": false,
  "reason": "Not a Valorant screenshot"
}}

If related return ONLY valid JSON:

{{
  "is_valorant": true,
  "score": 0,
  "match_type": "",
  "summary": "",
  "strengths": ["", "", ""],
  "weaknesses": ["", "", ""],
  "improvement_plan": ["", "", ""],
  "focus_area": "",
  "agent": "",
  "agent_advice": "",
  "confidence": ""
}}

Rules:
- Never leave fields empty
- Never use Unknown, N/A, None detected
- Use only visible OCR evidence
- strengths must contain 3 items
- weaknesses must contain 3 items
- improvement_plan must contain 3 items
- score between 1 and 10
- confidence must be High, Medium, or Low
- Return ONLY JSON
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=600
        )

        raw_analysis = response.choices[0].message.content

        # Parse JSON safely
        try:

            cleaned_response = raw_analysis.strip()

            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response.replace(
                    "```json",
                    ""
                )

            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.replace(
                    "```",
                    ""
                )

            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            cleaned_response = cleaned_response.strip()

            analysis = json.loads(cleaned_response)

        except Exception as e:

            analysis = {
                "error": "Failed to parse AI response",
                "raw_response": raw_analysis,
                "parse_error": str(e)
            }

        # Save latest report
        last_report = {
            "date": str(datetime.now()),
            "filename": file.filename,
            "ocr_text": extracted_text,
            "analysis": analysis
        }

        # Save history
        record = {
            "date": str(datetime.now()),
            "filename": file.filename,
            "ocr_text": extracted_text,
            "analysis": analysis
        }

        try:
            with open("history.json", "r") as f:
                history = json.load(f)
        except:
            history = []

        history.append(record)

        with open("history.json", "w") as f:
            json.dump(history, f, indent=2)

        return {
            "ocr_text": extracted_text,
            "analysis": analysis
        }

    except Exception as e:

        return {
            "ocr_text": "",
            "analysis": f"Error: {str(e)}"
        }

# =========================
# History Endpoint
# =========================

@app.get("/history")
async def get_history():

    try:
        with open("history.json", "r") as f:
            history = json.load(f)

        return history[::-1]

    except:
        return []

# =========================
# PDF Report Download
# =========================

@app.get("/download-report")
async def download_report():

    global last_report

    pdf_path = "ValorAI_Report.pdf"

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph("ValorAI Coach Report", styles["Title"])
    )

    content.append(Spacer(1, 12))

    content.append(
        Paragraph(
            f"Date: {last_report.get('date', 'N/A')}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Screenshot: {last_report.get('filename', 'N/A')}",
            styles["Normal"]
        )
    )

    content.append(Spacer(1, 12))

    content.append(
        Paragraph(
            str(last_report.get("analysis", "No analysis available.")),
            styles["BodyText"]
        )
    )

    doc.build(content)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="ValorAI_Report.pdf"
    )
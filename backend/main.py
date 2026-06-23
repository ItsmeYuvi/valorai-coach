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


        # Prompt
        prompt = f"""
You are ValorAI Coach, an elite Valorant analyst and coach.

OCR Extracted Text:
{extracted_text}

TASK 1:
Determine whether this screenshot is related to Valorant.

Valid Valorant screenshots may contain:
- Match scoreboards
- Kills / Deaths / Assists (KDA)
- ACS (Average Combat Score)
- Headshot %
- Match results
- Agent names
- Combat reports
- Career history
- Tracker statistics
- Tournament broadcasts
- Professional match overlays
- RR gain/loss

If the screenshot is NOT related to Valorant, return ONLY:

{{
  "is_valorant": false,
  "reason": "Not a Valorant screenshot"
}}

--------------------------------------------------

TASK 2:

If it IS a Valorant screenshot, analyze ONLY the information visible in the OCR text.

Return ONLY valid JSON in this exact format:

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

--------------------------------------------------

SCORING RULES

Performance score:
1-3 = Poor
4-5 = Below Average
6-7 = Average
8-9 = Strong
10 = Exceptional

Confidence:
High
Medium
Low

Possible match types:
- Competitive
- Unrated
- Swiftplay
- Deathmatch
- Premier
- Professional Match
- Tournament Match

--------------------------------------------------

COACHING RULES

You are a professional Valorant coach.

Never leave any field empty.

Never return:
- None
- Unknown
- N/A
- Not detected
- No data

If information is limited:
- Infer likely strengths and weaknesses from available evidence.
- Mention uncertainty through a lower confidence score.
- Still provide useful coaching advice.

Do NOT invent statistics that are not visible.

However, you SHOULD provide evidence-based coaching observations.

--------------------------------------------------

STRENGTHS RULES

strengths must contain EXACTLY 3 meaningful observations.

Bad examples:
- Good player
- Nice performance
- Strong gameplay

Good examples:
- Positive KDA compared to teammates
- Consistent participation in rounds
- Strong impact during decisive rounds

--------------------------------------------------

WEAKNESSES RULES

weaknesses must contain EXACTLY 3 meaningful observations.

Never use:
- None detected
- No weaknesses
- Unknown

If data is limited, identify:
- Missing information
- Potential performance risks
- Areas requiring further review

Example:
[
  "Opening duel success rate cannot be verified.",
  "Utility efficiency is not visible from the screenshot.",
  "Headshot consistency cannot be evaluated from available data."
]

--------------------------------------------------

IMPROVEMENT PLAN RULES

improvement_plan must contain EXACTLY 3 actionable recommendations.

Bad examples:
- Play more
- Practice aim
- Get better

Good examples:
- Spend 15 minutes daily practicing crosshair placement.
- Review deaths occurring within the first 20 seconds of rounds.
- Focus on maintaining head-level crosshair positioning while clearing angles.

--------------------------------------------------

FOCUS AREA RULES

focus_area must ALWAYS contain exactly ONE primary improvement area.

Choose ONLY one:

- Aim
- Crosshair Placement
- Positioning
- Utility Usage
- Game Sense
- Communication
- Economy Management

Never leave focus_area empty.

--------------------------------------------------

AGENT RULES

If an agent can be identified, provide agent-specific coaching.

If an agent cannot be identified, provide general Valorant coaching advice.

Never leave agent_advice empty.

--------------------------------------------------

SUMMARY RULES

summary must be 2-3 sentences.

The summary should explain:
- Overall performance
- Key strengths
- Main area for improvement

--------------------------------------------------

OUTPUT RULES

Return ONLY valid JSON.
Do not use markdown.
Do not use code blocks.
Do not include explanations outside the JSON.
"""

        # AI Analysis
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

        # Parse JSON
        try:
            analysis = json.loads(raw_analysis)
        except Exception:
            analysis = {
                "error": "Failed to parse AI response",
                "raw_response": raw_analysis
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
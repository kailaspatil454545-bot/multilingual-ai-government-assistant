import os
import shutil
import tempfile
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Multilingual AI Assistant for Government Services",
    version="1.0.0"
)

# Setup frontend static assets
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
CSS_DIR = os.path.join(FRONTEND_DIR, "css")
JS_DIR = os.path.join(FRONTEND_DIR, "js")

if os.path.exists(CSS_DIR):
    app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
if os.path.exists(JS_DIR):
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")

# Enable CORS for local development and file:/// origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "Multilingual AI Government Assistant is running"
    }


@app.get("/api")
def api_info():
    return {
        "message": "Multilingual AI Government Assistant API is running",
        "endpoints": ["/health", "/services", "/query", "/transcribe", "/tts"]
    }


@app.get("/health")
def health():
    return {
        "status": "OK"
    }


@app.get("/services")
def services():
    return {
        "services": [
            "Aadhaar",
            "PAN Card",
            "Ration Card",
            "Driving Licence",
            "Income Certificate",
            "Caste Certificate",
            "Birth Certificate",
            "Scholarship",
            "Pension",
            "Government Schemes"
        ]
    }


class QueryRequest(BaseModel):
    question: str
    language: str


@app.post("/query")
def query(request: QueryRequest):
    question = request.question.lower().strip()
    language = request.language.strip()

    # Knowledge base for government services with multilingual keywords & answers
    if any(k in question for k in ["aadhaar", "aadhar", "adhaar", "adhar", "आधार", "uidai"]):
        answers = {
            "en": "Aadhaar is a 12-digit unique identity number issued by UIDAI. For Aadhaar enrollment, updates, or downloads, visit the official UIDAI portal at https://uidai.gov.in.",
            "hi": "आधार UIDAI द्वारा जारी किया गया 12 अंकों का विशिष्ट पहचान दस्तावेज है। आधार नामांकन, सुधार या डाउनलोड के लिए आधिकारिक UIDAI पोर्टल https://uidai.gov.in का उपयोग करें।",
            "mr": "आधार हे UIDAI द्वारे जारी केलेले 12 अंकी ओळखपत्र आहे. नवीन आधार नोंदणी, दुरुस्ती किंवा डाउनलोडसाठी अधिकृत UIDAI पोर्टल https://uidai.gov.in ला भेट द्या."
        }
    elif any(k in question for k in ["pan", "pancard", "पैन", "पॅन", "income tax"]):
        answers = {
            "en": "PAN (Permanent Account Number) is a 10-digit alphanumeric identifier issued by the Income Tax Department for financial and tax purposes. Apply online via NSDL or UTIITSL.",
            "hi": "PAN आयकर विभाग द्वारा जारी किया जाने वाला 10 अंकों का स्थायी खाता संख्या है जो वित्तीय कार्यों के लिए आवश्यक है। NSDL या UTIITSL पर आवेदन करें।",
            "mr": "PAN हा भारतातील कर आणि आर्थिक सेवांसाठी आयकर विभागामार्फत वापरला जाणारा 10 अंकी कायमस्वरूपी खाते क्रमांक आहे. NSDL किंवा UTIITSL पोर्टलवरून अर्ज करा."
        }
    elif any(k in question for k in ["income", "utpanna", "utpann", "उत्पन्न", "आय प्रमाण", "उत्पन्नाचा", "aay praman"]):
        answers = {
            "en": "An Income Certificate is an official document verifying an individual's or family's annual income. Issued by the Tehsildar/Revenue Department. Documents needed: Ration card, salary slip/ITR, and address proof.",
            "hi": "आय प्रमाण पत्र राजस्व विभाग/तहसीलदार द्वारा जारी किया जाता है जो वार्षिक आय का प्रमाण होता है। आवश्यक दस्तावेज: वेतन पर्ची/आईटीआर, राशन कार्ड और निवास प्रमाण पत्र।",
            "mr": "उत्पन्न प्रमाणपत्र हे महसूल विभाग/तहसीलदार कार्यालयाकडून दिले जाते जे कुटुंबाच्या वार्षिक उत्पन्नाचा पुरावा असतो. आवश्यक कागदपत्रे: रेशन कार्ड, पगार पावती किंवा प्रतिज्ञापत्र, आणि रहिवासी पुरावा."
        }
    elif any(k in question for k in ["ration", "rashan", "raashan", "रेशन", "राशन"]):
        answers = {
            "en": "Ration Card is issued by the Food & Civil Supplies Department for subsidized food grains. Categories include APL, BPL, and Antyodaya (AAY). Apply through your state civil supplies portal.",
            "hi": "राशन कार्ड खाद्य एवं रसद विभाग द्वारा रियायती खाद्यान्न के लिए जारी किया जाता है (APL, BPL, अंत्योदय)। राज्य के आपूर्ति पोर्टल से आवेदन करें।",
            "mr": "रेशन कार्ड हे अन्न व नागरी पुरवठा विभागामार्फत सवलतीच्या दरात अन्नधान्य मिळवण्यासाठी दिले जाते (APL, BPL, अंत्योदय). अधिक माहितीसाठी राज्य अन्न पुरवठा पोर्टलला भेट द्या."
        }
    elif any(k in question for k in ["caste", "cast", "जात", "जाति", "जातीचा", "jati"]):
        answers = {
            "en": "A Caste Certificate verifies that an individual belongs to a reserved category (SC/ST/OBC). Issued by SDO/Tehsildar. Documents needed: Leaving Certificate, Father's caste proof, and address proof.",
            "hi": "जाति प्रमाण पत्र यह प्रमाणित करता है कि व्यक्ति किसी विशेष आरक्षित श्रेणी (SC/ST/OBC) से संबंधित है। यह एसडीएम/तहसीलदार द्वारा जारी किया जाता है।",
            "mr": "जात प्रमाणपत्र हे व्यक्ती विशिष्ट मागास प्रवर्गातील (SC/ST/OBC/VJNT) असल्याचे प्रमाणित करते. यासाठी शाळा सोडल्याचा दाखला, वडिलांचा जातीचा पुरावा व रहिवासी दाखला लागतो."
        }
    elif any(k in question for k in ["driving", "licence", "license", "ड्रायव्हिंग", "ड्राइविंग", "लायसन्स", "लाइसेंस"]):
        answers = {
            "en": "A Driving Licence is issued by the RTO. First apply online for a Learner's Licence at https://parivahan.gov.in. After 30 days, you can book a driving test for a permanent licence.",
            "hi": "ड्राइविंग लाइसेंस क्षेत्रीय परिवहन कार्यालय (RTO) द्वारा जारी किया जाता है। पहले https://parivahan.gov.in पर लर्नर लाइसेंस के लिए आवेदन करें।",
            "mr": "ड्रायव्हिंग लायसन्स प्रादेशिक परिवहन कार्यालयाकडून (RTO) दिले जाते. प्रथम https://parivahan.gov.in वर लर्नर लायसन्ससाठी अर्ज करा, त्यानंतर पक्क्या लायसन्ससाठी चाचणी द्या."
        }
    elif any(k in question for k in ["birth", "janma", "janam", "जन्म", "दाखला"]):
        answers = {
            "en": "A Birth Certificate is registered and issued by the local Municipal Corporation or Gram Panchayat. It is mandatory to register a birth within 21 days of occurrence.",
            "hi": "जन्म प्रमाण पत्र स्थानीय नगर निगम या ग्राम पंचायत द्वारा जन्म के 21 दिनों के भीतर दर्ज कराने पर जारी किया जाता है।",
            "mr": "जन्म दाखला स्थानिक महानगरपालिका किंवा ग्रामपंचायतीमार्फत जन्माच्या 21 दिवसांच्या आत नोंदणी केल्यावर विनामूल्य दिला जातो."
        }
    elif any(k in question for k in ["pension", "पेन्शन", "पेंशन", "वृद्धापकाळ"]):
        answers = {
            "en": "Government pensions include Old Age Pension, Widow Pension, and Disability Pension under the National Social Assistance Programme (NSAP) and state schemes.",
            "hi": "सरकारी पेंशन योजनाओं में वृद्धावस्था पेंशन, विधवा पेंशन और दिव्यांग पेंशन शामिल हैं। आवेदन एनएसएपी पोर्टल या तहसील कार्यालय में करें।",
            "mr": "शासकीय पेन्शन योजनांमध्ये श्रावणबाळ योजना, संजय गांधी निराधार योजना आणि वृद्धापकाळ पेन्शन यांचा समावेश आहे. यासाठी तहसील कार्यालयात संपर्क साधा."
        }
    elif any(k in question for k in ["scholarship", "scholarships", "शिष्यवृत्ती", "छात्रवृत्ति", "mahadbt"]):
        answers = {
            "en": "Students can apply for government scholarships via the National Scholarship Portal (scholarships.gov.in) or state portals such as MahaDBT (mahadbt.maharashtra.gov.in).",
            "hi": "छात्र राष्ट्रीय छात्रवृत्ति पोर्टल (scholarships.gov.in) या राज्य पोर्टल (जैसे MahaDBT) के माध्यम से सरकारी छात्रवृत्ति के लिए आवेदन कर सकते हैं।",
            "mr": "विद्यार्थी महाडीबीटी (mahadbt.maharashtra.gov.in) किंवा राष्ट्रीय शिष्यवृत्ती पोर्टल (scholarships.gov.in) द्वारे शिष्यवृत्तीसाठी अर्ज करू शकतात."
        }
    elif any(k in question for k in ["scheme", "schemes", "योजना", "सरकारी"]):
        answers = {
            "en": "Major government schemes include PM-KISAN, Ayushman Bharat (health card), PM Awas Yojana (housing), and ladki bahin yojana. Inquire about any specific scheme for details.",
            "hi": "प्रमुख सरकारी योजनाओं में पीएम-किसान, आयुष्मान भारत (स्वास्थ्य कार्ड), पीएम आवास योजना और लाडली बहना योजना शामिल हैं। किसी विशिष्ट योजना की जानकारी के लिए पूछें।",
            "mr": "प्रमुख शासकीय योजनांमध्ये पीएम किसान, आयुष्मान भारत आरोग्य योजना, पीएम आवास योजना आणि लाडकी बहीण योजना यांचा समावेश आहे. विशिष्ट योजनेबद्दल विचारण्यासाठी नाव सांगा."
        }
    else:
        answers = {
            "en": "I can help you with information about Aadhaar, PAN Card, Ration Card, Income Certificate, Caste Certificate, Driving Licence, Birth Certificate, Scholarships, and Pensions. Please specify which service you want to know about.",
            "hi": "मैं आधार, पैन कार्ड, राशन कार्ड, आय प्रमाण पत्र, जाति प्रमाण पत्र, ड्राइविंग लाइसेंस, जन्म प्रमाण पत्र, छात्रवृत्ति और पेंशन से संबंधित जानकारी दे सकता हूँ। कृपया अपनी सेवा बताएं।",
            "mr": "मी आधार, पॅन कार्ड, रेशन कार्ड, उत्पन्न प्रमाणपत्र, जात प्रमाणपत्र, ड्रायव्हिंग लायसन्स, जन्म दाखला, शिष्यवृत्ती आणि पेन्शन या सेवांबद्दल माहिती देऊ शकतो. कृपया तुम्हाला कोणत्या सेवेबद्दल जाणून घ्यायचे आहे ते विचारा."
        }

    return {
        "question": request.question,
        "language": language,
        "answer": answers.get(language, answers["en"])
    }


# Lazy loaded Whisper model to prevent startup hangs and avoid high memory usage
_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )
    return _whisper_model


@app.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    lang: Optional[str] = Query(None)
):
    ext = os.path.splitext(audio.filename or "")[1] or ".webm"
    if ext.lower() not in [".wav", ".webm", ".ogg", ".mp3", ".m4a"]:
        ext = ".webm"
    temp_file = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            temp_file = tmp.name
            shutil.copyfileobj(audio.file, tmp)

        # Support Marathi, Hindi, English or auto-detection
        target_lang = (language or lang or "").strip().lower()
        whisper_lang = target_lang if target_lang in ["mr", "hi", "en"] else None

        whisper_model = get_whisper_model()
        segments, info = whisper_model.transcribe(
            temp_file,
            beam_size=5,
            language=whisper_lang,
            vad_filter=True
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        detected_lang = info.language if info else (whisper_lang or "unknown")

        return {
            "text": text,
            "language": detected_lang,
            "success": True
        }

    except Exception as e:
        return {
            "error": str(e),
            "text": "",
            "success": False
        }

    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass


VOICE_MAP = {
    "mr": "mr-IN-AarohiNeural",
    "hi": "hi-IN-SwaraNeural",
    "en": "en-IN-NeerjaNeural"
}


class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "en"


@app.api_route("/tts", methods=["GET", "POST"])
async def text_to_speech(
    request: Optional[TTSRequest] = None,
    text: Optional[str] = Query(None),
    language: Optional[str] = Query(None)
):
    try:
        import edge_tts
        t = (request.text if request and request.text else text) or ""
        l = (request.language if request and request.language else language) or "en"
        t = t.strip()
        l = l.strip().lower()

        if not t:
            return Response(content="Missing text", status_code=400)

        voice = VOICE_MAP.get(l, "en-IN-NeerjaNeural")
        communicate = edge_tts.Communicate(t, voice)
        audio_buffer = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.extend(chunk["data"])

        return Response(content=bytes(audio_buffer), media_type="audio/mpeg")
    except Exception as e:
        return Response(content=f"TTS error: {e}", status_code=500)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    import uvicorn

    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    # Ensure project root is in sys.path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    print("Starting Multilingual AI Government Assistant Backend on http://127.0.0.1:8000...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=str(project_root))
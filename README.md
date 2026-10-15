# Multilingual AI Assistant for Government Services

## Project

TY B.Sc. Data Science Project

## Description

A multilingual AI assistant that helps users find information about
selected government services using English, Hindi and Marathi.

## Current Version

Voice Assistant Integration - Complete Voice Interaction with Faster-Whisper Speech-to-Text & Neural Text-to-Speech.

## Features

- 🎙️ **Microphone Voice Recording**: Records speech directly in the browser via `MediaRecorder` API.
- ⚡ **Faster-Whisper STT**: High-accuracy local speech-to-text supporting Marathi, Hindi, and English.
- 🌐 **Multilingual Government Knowledge Base**: Information on Aadhaar, PAN Card, Ration Card, Income Certificate, Caste Certificate, Driving Licence, Birth Certificate, Pensions, and Government Schemes in Marathi, Hindi, and English.
- 🔊 **Text-to-Speech (TTS)**: Natural voice synthesis speaks answers aloud with a replay button (🔊).
- 📊 **Dynamic Status Bar**: Visual states for "Listening...", "Processing...", and "Response ready".
- ⌨️ **Dual Interaction**: Voice input with microphone button alongside traditional text input and Ask button.

## Technologies

- Python 3.12
- FastAPI & Uvicorn
- Faster-Whisper (CTranslate2)
- Edge-TTS / Web Speech Synthesis API
- HTML5, CSS3 & JavaScript (Vanilla)
- MediaRecorder API

## Running the Application

1. Run the backend:
   ```cmd
   start_backend.bat
   ```
   Or:
   ```cmd
   .\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Open your browser at:
   ```
   http://127.0.0.1:8000
   ```
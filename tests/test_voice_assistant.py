import asyncio
import edge_tts
import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

VOICE_MAP = {
    'mr': ('आधार कार्ड कसे काढायचे', 'mr-IN-AarohiNeural'),
    'hi': ('राशन कार्ड कैसे बनवाएं', 'hi-IN-SwaraNeural'),
    'en': ('How to get a driving licence', 'en-IN-NeerjaNeural')
}

async def run_stt_test():
    print("=================================================================")
    print("Testing Voice Assistant: Audio Generation -> Whisper STT -> Query -> TTS")
    print("=================================================================\n")

    for lang, (phrase, voice) in VOICE_MAP.items():
        print(f"--- Testing Language: {lang.upper()} ---")
        print(f"1. Synthesizing voice audio: '{phrase}' (Voice: {voice})")
        comm = edge_tts.Communicate(phrase, voice)
        chunks = []
        async for c in comm.stream():
            if c['type'] == 'audio':
                chunks.append(c['data'])
        audio_bytes = b''.join(chunks)
        print(f"   Generated audio: {len(audio_bytes)} bytes")

        # 2. Upload to /transcribe via multipart/form-data
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = bytearray()
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="audio"; filename="speech_{lang}.mp3"\r\n'.encode('utf-8'))
        body.extend(b'Content-Type: audio/mpeg\r\n\r\n')
        body.extend(audio_bytes)
        body.extend(b'\r\n')
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="language"\r\n\r\n'.encode('utf-8'))
        body.extend(f'{lang}\r\n'.encode('utf-8'))
        body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

        print("2. Uploading recorded audio to /transcribe endpoint...")
        req = urllib.request.Request(
            'http://127.0.0.1:8000/transcribe',
            data=bytes(body),
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
        )
        with urllib.request.urlopen(req) as resp:
            stt_res = json.loads(resp.read().decode('utf-8'))
            transcribed = stt_res.get('text', '')
            print(f"   Whisper STT Result: '{transcribed}'")
            print(f"   Detected/Specified Language: {stt_res.get('language')}")

        # 3. Query government assistant
        print("3. Querying /query API with transcribed text...")
        q_data = json.dumps({'question': transcribed, 'language': lang}).encode('utf-8')
        q_req = urllib.request.Request(
            'http://127.0.0.1:8000/query',
            data=q_data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(q_req) as q_resp:
            q_res = json.loads(q_resp.read().decode('utf-8'))
            answer = q_res.get('answer', '')
            print(f"   Government Service Answer:\n   \"{answer}\"")

        # 4. Test Text-to-Speech endpoint for this response
        print("4. Testing /tts endpoint for the answer...")
        tts_req = urllib.request.Request(
            'http://127.0.0.1:8000/tts',
            data=json.dumps({'text': answer, 'language': lang}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(tts_req) as tts_resp:
            tts_audio = tts_resp.read()
            print(f"   TTS Response Status: {tts_resp.status}, Audio bytes: {len(tts_audio)}")

        print(f"✓ Language {lang.upper()} passed successfully!\n")

    print("=================================================================")
    print("ALL TESTS PASSED: Microphone Audio -> Whisper STT -> Query -> TTS")
    print("=================================================================")

if __name__ == '__main__':
    asyncio.run(run_stt_test())

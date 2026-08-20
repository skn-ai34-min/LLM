# STT(음성 -> 텍스트) + GPT 응답 + TTS(텍스트 -> 음성) 파이프라인 함수
import base64
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
client = OpenAI()
#오디오 객체를 Whisper로 STT(Speech-To-Text)하는 함수
def stt(audio):
    """Speech->Text"""
    output_filepath = 'input.mp3'
    audio.export(output_filepath, format='mp3')
    with open(output_filepath, 'rb') as f:
        transcription = client.audio.transcriptions.create(
            model = 'whisper-1',
            file=f
        )
    os.remove(output_filepath) # 임시 mp3파일 삭제
    return transcription.text
# 메시지 히스토리를 받아서 GPT API로 응답을 생성해서 반환하는 함수
def ask_gpt(messages, model='gpt-5.6-luna'):
    """messages->GPT API->result"""
    return client.chat.completions.create(
            model = model,
            messages = messages,
            temperature=1,
            top_p=1,
            max_completion_tokens=4096
        ).choices[0].message.content

# 텍스트를 받아 TTS(Text-To-Speech)로 mp3 생성 후 base64 문자열로 반환하는 함수
# - base64 : json의 값으로써 멀티미디어 파일을 전송하고 싶은 경우 base64 인코딩 -> 확인하는 측에서는 base64 디코딩
def tts(response: str):
    """Text->Speech"""
    filename = 'output.mp3'
    with client.audio.speech.with_streaming_response.create(
        model= 'tts-1',
        voice= 'onyx',
        input= response
    ) as resp:
        resp.stream_to_file(filename)

    with open(filename, 'rb') as f:
        data = f.read()
        b64_encoded = base64.b64encode(data).decode()
    os.remove(filename) # 임시 mp3파일 삭제
    return b64_encoded

# ffmpeg 미설치시 업로드된 파일을 텍스트로 변환해 반환하는 함수
def stt_file(uploaded_file) -> str:
    """Speech->Text"""
    transcription = client.audio.transcriptions.create(
        model = 'whisper-1',
        # (파일명, 파일바이트) 튜플형식으로 업로드
        file=(uploaded_file.name, uploaded_file.getvalue())
    )
    return transcription.text
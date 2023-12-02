import os
from gtts import gTTS
import contextlib
import playsound
import sys
import pyaudio
import wave
import whisper
import subprocess


# ANSI escape codes for some colors
RED = "\033[31m"  # Red text
GREEN = "\033[32m"  # Green text
YELLOW = "\033[33m"  # Yellow text
BLUE = "\033[34m"  # Blue text
MAGENTA = "\033[35m"  # Magenta text
CYAN = "\033[36m"  # Cyan text
RESET = "\033[0m"  # Reset to default color

def record_voice(filename, record_seconds=5):
    # Setup the parameters for recording
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    audio = pyaudio.PyAudio()

    # Start recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []

    for i in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    # Stop and close the stream and audio
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded data as a WAV file
    with wave.open(filename, 'wb') as waveFile:
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))

def transcribe_voice(filename):
    model = whisper.load_model("base")
    result = model.transcribe(filename)
    return result["text"]

def play(assistant_text): 
    language = 'en'
    sound = gTTS(text=assistant_text, lang=language, slow=False)
    
    filename = "speak.mp3"
    sound.save(filename)
    os.system("play " + "speak.mp3"+" tempo 1.5")
    os.remove(filename)

def main():
    while 1:
        # Record the user's voice
        voice_filename = "user_voice.wav"
        record_voice(voice_filename)

        # Transcribe the recorded voice
        transcription = transcribe_voice(voice_filename)
        preprompt = "You are an assistant. Help answer my questions. My question is: "
        prompt = preprompt + transcription
        
        if len(transcription) == 0: 
            continue

        print(BLUE + "\nUser: " + RESET, transcription)


        if "exit" in transcription.lower() or "stop" in transcription.lower():
            break

        try:
            result = subprocess.run(["../llama.cpp/main", "-m", "../llama.cpp/models/openhermes-2.5-mistral-7b.Q8_0.gguf", "-p", prompt, "-n", "192", "-ngl", "128"], capture_output=True, text=True, check=True)
            print(CYAN + "Assistant: " + RESET + result.stdout.replace(prompt, '').strip())
            play(result.stdout.replace(prompt, '').strip())
        except subprocess.CalledProcessError as e:
            print("error")

if __name__ == "__main__": 
    main()


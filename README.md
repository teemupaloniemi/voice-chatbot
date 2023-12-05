# VOICE CHATBOT

## Overview 

This Python program allows users to interact using speech. It records the user's speech, transcribes it, and then provides both speech and text output based on the processed input. The program utilizes various libraries like gtts, pyaudio, whisper, and playsound for its functionality.

![](http://users.jyu.fi/~tealjapa/example/example.mp4)(Example Video)

## Requirements

 - Python 3.x
 - Libraries: gtts, pyaudio, whisper, playsound, subprocess, wave
 - Microphone for recording voice
 - Internet connection for text-to-speech (gTTS) translation
 - You need a language model and llama.cpp library

## Installation

1. install python3
2. install required libraries

## Usage

1. Running the Program: Execute the script using python3 conv.py or python3 conv.py 2>/dev/null if you want cleaner output (Note that this will omit also errors!).
2. Interacting with the Program: Speak into your microphone after the "Recording..." prompt appears. The program will transcribe your speech and provide an output.
3. Stopping the Program: Say "exit" or "stop" during your interaction to terminate the program.

## Licence

Check the License file. It's MIT.  

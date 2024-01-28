import requests
import json
from flask import Flask, render_template, request
import regex as re
app = Flask(__name__)

PRINT_CACHE = True
past_interaction = []
tmp_interaction = []


# ANSI escape codes for some colors
RED = "\033[31m"  # Red text
GREEN = "\033[32m"  # Green text
YELLOW = "\033[33m"  # Yellow text
BLUE = "\033[34m"  # Blue text
MAGENTA = "\033[35m"  # Magenta text
CYAN = "\033[36m"  # Cyan text
RESET = "\033[0m"  # Reset to default color

def generate(prompt):
    try: 
        url = 'http://localhost:8081/completion'  # Replace with the correct URL if needed
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({
            'prompt': prompt,
            'n_predict': 1024  # Adjust as needed
        })

        response = requests.post(url, headers=headers, data=data)
        print(RED + str(response.json()) + RESET)
        if response.status_code == 200:
            return response.json()['content'], response.json()['timings']
        else:
            return "Error: " + response.text
    except: 
        print(RED + "ERROR: " + RESET + "Start up the llama.cpp server with \"" + GREEN + "./server -m models/YOUR_MODEL -ngl 100" + RESET + "\" in the llama.cpp folder!")

def tokenize(transcription, past_interaction): 
        system = "<|im_start|>system\nYou are an assistant called Lexie. You are a superintelligent system developed to help users and answer their questions. Give a short answer, please. You, Lexie, are really smart and answers in clear fashion but accurately<|im_end|>"
        for item in past_interaction: 
            system += item['user'] + item['assistant']
        user = "<|im_start|>user\n" + transcription + "<|im_end|>"
        assistant = "<|im_start|>assistant\n"
        prompt = system + user + assistant
        return prompt, user, assistant


@app.route("/", methods=["GET", "POST"])
def index():
    global past_interaction, tmp_interaction

    if request.method == "POST":
        transcription = request.form["transcription"]
        past_user = ""
        past_assistant = ""

        prompt, user, assistant = tokenize(transcription, past_interaction)
        response, timings = generate(prompt)

        past_user = user
        past_assistant = assistant + response.strip()

        cache_length = 6
        if len(past_interaction) > cache_length:
            past_interaction.pop(0)

        past_interaction.append({'user': past_user, 'assistant': past_assistant})
        
        if len(tmp_interaction) > cache_length:
            tmp_interaction.pop(0)

        tmp_user = past_user.replace("<|im_start|>user", "")
        tmp_user = tmp_user.replace("<|im_end|>", "")
        tmp_assistant = past_assistant.replace("<|im_start|>assistant", "")
        tmp_assistant = tmp_assistant.replace("<|im_end|>", "")
        code_blocks = re.findall(r'```(?!html\s)(.*?)```', tmp_assistant, re.DOTALL)
        is_code = bool(code_blocks)
        assistantstart = tmp_assistant
        assistantend = ""
        if len(code_blocks) > 0:
            for stuff in code_blocks: 
                tmp_assistant = tmp_assistant.replace("```"+stuff+"```","[splithere]")
            
            s = tmp_assistant.split("[splithere]")
            if len(s) == 2:
                assistantstart = s[0]
                assistantend = s[1]
        tmp_interaction.append({'user': tmp_user, 'assistantstart': assistantstart, 'assistantend': assistantend, 'is_code': is_code, 'code_blocks': code_blocks})
    
        if PRINT_CACHE:
            print_memory_window()

        return render_template("index.html", past_interaction=tmp_interaction, timings=timings)

    return render_template("index.html", past_interaction=past_interaction)

def print_memory_window():
    print("-" * 16 + "MEMORY WINDOW START" + "-" * 16)
    for i, line in enumerate(past_interaction):
        print(f"Q:{i}")
        print("Cache user:", line['user'])
        print("Cache assistant:", line['assistant'])
    print("-" * 16 + "MEMORY WINDOW END" + "-" * 16)


if __name__ == "__main__":
    app.run(debug=True)

import os
import subprocess
import datetime
import pywhatkit
import webbrowser
import pyttsx3
import openai
import sounddevice as sd
import speech_recognition as sr
import smtplib
import tkinter as tk
from threading import Thread
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API setup
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
recognizer = sr.Recognizer()

# UI Variables
listening = False
app_running = True
ui_instance = None

def create_ui():
    global canvas, root, ui_instance
    ui_instance = tk.Tk()
    ui_instance.title("Assistant UI")
    ui_instance.geometry("400x400")
    ui_instance.configure(bg="black")

    canvas = tk.Canvas(ui_instance, width=400, height=400, bg="black", highlightthickness=0)
    canvas.pack()

    circle = canvas.create_oval(150, 150, 250, 250, outline="cyan", width=4)
    animate_circle(circle)

    ui_instance.protocol("WM_DELETE_WINDOW", on_close)
    ui_instance.mainloop()

def on_close():
    global app_running
    app_running = False
    if ui_instance:
        ui_instance.destroy()

def animate_circle(circle):
    if listening and app_running:
        for color in ["cyan", "blue", "purple"]:
            canvas.itemconfig(circle, outline=color)
            canvas.update()
            canvas.after(300)
    if app_running:
        ui_instance.after(100, lambda: animate_circle(circle))

def listen_for_command(duration=5, samplerate=44100):
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    audio = sr.AudioData(audio_data.tobytes(), samplerate, 2)
    try:
        text = recognizer.recognize_google(audio, language='en_US')
        print("Heard:", text.lower())
        return text.lower()
    except Exception as ex:
        print("Error:", ex)
        return ""

def get_openai_response(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            max_tokens=100
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.error.RateLimitError:
        return "Sorry, the service is currently unavailable due to usage limits."
    except openai.error.APIError as e:
        return f"An API error occurred: {str(e)}"
    except Exception as e:
        return f"Sorry, I couldn't understand your question. Error: {e}"

def send_email(subject, body, to_email="recipient@example.com"):
    my_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    if not my_email or not password:
        print("Email credentials not found in environment variables.")
        return
    connection = smtplib.SMTP("smtp.gmail.com", 587)
    connection.starttls()
    connection.login(user=my_email, password=password)
    connection.sendmail(from_addr=my_email, to_addrs=to_email, msg=f"Subject:{subject}\n\n{body}")
    connection.close()

def search_and_open_file():
    desktop_path = r"C:\Users\prane\OneDrive\Desktop"
    engine.say("What is the name of the file or folder you're looking for?")
    engine.runAndWait()
    search_name = listen_for_command()
    found = False
    for root, dirs, files in os.walk(desktop_path):
        if search_name.lower() in files:
            file_path = os.path.join(root, search_name)
            engine.say(f"File {search_name} found. Do you want to open it?")
            engine.runAndWait()
            response = listen_for_command()
            if 'yes' in response:
                engine.say(f"Opening {search_name}.")
                engine.runAndWait()
                os.startfile(file_path)
                found = True
                break
            elif 'no' in response or not response:
                engine.say("Not opening the file.")
                engine.runAndWait()
                found = True
                break
        elif search_name.lower() in dirs:
            folder_path = os.path.join(root, search_name)
            engine.say(f"Folder {search_name} found. Do you want to open it?")
            engine.runAndWait()
            response = listen_for_command()
            if 'yes' in response:
                engine.say(f"Opening {search_name}.")
                engine.runAndWait()
                subprocess.Popen(['explorer', folder_path])
                found = True
                break
            elif 'no' in response or not response:
                engine.say("Not opening the folder.")
                engine.runAndWait()
                found = True
                break
    if not found:
        engine.say(f"Could not find any file or folder named {search_name}.")
        engine.runAndWait()

def cmd():
    global listening
    listening = False
    while app_running:
        print("Recording and waiting for command...")
        text = listen_for_command()
        if "hey assistant" in text and not listening:
            engine.say("Yes, how can I help you?")
            engine.runAndWait()
            listening = True
            ui_thread = Thread(target=create_ui)
            ui_thread.start()
        elif listening:
            if 'exit' in text:
                engine.say("Goodbye!")
                engine.runAndWait()
                print("Exiting...")
                if ui_instance:
                    ui_instance.quit()
                break
            elif 'send email' in text:
                engine.say("What is the subject of the email?")
                engine.runAndWait()
                subject = listen_for_command()
                engine.say("What is the body of the email?")
                engine.runAndWait()
                body = listen_for_command()
                send_email(subject, body)
                engine.say("Email sent successfully.")
                engine.runAndWait()
            elif 'google' in text:
                search_query = text.split("google")[-1].strip()
                if search_query:
                    engine.say(f"Googling {search_query}.")
                    engine.runAndWait()
                    webbrowser.open(f'https://www.google.com/search?q={search_query}')
            elif 'play music' in text or 'playmusic' in text:
                song_name = text.split('play music')[-1].strip()
                if song_name:
                    engine.say(f"Playing {song_name} on YouTube.")
                    engine.runAndWait()
                    pywhatkit.playonyt(song_name)
            elif 'open chrome' in text:
                engine.say("Opening Chrome.")
                engine.runAndWait()
                program_name = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                subprocess.Popen([program_name])
            elif 'time' in text:
                current_time = datetime.datetime.now().strftime('%I:%M %p')
                engine.say(f"The time is {current_time}.")
                engine.runAndWait()
            elif 'play' in text:
                engine.say("Opening YouTube to play your request.")
                engine.runAndWait()
                pywhatkit.playonyt(text)
            elif 'youtube' in text:
                engine.say("Opening YouTube.")
                engine.runAndWait()
                webbrowser.open('https://www.youtube.com')
            elif 'open file explorer' in text:
                engine.say("Opening File Explorer.")
                engine.runAndWait()
                subprocess.Popen('explorer')
            elif 'search file' in text:
                search_and_open_file()
            elif 'open microsoft store' in text:
                engine.say("Opening Microsoft Store.")
                engine.runAndWait()
                subprocess.Popen(['start', 'ms-windows-store:'], shell=True)
            else:
                response = get_openai_response(text)
                engine.say(response)
                engine.runAndWait()

if __name__ == "__main__":
    cmd()

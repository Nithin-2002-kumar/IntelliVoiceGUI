import logging
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk
import webbrowser
import os
import pyautogui
import wikipedia
import pyttsx3
import spacy
import speech_recognition as sr

# Configure logging
logging.basicConfig(
    filename="assistant.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class IntelliVoiceGUI:
    def __init__(self, master):
        self.command_entry = None
        self.text_area = None
        self.listen_btn = None
        self.master = master
        master.title("IntelliVoice Assistant")
        master.geometry("800x600")

        # Initialize text-to-speech engine
        self.engine = self._init_tts_engine()

        # Context variables
        self.current_context = None
        self.action_history = []
        self.redo_stack = []
        self.user_preferences = {
            'name': 'User',
            'speech_rate': 150,
            'preferred_language': 'en',
            'spaCy_model': 'en_core_web_sm'
        }
        try:
            self.nlp = spacy.load(self.user_preferences['spaCy_model'])
        except OSError:
            logging.error("spaCy model not found. Please install it.")
            self.nlp = None

        self.expecting_name = True  # For initial setup
        self.listening = False  # Flag to track listening state

        # Create GUI widgets
        self.create_widgets()

        # Initial setup
        self.assistant_speaks("What is your name?")
        threading.Thread(target=self.listen_for_name, daemon=True).start()

    def _init_tts_engine(self):
        """Initialize and configure the text-to-speech engine."""
        try:
            engine = pyttsx3.init('sapi5')
            engine.setProperty("rate", 150)
            engine.setProperty("volume", 0.9)
            return engine
        except Exception as e:
            logging.error聅

    @staticmethod
    def log_action(action, status="INFO"):
        if status == "ERROR":
            logging.error(action)
        else:
            logging.info(action)

    def create_widgets(self):
        """Create and arrange all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.master)
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        # Text area for conversation
        self.text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state='disabled')
        self.text_area.pack(expand=True, fill='both')
        self.text_area.tag_config('user', foreground='blue')
        self.text_area.tag_config('assistant', foreground='green')
        self.text_area.tag_config('error', foreground='red')

        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill='x', pady=(5, 0))

        # Command entry
        self.command_entry = ttk.Entry(input_frame)
        self.command_entry.pack(side='left', expand=True, fill='x', padx=(0, 5))
        self.command_entry.bind("<Return>", self.process_text_command)

        # Buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side='left')

        self.listen_btn = ttk.Button(btn_frame, text="🎤 Listen", command=self.toggle_listening)
        self.listen_btn.pack(side='left', padx=(0, 5))

        ttk.Button(btn_frame, text="⚙️ Settings", command=self.show_settings).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="❌ Exit", command=self.master.quit).pack(side='left')

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_bar.pack(fill='x')

    def toggle_listening(self):
        """Toggle listening state."""
        if not self.listening:
            self.listening = True
            self.listen_btn.config(text="🔴 Listening...")
            self.status_var.set("Listening...")
            threading.Thread(target=self.listen_and_process, daemon=True).start()
        else:
            self.listening = False
            self.listen_btn.config(text="🎤 Listen")
            self.status_var.set("Ready")

    def show_settings(self):
        """Show settings dialog."""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Settings")

        ttk.Label(settings_window, text="Assistant Settings").pack(pady=10)

        # Add your settings controls here
        ttk.Button(settings_window, text="Close", command=settings_window.destroy).pack(pady=10)

    def assistant_speaks(self, text):
        """Display assistant's text in the GUI and speak it."""
        if not text:
            return

        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"Assistant: {text}\n", 'assistant')
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)

        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logging.error(f"Error in text-to-speech: {e}")
                self.text_area.configure(state='normal')
                self.text_area.insert(tk.END, f"Error: Could not speak text\n", 'error')
                self.text_area.configure(state='disabled')

    def user_says(self, text):
        """Display user's text in the GUI."""
        if not text:
            return

        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"You: {text}\n", 'user')
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)

    def process_text_command(self, event=None):
        command = self.command_entry.get()
        self.command_entry.delete(0, tk.END)
        if command:
            self.user_says(command)
            self.execute_command(command)

    def start_listening(self):
        """Start listening for voice commands."""
        if not self.listening:
            self.listening = True
            self.listen_btn.config(text="🔴 Listening...")
            threading.Thread(target=self.listen_and_process, daemon=True).start()

    def listen_for_name(self):
        """Special listening mode for initial name setup."""
        command = self.listen()
        if command:
            self.user_preferences['name'] = command
            self.master.after(0, self.assistant_speaks, f"Hello {command}! How can I help you today?")
            self.expecting_name = False

    def listen_and_process(self):
        """Listen for commands and process them."""
        command = self.listen()
        if command:
            self.master.after(0, self.user_says, command)
            self.master.after(0, self.execute_command, command)
        self.listening = False
        self.master.after(0, lambda: self.listen_btn.config(text="🎤 Listen"))

    def listen(self):
        """Listen to microphone and return recognized text."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.master.after(0, self.assistant_speaks, "Listening...")
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source, timeout=5)
            except sr.WaitTimeoutError:
                return None

        try:
            return recognizer.recognize_google(audio, language='en').lower()
        except sr.UnknownValueError:
            self.master.after(0, self.assistant_speaks, "I didn't catch that. Could you please repeat?")
            return None
        except sr.RequestError as e:
            self.master.after(0, self.assistant_speaks, f"Could not request results; check your internet connection.")
            logging.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in listen(): {e}")
            return None

    def process_command(self, command):
        command = command.lower()
        intents = []
        intent_keywords = {
            "open browser": "open_browser",
            "open notepad": "open_notepad",
            "open file explorer": "open_file_explorer",
            "search wikipedia": "search_wikipedia",
            "open calculator": "open_calculator",
            "time": "time",
            "screenshot": "screenshot",
            "shutdown": "shutdown",
            "create a file": "create_a_file",
            "move mouse": "move_mouse",
            "click": "click",
            "scroll": "scroll",
            "type": "type",
            "exit": "exit_program",
            "delete": "delete",
            "language": "language",
            "open application": "open application",
            "close application": "close application",
            "open website": "open website",
            "close website": "close website",
            "search online": "search",
            "list files": "list_files",
            "copy file": "copy_file",
            "move file": "move_file",
            "rename file": "rename_file",
            "create folder": "create_folder",
            "delete folder": "delete_folder",
            "open task manager": "open_task_manager",
            "restart": "restart",
            "lock computer": "lock_computer",
            "open settings": "open_settings",
            "minimize": "minimize",
            "maximize": "maximize",
            "restore": "restore",
            "switch application": "switch_application",
        }
        for keyword, intent in intent_keywords.items():
            if keyword in command:
                intents.append(intent)
                break
        return intents

    def execute_command(self, command):
        if self.expecting_name:
            self.user_preferences['name'] = command
            self.assistant_speaks(f"Hello {command}! How can I help you today?")
            self.expecting_name = False
            self.log_action(f"Executed command: {command}")
            return

        intents = self.process_command(command)
        for intent in intents:
            try:
                if intent == "open_browser":
                    self.assistant_speaks("Opening browser...")
                    subprocess.run(["start", "chrome"], shell=True)
                elif intent == "open_file_explorer":
                    self.assistant_speaks("Opening File Explorer...")
                    subprocess.run(["explorer"], shell=True)
                elif intent == "time":
                    current_time = datetime.now().strftime("%H:%M:%S")
                    self.assistant_speaks(f"The time is {current_time}")
                elif intent == "search":
                    self.assistant_speaks("What do you want to search for online?")
                    query = self.listen()
                    if query:
                        webbrowser.open(f"https://www.google.com/search?q={query}")
                        self.assistant_speaks(f"Searching for {query} online.")
                    else:
                        self.assistant_speaks("I didn't catch that. Please say the search term again.")
                elif intent == 'open notepad':
                    os.system('notepad')
                    self.assistant_speaks(f"Opening Notepad, {self.user_preferences['name']}")
                elif intent == 'search wikipedia':
                    self.assistant_speaks(f"What do you want to search for, {self.user_preferences['name']}?")
                    query = self.listen()
                    if query:
                        result = wikipedia.summary(query, sentences=2)
                        self.assistant_speaks(f"According to Wikipedia: {result}")
                elif intent == 'open calculator':
                    os.system('calc')
                    self.assistant_speaks(f"Opening Calculator, {self.user_preferences['name']}")
                elif intent == "open application":
                    self.assistant_speaks("What application do you want to open?")
                    app_name = self.listen()
                    if app_name:
                        try:
                            subprocess.Popen(app_name)
                            self.assistant_speaks(f"Opening {app_name}, {self.user_preferences['name']}.")
                        except Exception as e:
                            self.assistant_speaks(f"Could not open {app_name}. Please check the application name.")
                            logging.error(f"Error opening application: {e}")
                elif intent == "close application":
                    self.assistant_speaks("What application do you want to close?")
                    app_name = self.listen()
                    if app_name:
                        try:
                            os.system(f"taskkill /im {app_name}.exe")
                            self.assistant_speaks(f"Closing {app_name}, {self.user_preferences['name']}.")
                        except Exception as e:
                            self.assistant_speaks(f"Could not close {app_name}. Please check the application name.")
                            logging.error(f"Error closing application: {e}")
                elif intent == "open website":
                    self.assistant_speaks("What website do you want to open?")
                    website = self.listen()
                    if website:
                        webbrowser.open(f"https://{website}")
                        self.assistant_speaks(f"Opening {website}, {self.user_preferences['name']}.")
                    else:
                        self.assistant_speaks("I didn't catch that. Please say the website name again.")
                elif intent == "close website":
                    self.assistant_speaks("Closing the browser is not supported directly. Please close it manually.")
                elif intent == 'screenshot':
                    screenshot = pyautogui.screenshot()
                    screenshot.save('screenshot.png')
                    self.assistant_speaks(f"Screenshot taken and saved, {self.user_preferences['name']}")
                elif intent == "shutdown":
                    self.assistant_speaks(f"Are you sure you want to shut down, {self.user_preferences['name']}?")
                    confirmation = self.listen()
                    if "yes" in confirmation:
                        self.assistant_speaks(f"Shutting down the computer, {self.user_preferences['name']}")
                        subprocess.run(['shutdown', "/s", "/t", "0"], shell=True)
                    else:
                        self.assistant_speaks(f"Shutdown cancelled, {self.user_preferences['name']}")
                elif intent == "restart":
                    self.assistant_speaks(f"Are you sure you want to restart, {self.user_preferences['name']}?")
                    confirmation = self.listen()
                    if "yes" in confirmation:
                        self.assistant_speaks(f"Restarting the computer, {self.user_preferences['name']}")
                        subprocess.run(['shutdown', "/r", "/t", "0"], shell=True)
                    else:
                        self.assistant_speaks(f"Restart cancelled, {self.user_preferences['name']}")
                elif intent == "lock_computer":
                    self.assistant_speaks(f"Locking the computer, {self.user_preferences['name']}.")
                    subprocess.run("rundll32.exe user32.dll,LockWorkStation")
                elif intent == "open settings":
                    self.assistant_speaks(f"Opening Windows Settings, {self.user_preferences['name']}.")
                    subprocess.run("start ms-settings:", shell=True)
                elif intent == "delete":
                    self.assistant_speaks("What file do you want to delete?")
                    file_name = self.listen()
                    if file_name:
                        file_path = os.path.join(os.getcwd(), file_name)
                        if os.path.exists(file_path):
                            self.assistant_speaks(f"Are you sure you want to delete {file_name}? Say 'yes' to confirm.")
                            confirmation = self.listen()
                            if "yes" in confirmation:
                                os.remove(file_path)
                                self.assistant_speaks(f"{file_name} has been deleted.")
                            else:
                                self.assistant_speaks("File deletion canceled.")
                        else:
                            self.assistant_speaks("File not found. Please check the name and try again.")
                elif intent == "create a file":
                    self.assistant_speaks("What should be the name of the file?")
                    filename = self.listen()
                    if filename:
                        filepath = os.path.join(os.getcwd(), f"{filename}.txt")
                        with open(filepath, "w") as file:
                            file.write("This is a new file created by your voice assistant.")
                        self.assistant_speaks(
                            f"File {filename}.txt has been created in the current directory, {self.user_preferences['name']}")
                    else:
                        self.assistant_speaks(f"File creation cancelled, {self.user_preferences['name']}")
                elif intent == "move mouse":
                    self.assistant_speaks(
                        f"Where do you want to move the mouse, {self.user_preferences['name']}? Please tell the coordinates.")
                    position = self.listen()
                    if position:
                        try:
                            x, y = map(int, position.split())
                            pyautogui.moveTo(x, y)
                            self.assistant_speaks(f"Mouse moved to position ({x}, {y})")
                        except ValueError:
                            self.assistant_speaks("Sorry, I couldn't understand the position.")
                elif intent == "click":
                    pyautogui.click()
                    self.assistant_speaks(f"Mouse clicked, {self.user_preferences['name']}.")
                elif intent == "scroll":
                    if intent == "up":
                        pyautogui.scroll(10)
                        self.assistant_speaks(f"Scrolling up, {self.user_preferences['name']}.")
                    elif intent == "down":
                        pyautogui.scroll(-10)
                        self.assistant_speaks(f"Scrolling down, {self.user_preferences['name']}.")
                elif intent == "type":
                    self.assistant_speaks(f"What would you like to type, {self.user_preferences['name']}?")
                    text_to_type = self.listen()
                    if text_to_type:
                        pyautogui.write(text_to_type)
                        self.assistant_speaks(f"Typed: {text_to_type}")
                elif intent == "list files":
                    self.assistant_speaks("What directory do you want to list files from?")
                    directory = self.listen()
                    if directory:
                        try:
                            files = os.listdir(directory)
                            if files:
                                self.assistant_speaks(f"The files in {directory} are: {', '.join(files)}")
                            else:
                                self.assistant_speaks(f"There are no files in {directory}.")
                        except Exception as e:
                            self.assistant_speaks(f"Could not access {directory}. Please check the directory name.")
                elif intent == "copy file":
                    self.assistant_speaks("What file do you want to copy?")
                    file_name = self.listen()
                    if file_name:
                        source_path = os.path.join(os.getcwd(), file_name)
                        if os.path.exists(source_path):
                            self.assistant_speaks("Where do you want to copy the file?")
                            destination = self.listen()
                            if destination:
                                try:
                                    destination_path = os.path.join(destination, file_name)
                                    os.system(f'copy "{source_path}" "{destination_path}"')
                                    self.assistant_speaks(f"{file_name} has been copied to {destination}.")
                                except Exception as e:
                                    self.assistant_speaks(f"Could not copy the file. Please check the destination.")
                        else:
                            self.assistant_speaks("File not found. Please check the name and try again.")
                elif intent == "move file":
                    self.assistant_speaks("What file do you want to move?")
                    file_name = self.listen()
                    if file_name:
                        source_path = os.path.join(os.getcwd(), file_name)
                        if os.path.exists(source_path):
                            self.assistant_speaks("Where do you want to move the file?")
                            destination = self.listen()
                            if destination:
                                try:
                                    destination_path = os.path.join(destination, file_name)
                                    os.rename(source_path, destination_path)
                                    self.assistant_speaks(f"{file_name} has been moved to {destination}.")
                                except Exception as e:
                                    self.assistant_speaks(f"Could not move the file. Please check the destination.")
                        else:
                            self.assistant_speaks("File not found. Please check the name and try again.")
                elif intent == "rename file":
                    self.assistant_speaks("What file do you want to rename?")
                    old_name = self.listen()
                    if old_name:
                        old_path = os.path.join(os.getcwd(), old_name)
                        if os.path.exists(old_path):
                            self.assistant_speaks("What should be the new name?")
                            new_name = self.listen()
                            if new_name:
                                new_path = os.path.join(os.getcwd(), new_name)
                                os.rename(old_path, new_path)
                                self.assistant_speaks(f"{old_name} has been renamed to {new_name}.")
                            else:
                                self.assistant_speaks("File renaming canceled.")
                        else:
                            self.assistant_speaks("File not found. Please check the name and try again.")
                elif intent == "create folder":
                    self.assistant_speaks("What should be the name of the folder?")
                    folder_name = self.listen()
                    if folder_name:
                        try:
                            os.makedirs(folder_name)
                            self.assistant_speaks(f"Folder {folder_name} has been created.")
                        except Exception as e:
                            self.assistant_speaks(f"Could not create the folder. Please check the name.")
                elif intent == "delete folder":
                    self.assistant_speaks("What folder do you want to delete?")
                    folder_name = self.listen()
                    if folder_name:
                        folder_path = os.path.join(os.getcwd(), folder_name)
                        if os.path.exists(folder_path):
                            self.assistant_speaks(f"Are you sure you want to delete the folder {folder_name}? Say 'yes' to confirm.")
                            confirmation = self.listen()
                            if "yes" in confirmation:
                                os.rmdir(folder_path)
                                self.assistant_speaks(f"Folder {folder_name} has been deleted.")
                            else:
                                self.assistant_speaks("Folder deletion canceled.")
                        else:
                            self.assistant_speaks("Folder not found. Please check the name and try again.")
                elif intent == "exit_program":
                    self.assistant_speaks("Goodbye!")
                    self.master.quit()
                else:
                    self.assistant_speaks("I didn't understand that command. Please try again.")

            except Exception as e:
                error_msg = f"Error executing command: {str(e)}"
                self.assistant_speaks("Something went wrong with that command.")
                logging.error(error_msg)

    def handle_follow_up(self, action):
        """Handle follow-up actions after command execution."""
        self.action_history.append(action)
        self.assistant_speaks(
            f"Did I perform the {action} correctly? You can say 'yes', 'no', 'modify', 'undo', 'redo', or 'cancel'.")

        follow_up_command = self.listen()
        if follow_up_command:
            if 'yes' in follow_up_command:
                self.assistant_speaks("Great!")
                self.redo_stack.clear()
            elif 'no' in follow_up_command:
                self.assistant_speaks("Okay, let's undo or modify that.")
                self.handle_modification(action)
            elif 'modify' in follow_up_command:
                self.assistant_speaks("How would you like to modify it?")
                new_action = self.listen()
                if new_action:
                    self.execute_command(new_action)
            elif 'undo' in follow_up_command:
                self.undo_last_action()
            elif 'redo' in follow_up_command:
                self.redo_last_action()
            elif 'cancel' in follow_up_command:
                self.assistant_speaks("Action cancelled.")
            else:
                self.assistant_speaks("Sorry, I didn't understand that.")

    def undo_last_action(self):
        """Undo the last action."""
        if self.action_history:
            last_action = self.action_history.pop()
            self.redo_stack.append(last_action)
            self.assistant_speaks(f"Undoing: {last_action}")
        else:
            self.assistant_speaks("Nothing to undo.")

    def redo_last_action(self):
        """Redo the last undone action."""
        if self.redo_stack:
            action = self.redo_stack.pop()
            self.action_history.append(action)
            self.assistant_speaks(f"Redoing: {action}")
            self.execute_command(action)
        else:
            self.assistant_speaks("Nothing to redo.")

if __name__ == "__main__":
    root = tk.Tk()
    try:
        gui = IntelliVoiceGUI(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Application error: {e}")
        raise

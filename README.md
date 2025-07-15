# IntelliVoice Assistant

IntelliVoice is a voice-activated desktop assistant built with Python, featuring a graphical user interface (GUI) using Tkinter. It supports voice and text commands to perform tasks such as opening applications, searching Wikipedia, taking screenshots, managing files, and controlling system functions like shutdown or restart. The assistant uses speech recognition and text-to-speech capabilities to interact with users naturally.

## Features

- **Voice and Text Input**: Accepts commands via microphone or text entry.
- **System Control**: Open applications (e.g., Notepad, Calculator), File Explorer, or web browsers.
- **Web Interaction**: Search Google or Wikipedia, open websites.
- **File Management**: Create, delete, copy, move, or rename files and folders.
- **System Actions**: Take screenshots, check time, shut down, restart, or lock the computer.
- **Mouse and Keyboard Control**: Move the mouse, click, scroll, or type text.
- **Action History**: Supports undo/redo for certain commands.
- **Logging**: Records actions and errors in `assistant.log` for debugging.

## Prerequisites

- **Operating System**: Windows (due to `sapi5` TTS and commands like `taskkill`).
- **Python**: Version 3.6 or higher.
- **Hardware**: Microphone for voice input.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd intellivoice

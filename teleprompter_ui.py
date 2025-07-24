import tkinter as tk
from tkinter import font
import requests
import json
import threading
import sys
from pynput import keyboard
import psutil

# --- Configuration ---
API_URL = "http://127.0.0.1:5000/query"
MOVE_AMOUNT = 15  # Pixels to move window with arrow keys

class TeleprompterApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()

        # --- Window Creation and Styling ---
        self.prompter_window = tk.Toplevel(root)
        self.prompter_window.title("NotebookLM Teleprompter")
        self.prompter_window.geometry("900x200+100+50")
        
        # Core Attributes for Overlay Behavior
        self.prompter_window.overrideredirect(True) # Frameless
        self.prompter_window.wm_attributes("-topmost", True) # Always on top
        self.prompter_window.config(bg="#282c34")

        # --- Invisibility and Platform-Specific Tweaks ---
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.prompter_window.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20) # GWL_EXSTYLE
                style = style | 0x00000080  # WS_EX_TOOLWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
            except Exception as e:
                print(f"Could not set window style for invisibility: {e}")

        # --- Opacity and Font/Zoom Control ---
        self.opacity = 0.8
        self.prompter_window.attributes("-alpha", self.opacity)
        self.font_size = 14
        # self.update_font() # <-- MOVED FROM HERE

        # --- Main Widgets ---
        self.response_text = tk.StringVar()
        self.response_text.set("Welcome! Type a question and press Ctrl+Enter.")
        
        # This label must be created BEFORE update_font() is called.
        self.response_label = tk.Label(
            self.prompter_window, textvariable=self.response_text, fg="#abb2bf",
            bg="#282c34", wraplength=880, justify="left", anchor="nw"
        )
        self.response_label.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.update_font() # <-- TO HERE. Now it's safe to call.

        self.input_entry = tk.Entry(
            self.prompter_window, font=("Segoe UI", 12), bg="#21252b", fg="#abb2bf",
            insertbackground="white", bd=0, highlightthickness=1,
            highlightbackground="#61afef", highlightcolor="#61afef"
        )
        self.input_entry.pack(padx=10, pady=(0, 10), fill="x")
        self.input_entry.focus_set()

        # --- Window Interaction Handlers ---
        self._offset_x = 0
        self._offset_y = 0
        self.prompter_window.bind("<ButtonPress-1>", self.start_move)
        self.prompter_window.bind("<ButtonRelease-1>", self.stop_move)
        self.prompter_window.bind("<B1-Motion>", self.do_move)
        
        # --- Resize Handle ---
        self.resize_handle = tk.Frame(self.prompter_window, bg="#61afef", cursor="sizing")
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se", width=10, height=10)
        self.resize_handle.bind("<B1-Motion>", self.do_resize)


    def update_font(self):
        """Applies the current font size to the response label."""
        new_font = font.Font(family="Segoe UI", size=self.font_size)
        self.response_label.config(font=new_font)

    # --- Window Management Methods (Called by Hotkeys) ---
    def start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def stop_move(self, event):
        self._offset_x = 0
        self._offset_y = 0

    def do_move(self, event):
        x = self.prompter_window.winfo_x() + event.x - self._offset_x
        y = self.prompter_window.winfo_y() + event.y - self._offset_y
        self.prompter_window.geometry(f"+{x}+{y}")
        
    def do_resize(self, event):
        width = self.prompter_window.winfo_width() + event.x
        height = self.prompter_window.winfo_height() + event.y
        self.prompter_window.geometry(f"{width}x{height}")
        self.response_label.config(wraplength=width - 20)

    def move_by_key(self, dx=0, dy=0):
        x = self.prompter_window.winfo_x() + dx
        y = self.prompter_window.winfo_y() + dy
        self.prompter_window.geometry(f"+{x}+{y}")

    def zoom_in(self):
        self.font_size += 2
        self.update_font()

    def zoom_out(self):
        self.font_size = max(8, self.font_size - 2)
        self.update_font()

    def reset_zoom(self):
        self.font_size = 14
        self.update_font()

    def increase_opacity(self):
        self.opacity = min(1.0, self.opacity + 0.1)
        self.prompter_window.attributes("-alpha", self.opacity)

    def decrease_opacity(self):
        self.opacity = max(0.1, self.opacity - 0.1)
        self.prompter_window.attributes("-alpha", self.opacity)
    
    def toggle_visibility(self):
        if self.prompter_window.winfo_viewable():
            self.prompter_window.withdraw()
        else:
            self.prompter_window.deiconify()

    def start_new_problem(self):
        self.response_text.set("New session started. Ask a new question.")
        self.input_entry.delete(0, tk.END)
        self.input_entry.focus_set()

    def submit_query(self):
        question = self.input_entry.get()
        if question:
            self.response_text.set("Asking NotebookLM...")
            threading.Thread(target=self.send_request, args=(question,)).start()
            self.input_entry.delete(0, tk.END)
            
    def quit_app(self):
        # We need to stop the hotkey listener thread gracefully
        hotkey_listener.stop()
        self.root.quit()

    # --- API Communication ---
    def send_request(self, question):
        try:
            response = requests.post(API_URL, json={"question": question}, timeout=120)
            if response.status_code == 200:
                self.response_text.set(response.json().get("response", "No response text found."))
            else:
                self.response_text.set(f"Error: {response.json().get('error', 'API error')}")
        except requests.exceptions.ConnectionError:
            self.response_text.set("Error: Connection failed. Is server.py running?")
        except Exception as e:
            self.response_text.set(f"Error: {e}")

# --- Global Hotkey Manager (pynput) ---
# This runs in a separate thread to listen for key presses system-wide.
class HotKeyManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.hotkeys = {
            '<ctrl>+<enter>': self.app.submit_query,
            '<ctrl>+b': self.app.toggle_visibility,
            '<ctrl>+q': self.app.quit_app,
            '<ctrl>+r': self.app.start_new_problem,
            '<ctrl>+<up>': lambda: self.app.move_by_key(dy=-MOVE_AMOUNT),
            '<ctrl>+<down>': lambda: self.app.move_by_key(dy=MOVE_AMOUNT),
            '<ctrl>+<left>': lambda: self.app.move_by_key(dx=-MOVE_AMOUNT),
            '<ctrl>+<right>': lambda: self.app.move_by_key(dx=MOVE_AMOUNT),
            '<ctrl>+=': self.app.zoom_in,
            '<ctrl>+-': self.app.zoom_out,
            '<ctrl>+0': self.app.reset_zoom,
            '<ctrl>+]': self.app.increase_opacity, # Ctrl + ]
            '<ctrl>+[': self.app.decrease_opacity, # Ctrl + [
        }

    def start_listener(self):
        # The Hotkey listener runs in a non-blocking way
        self.listener = keyboard.GlobalHotKeys(self.hotkeys)
        self.listener.start()

    def stop(self):
        self.listener.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = TeleprompterApp(root)
    
    def kill_debug_chrome():
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'chrome.exe' in proc.info['name'].lower():
                cmd = ' '.join(proc.info['cmdline']).lower()
                if '--remote-debugging-port=9222' in cmd:
                    try:
                        proc.kill()
                    except Exception:
                        pass

    # Start the global hotkey listener
    hotkey_manager = HotKeyManager(app)
    hotkey_listener_thread = threading.Thread(target=hotkey_manager.start_listener)
    hotkey_listener_thread.daemon = True # Allows main thread to exit
    hotkey_listener_thread.start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Exiting Teleprompter App...")
    finally:
        hotkey_manager.stop()
        kill_debug_chrome()


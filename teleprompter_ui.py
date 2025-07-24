import tkinter as tk
from tkinter import font
import requests
import json
import threading
import sys
# Removed unused psutil import

# --- Conditional import for Windows-only library ---
if sys.platform == "win32":
    from pynput import keyboard

# --- Configuration ---
API_URL = "http://127.0.0.1:5000/query"
MOVE_AMOUNT = 15

class TeleprompterApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()

        # --- Window Creation and Styling ---
        self.prompter_window = tk.Toplevel(root)
        self.prompter_window.title("NotebookLM Teleprompter")
        self.prompter_window.geometry("900x200+100+50")
        self.prompter_window.overrideredirect(True)
        self.prompter_window.wm_attributes("-topmost", True)
        self.prompter_window.config(bg="#282c34")

        # --- Platform-Specific Setup ---
        if sys.platform == "win32":
            # On Windows, use ctypes for "invisibility" to screen recorders
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.prompter_window.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                style = style | 0x00000080
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
            except Exception as e:
                print(f"Could not set window style for invisibility: {e}")
        else: # For Linux/macOS
            # On Linux, set the window type to 'dialog' to fix focus issues
            self.prompter_window.wm_attributes('-type', 'utility')
            # Bind in-app hotkeys that work when the window is focused
            self.prompter_window.bind("<Control-Return>", self.submit_query)
            self.prompter_window.bind("<Control-b>", self.toggle_visibility)
            self.prompter_window.bind("<Control-q>", self.quit_app)
            self.prompter_window.bind("<Control-r>", self.start_new_problem)
            self.prompter_window.bind("<Control-Up>", lambda e: self.move_by_key(dy=-MOVE_AMOUNT))
            self.prompter_window.bind("<Control-Down>", lambda e: self.move_by_key(dy=MOVE_AMOUNT))
            self.prompter_window.bind("<Control-Left>", lambda e: self.move_by_key(dx=-MOVE_AMOUNT))
            self.prompter_window.bind("<Control-Right>", lambda e: self.move_by_key(dx=MOVE_AMOUNT))
            self.prompter_window.bind("<Control-equal>", self.zoom_in)
            self.prompter_window.bind("<Control-minus>", self.zoom_out)
            self.prompter_window.bind("<Control-0>", self.reset_zoom)
            self.prompter_window.bind("<Control-bracketright>", self.increase_opacity)
            self.prompter_window.bind("<Control-bracketleft>", self.decrease_opacity)

        # --- Opacity and Font/Zoom Control ---
        self.opacity = 0.8
        self.prompter_window.attributes("-alpha", self.opacity)
        self.font_size = 14

        # --- Main Widgets ---
        self.response_text = tk.StringVar()
        self.response_text.set("Welcome! Type a question and press Ctrl+Enter.")
        self.response_label = tk.Label(
            self.prompter_window, textvariable=self.response_text, fg="#abb2bf",
            bg="#282c34", wraplength=880, justify="left", anchor="nw"
        )
        self.response_label.pack(padx=10, pady=10, fill="both", expand=True)
        self.update_font()

        self.input_entry = tk.Entry(
            self.prompter_window, font=("Segoe UI", 12), bg="#21252b", fg="#abb2bf",
            insertbackground="white", bd=0, highlightthickness=1,
            highlightbackground="#61afef", highlightcolor="#61afef"
        )
        self.input_entry.pack(padx=10, pady=(0, 10), fill="x")
        self.input_entry.focus_set()

        # --- Window Interaction Handlers ---
        self._offset_x, self._offset_y = 0, 0
        self.prompter_window.bind("<ButtonPress-1>", self.start_move)
        self.prompter_window.bind("<ButtonRelease-1>", self.stop_move)
        self.prompter_window.bind("<B1-Motion>", self.do_move)
        
        # --- Resize Handle ---
        self.resize_handle = tk.Frame(self.prompter_window, bg="#61afef", cursor="sizing")
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se", width=10, height=10)
        self.resize_handle.bind("<B1-Motion>", self.do_resize)

        # --- Final Linux Focus Fix ---
        # Force focus onto the input box whenever the main window is clicked.
        self.prompter_window.bind("<Button-1>", self.force_focus)
        # Also bind to the label, so clicking anywhere in the window works
        self.response_label.bind("<Button-1>", self.force_focus)

    def update_font(self):
        new_font = font.Font(family="Segoe UI", size=self.font_size)
        self.response_label.config(font=new_font)

    # --- Window Management Methods ---
    def start_move(self, event):
        self._offset_x, self._offset_y = event.x, event.y

    def stop_move(self, event):
        self._offset_x, self._offset_y = 0, 0

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
        
    # --- Hotkey Methods (now accept 'event=None') ---
    def zoom_in(self, event=None):
        self.font_size += 2
        self.update_font()

    def zoom_out(self, event=None):
        self.font_size = max(8, self.font_size - 2)
        self.update_font()

    def reset_zoom(self, event=None):
        self.font_size = 14
        self.update_font()

    def increase_opacity(self, event=None):
        self.opacity = min(1.0, self.opacity + 0.1)
        self.prompter_window.attributes("-alpha", self.opacity)

    def decrease_opacity(self, event=None):
        self.opacity = max(0.1, self.opacity - 0.1)
        self.prompter_window.attributes("-alpha", self.opacity)
    
    def toggle_visibility(self, event=None):
        if self.prompter_window.winfo_viewable():
            self.prompter_window.withdraw()
        else:
            self.prompter_window.deiconify()

    def start_new_problem(self, event=None):
        self.response_text.set("New session started. Ask a new question.")
        self.input_entry.delete(0, tk.END)
        self.input_entry.focus_set()

    def submit_query(self, event=None):
        question = self.input_entry.get()
        if question:
            self.response_text.set("Asking NotebookLM...")
            threading.Thread(target=self.send_request, args=(question,)).start()
            self.input_entry.delete(0, tk.END)

    def force_focus(self, event=None): 
        """Aggressively force focus to the input entry widget for Linux."""
        self.prompter_window.lift() # Bring window to the front
        self.prompter_window.focus_force() # Force focus on the window itself
        self.input_entry.focus_set() # Tell the entry widget to accept focus
        self.input_entry.focus_force()


            
    def quit_app(self, event=None):
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.stop()
        self.root.destroy()

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

# --- Global Hotkey Manager (Windows-Only) ---
if sys.platform == "win32":
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
                '<ctrl>+]': self.app.increase_opacity,
                '<ctrl>+[': self.app.decrease_opacity,
            }
        def start_listener(self):
            self.listener = keyboard.GlobalHotKeys(self.hotkeys)
            self.listener.start()
        def stop(self):
            if hasattr(self, 'listener'):
                self.listener.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = TeleprompterApp(root)

    # --- Platform-Specific Hotkey Initialization ---
    if sys.platform == "win32":
        print("Windows detected. Initializing global hotkeys.")
        hotkey_manager = HotKeyManager(app)
        hotkey_listener_thread = threading.Thread(target=hotkey_manager.start_listener)
        hotkey_listener_thread.daemon = True
        hotkey_listener_thread.start()
        app.hotkey_manager = hotkey_manager 
    else:
        print("Linux/macOS detected. In-app hotkeys are active.")
        app.hotkey_manager = None

    root.mainloop()
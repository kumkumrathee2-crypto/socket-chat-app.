import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from datetime import datetime
from cryptography.fernet import Fernet

# ---------------- CONFIGURATION (must match server.py) ----------------
HOST = '127.0.0.1'
PORT = 5555
HEADER_LENGTH = 10
FORMAT = 'utf-8'
DISCONNECT_MSG = '!DISCONNECT'

SECRET_KEY = b'19qvwujIi2RpwFWO2bUG50QJARyBVzidbste76b_UbI='
fernet = Fernet(SECRET_KEY)

AVATAR_EMOJIS = ['🧑', '👩', '🧔', '👦', '👧', '🐱', '🐶', '🦊', '🐼', '🐵', '🦁', '🐸']

def get_avatar(username):
    idx = sum(ord(c) for c in username) % len(AVATAR_EMOJIS)
    return AVATAR_EMOJIS[idx]

EMOJI_LIST = ['😀', '😂', '😍', '😎', '🥳', '😢', '😡', '👍', '👎', '👏',
              '🙏', '🔥', '🎉', '❤️', '💯', '🤔', '😴', '👋', '✅', '❌']

DARK_THEME = {
    'bg': '#0e1621', 'panel_bg': '#17212b', 'chat_bg': '#0e1621',
    'entry_bg': '#242f3d', 'text_fg': '#ffffff',
    'self_bubble': '#2b7fff', 'self_text': '#ffffff',
    'other_bubble': '#1e2c3a', 'other_text': '#ffffff',
    'pm_bubble': '#7d5fff', 'pm_text': '#ffffff',
    'server_fg': '#9fb0c3', 'btn_bg': '#2b7fff'
}
LIGHT_THEME = {
    'bg': '#f5f7fa', 'panel_bg': '#e8ecf1', 'chat_bg': '#ffffff',
    'entry_bg': '#ffffff', 'text_fg': '#000000',
    'self_bubble': '#2b7fff', 'self_text': '#ffffff',
    'other_bubble': '#eef1f5', 'other_text': '#000000',
    'pm_bubble': '#a58cff', 'pm_text': '#ffffff',
    'server_fg': '#555555', 'btn_bg': '#2b7fff'
}

FONT_HEADER = ("Segoe UI", 14, "bold")
FONT_STATUS = ("Segoe UI", 12)
FONT_CHAT_HEADER = ("Segoe UI", 11, "bold")
FONT_CHAT_MSG = ("Segoe UI", 13)
FONT_SERVER = ("Segoe UI", 11, "italic")
FONT_ENTRY = ("Segoe UI", 13)
FONT_BUTTON = ("Segoe UI", 12, "bold")
FONT_HINT = ("Segoe UI", 10)
FONT_USERLIST_TITLE = ("Segoe UI", 12, "bold")
FONT_USERLIST_ITEM = ("Segoe UI", 12)
FONT_EMOJI = ("Segoe UI", 16)


class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.theme = DARK_THEME
        self.dark_mode = True

        self.root.title("Socket Chat App")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        self.username = simpledialog.askstring("Username", "Enter your username:", parent=self.root)
        if not self.username:
            self.root.destroy()
            return

        self.room = simpledialog.askstring("Room", "Enter room name to join (e.g. general):", parent=self.root)
        if not self.room or not self.room.strip():
            self.room = "general"
        self.room = self.room.strip()

        self.my_avatar = get_avatar(self.username)
        self.root.title(f"Socket Chat App - {self.username} (#{self.room}) (Encrypted)")

        # ---------------- TOP BAR ----------------
        self.top_bar = tk.Frame(root, height=55)
        self.top_bar.pack(fill='x')

        self.status_label = tk.Label(self.top_bar, text=f"{self.my_avatar}  {self.username}",
                                      font=FONT_HEADER)
        self.status_label.pack(side='left', padx=15, pady=10)

        self.room_label = tk.Label(self.top_bar, text=f"# {self.room}", font=FONT_STATUS)
        self.room_label.pack(side='left', padx=5)

        self.theme_btn = tk.Button(self.top_bar, text="☀ Light Mode", command=self.toggle_theme,
                                    bd=0, padx=12, pady=6, font=FONT_STATUS)
        self.theme_btn.pack(side='right', padx=(0, 12), pady=8)

        self.clear_btn = tk.Button(self.top_bar, text="🗑 Clear Chat", command=self.clear_chat,
                                    bd=0, padx=12, pady=6, font=FONT_STATUS)
        self.clear_btn.pack(side='right', padx=(0, 8), pady=8)

        self.join_btn = tk.Button(self.top_bar, text="🚪 Switch Room", command=self.switch_room,
                                   bd=0, padx=12, pady=6, font=FONT_STATUS)
        self.join_btn.pack(side='right', padx=(0, 8), pady=8)

        # ---------------- MAIN LAYOUT ----------------
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill='both', expand=True, padx=8, pady=8)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side='left', fill='both', expand=True)

        self.bottom_frame = tk.Frame(self.left_frame)
        self.bottom_frame.pack(side='bottom', fill='x', pady=(6, 0))

        self.emoji_btn = tk.Button(self.bottom_frame, text="😊", command=self.open_emoji_picker,
                                    bd=0, padx=10, pady=6, font=FONT_EMOJI)
        self.emoji_btn.pack(side='left', padx=(0, 6))

        self.msg_entry = tk.Entry(self.bottom_frame, font=FONT_ENTRY, bd=0)
        self.msg_entry.pack(side='left', fill='x', expand=True, ipady=10, padx=(0, 8))
        self.msg_entry.bind("<Return>", self.send_message)

        self.send_btn = tk.Button(self.bottom_frame, text="Send ➤", command=self.send_message,
                                   fg="white", bd=0, padx=20, pady=8, font=FONT_BUTTON)
        self.send_btn.pack(side='right')

        self.hint_label = tk.Label(
            self.left_frame,
            text="Tip:  /msg username message = private   |   /join roomname = switch room",
            font=FONT_HINT
        )
        self.hint_label.pack(side='bottom', fill='x', pady=(6, 0))

        self.chat_area = scrolledtext.ScrolledText(
            self.left_frame, state='disabled', wrap='word', font=FONT_CHAT_MSG, bd=0,
            spacing1=6, spacing3=10, padx=10, pady=10
        )
        self.chat_area.pack(side='top', fill='both', expand=True)

        self.chat_area.tag_configure('self_msg', justify='right', lmargin1=100, lmargin2=100, rmargin=6,
                                      spacing1=4, spacing3=10, wrap='word', font=FONT_CHAT_MSG)
        self.chat_area.tag_configure('self_header', justify='right', lmargin1=100, lmargin2=100, rmargin=6,
                                      font=FONT_CHAT_HEADER)
        self.chat_area.tag_configure('other_msg', justify='left', lmargin1=6, lmargin2=6, rmargin=100,
                                      spacing1=4, spacing3=10, wrap='word', font=FONT_CHAT_MSG)
        self.chat_area.tag_configure('other_header', justify='left', lmargin1=6, lmargin2=6, rmargin=100,
                                      font=FONT_CHAT_HEADER)
        self.chat_area.tag_configure('pm_msg', justify='left', lmargin1=6, lmargin2=6, rmargin=60,
                                      spacing1=4, spacing3=10, wrap='word', font=FONT_CHAT_MSG)
        self.chat_area.tag_configure('pm_header', justify='left', lmargin1=6, lmargin2=6, rmargin=60,
                                      font=FONT_CHAT_HEADER)
        self.chat_area.tag_configure('server_msg', justify='center', font=FONT_SERVER,
                                      spacing1=8, spacing3=8)

        self.right_frame = tk.Frame(self.main_frame, width=190)
        self.right_frame.pack(side='right', fill='y', padx=(10, 0))
        self.right_frame.pack_propagate(False)

        self.users_label = tk.Label(self.right_frame, text="🟢 Online in Room", font=FONT_USERLIST_TITLE)
        self.users_label.pack(pady=(8, 6))

        self.user_listbox = tk.Listbox(self.right_frame, font=FONT_USERLIST_ITEM, bd=0,
                                        highlightthickness=0)
        self.user_listbox.pack(fill='both', expand=True, padx=8, pady=8)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.apply_theme()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not connect to server:\n{e}")
            self.root.destroy()
            return

        self.send_raw(self.username)   # 1st handshake message: username
        self.send_raw(self.room)       # 2nd handshake message: room name

        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    # ---------------- ROOM SWITCHING ----------------
    def switch_room(self):
        new_room = simpledialog.askstring("Switch Room", "Enter room name to join:", parent=self.root)
        if new_room and new_room.strip():
            new_room = new_room.strip()
            self.send_raw(f"/join {new_room}")
            self.room = new_room
            self.room_label.configure(text=f"# {self.room}")
            self.root.title(f"Socket Chat App - {self.username} (#{self.room}) (Encrypted)")
            self.clear_chat(confirm=False)

    # ---------------- EMOJI PICKER ----------------
    def open_emoji_picker(self):
        picker = tk.Toplevel(self.root)
        picker.title("Pick an emoji")
        picker.geometry("260x180")
        picker.configure(bg=self.theme['panel_bg'])
        picker.resizable(False, False)

        row, col = 0, 0
        for emoji in EMOJI_LIST:
            btn = tk.Button(
                picker, text=emoji, font=FONT_EMOJI, bd=0,
                bg=self.theme['panel_bg'],
                command=lambda e=emoji: self.insert_emoji(e, picker)
            )
            btn.grid(row=row, column=col, padx=4, pady=4)
            col += 1
            if col >= 5:
                col = 0
                row += 1

    def insert_emoji(self, emoji, picker_window):
        self.msg_entry.insert(tk.INSERT, emoji)
        picker_window.destroy()
        self.msg_entry.focus_set()

    # ---------------- CLEAR CHAT ----------------
    def clear_chat(self, confirm=True):
        do_clear = True
        if confirm:
            do_clear = messagebox.askyesno("Clear Chat", "Clear all messages from your view?\n(This only clears your screen, not the server's saved history.)")
        if do_clear:
            self.chat_area.config(state='normal')
            self.chat_area.delete('1.0', tk.END)
            self.chat_area.config(state='disabled')

    # ---------------- THEME ----------------
    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t['bg'])
        self.top_bar.configure(bg=t['panel_bg'])
        self.status_label.configure(bg=t['panel_bg'], fg=t['text_fg'])
        self.room_label.configure(bg=t['panel_bg'], fg=t['server_fg'])
        self.theme_btn.configure(bg=t['btn_bg'], fg='white')
        self.clear_btn.configure(bg=t['btn_bg'], fg='white')
        self.join_btn.configure(bg=t['btn_bg'], fg='white')
        self.main_frame.configure(bg=t['bg'])
        self.left_frame.configure(bg=t['bg'])
        self.chat_area.configure(bg=t['chat_bg'], fg=t['text_fg'])

        self.chat_area.tag_configure('self_msg', background=t['self_bubble'], foreground=t['self_text'])
        self.chat_area.tag_configure('self_header', foreground=t['self_bubble'])
        self.chat_area.tag_configure('other_msg', background=t['other_bubble'], foreground=t['other_text'])
        self.chat_area.tag_configure('other_header', foreground=t['self_bubble'])
        self.chat_area.tag_configure('pm_msg', background=t['pm_bubble'], foreground=t['pm_text'])
        self.chat_area.tag_configure('pm_header', foreground=t['pm_bubble'])
        self.chat_area.tag_configure('server_msg', foreground=t['server_fg'])

        self.hint_label.configure(bg=t['bg'], fg=t['server_fg'])
        self.bottom_frame.configure(bg=t['bg'])
        self.emoji_btn.configure(bg=t['entry_bg'], fg=t['text_fg'])
        self.msg_entry.configure(bg=t['entry_bg'], fg=t['text_fg'], insertbackground=t['text_fg'])
        self.send_btn.configure(bg=t['btn_bg'])
        self.right_frame.configure(bg=t['panel_bg'])
        self.users_label.configure(bg=t['panel_bg'], fg=t['text_fg'])
        self.user_listbox.configure(bg=t['panel_bg'], fg=t['self_bubble'])

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme = DARK_THEME if self.dark_mode else LIGHT_THEME
        self.theme_btn.configure(text="☀ Light Mode" if self.dark_mode else "🌙 Dark Mode")
        self.apply_theme()

    # ---------------- LOW-LEVEL PROTOCOL ----------------
    def send_raw(self, message):
        encoded_message = message.encode(FORMAT)
        header = f"{len(encoded_message):<{HEADER_LENGTH}}".encode(FORMAT)
        self.client_socket.send(header + encoded_message)

    def receive_raw(self):
        header = self.client_socket.recv(HEADER_LENGTH).decode(FORMAT)
        if not header:
            return None
        message_length = int(header.strip())
        return self.client_socket.recv(message_length).decode(FORMAT)

    # ---------------- DISPLAY ----------------
    def add_bubble(self, avatar, sender_label, text, header_tag, msg_tag):
        timestamp = datetime.now().strftime('%I:%M %p')
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"\n{avatar} {sender_label}  ·  {timestamp}\n", header_tag)
        self.chat_area.insert(tk.END, f"{text}\n", msg_tag)
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)

    def display_server_msg(self, text):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"\n— {text} —\n", 'server_msg')
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)

    def update_user_list(self, user_list_str):
        self.user_listbox.delete(0, tk.END)
        for name in user_list_str.split(","):
            name = name.strip()
            if name:
                self.user_listbox.insert(tk.END, f"{get_avatar(name)} {name}")

    # ---------------- RECEIVING ----------------
    def listen_for_messages(self):
        while True:
            try:
                message = self.receive_raw()
                if message is None:
                    break

                if message.startswith("USERLIST:"):
                    self.update_user_list(message[len("USERLIST:"):])

                elif message.startswith("SERVER:"):
                    self.display_server_msg(message[len("SERVER:"):].strip())

                elif message.startswith("[PM"):
                    try:
                        prefix, encrypted_part = message.rsplit("]: ", 1)
                        decrypted = fernet.decrypt(encrypted_part.encode()).decode()
                        sender_name = prefix.replace("[PM from ", "").replace("[PM to ", "").strip()
                        self.add_bubble(get_avatar(sender_name), prefix + "]", decrypted,
                                         'pm_header', 'pm_msg')
                    except Exception:
                        self.display_server_msg(message)

                else:
                    try:
                        sender, encrypted_part = message.split(": ", 1)
                        decrypted = fernet.decrypt(encrypted_part.encode()).decode()
                        self.add_bubble(get_avatar(sender), sender, decrypted,
                                         'other_header', 'other_msg')
                    except Exception:
                        self.display_server_msg(message)
            except:
                break
        self.display_server_msg("Disconnected from server.")

    # ---------------- SENDING ----------------
        def send_private_message(self, target_username, message):
        encrypted_message = fernet.encrypt(message.encode()).decode()
        self.send_raw(f"/msg {target_username}|||{encrypted_message}")
        # No local display here — the server echoes "[PM to <target>]: ..." back to us,
        # and listen_for_messages() will display it once, correctly.

    def send_message(self, event=None):
        message = self.msg_entry.get().strip()
        if not message:
            return

        if message.startswith("/msg "):
            try:
                _, rest = message.split(" ", 1)
                target_username, actual_message = rest.split(" ", 1)
                self.send_private_message(target_username, actual_message)
            except ValueError:
                self.display_server_msg("Usage: /msg username your message here")
        else:
            encrypted_message = fernet.encrypt(message.encode()).decode()
            self.send_raw(encrypted_message)
            self.add_bubble(self.my_avatar, "You", message, 'self_header', 'self_msg')

        self.msg_entry.delete(0, tk.END)

    def on_close(self):
        try:
            self.send_raw(DISCONNECT_MSG)
            self.client_socket.close()
        except:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()
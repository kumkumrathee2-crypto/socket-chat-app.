# 🔐 Secure Multi-Room Socket Chat Application

A real-time, multi-client chat application built from scratch using raw TCP sockets in Python — featuring a custom message-framing protocol, AES encryption, multi-room support, private messaging, and a graphical interface.

## 📌 Features

- **Custom Protocol Design** — Implements a header-based message framing protocol over TCP to solve the "message boundary" problem inherent to stream-based sockets.
- **Multi-threaded Server** — Handles multiple simultaneous client connections using Python's `threading` module.
- **AES Encryption** — All chat messages are encrypted client-side using the `cryptography` library (Fernet/AES-128) before transmission. The server relays and stores only ciphertext, never plaintext.
- **Multi-Room Support** — Clients can join different chat rooms and switch between them live; messages are scoped to the room they're sent in.
- **Private Messaging** — Direct one-to-one encrypted messages using a `/msg username message` command, working independently of room membership.
- **Persistent Chat History** — All messages are logged to a local SQLite database (`chat_history.db`) with timestamps, usernames, and rooms.
- **Graphical User Interface** — Built with Tkinter, featuring:
  - Chat bubble-style message display with emoji avatars
  - Light/Dark theme toggle
  - Live "online users" panel
  - Emoji picker
  - Clear-chat option

## 🛠️ Tech Stack

- **Language:** Python 3
- **Networking:** `socket`, `threading` (raw TCP sockets)
- **Security:** `cryptography` (Fernet symmetric encryption)
- **Database:** `sqlite3`
- **GUI:** `tkinter`

## 📂 Project Structure

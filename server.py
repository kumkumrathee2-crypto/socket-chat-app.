import socket
import threading
import sqlite3
from datetime import datetime

# ---------------- CONFIGURATION ----------------
HOST = '0.0.0.0'
PORT = 5555
HEADER_LENGTH = 10
FORMAT = 'utf-8'
DISCONNECT_MSG = '!DISCONNECT'
DB_FILE = 'chat_history.db'

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            room TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_message_to_db(username, room, message):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO messages (username, room, message, timestamp) VALUES (?, ?, ?, ?)',
        (username, room, message, timestamp)
    )
    conn.commit()
    conn.close()

# ---------------- SERVER SETUP ----------------
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

# Each client_socket maps to a dict: {"username": ..., "room": ...}
clients = {}

def log(message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

def send_message(sock, message):
    encoded_message = message.encode(FORMAT)
    header = f"{len(encoded_message):<{HEADER_LENGTH}}".encode(FORMAT)
    sock.send(header + encoded_message)

def receive_message(sock):
    try:
        header = sock.recv(HEADER_LENGTH).decode(FORMAT)
        if not header:
            return None
        message_length = int(header.strip())
        return sock.recv(message_length).decode(FORMAT)
    except:
        return None

def broadcast_to_room(room, message, sender_socket=None):
    """Sends a message only to clients currently in the given room."""
    for sock, info in list(clients.items()):
        if sock != sender_socket and info['room'] == room:
            try:
                send_message(sock, message)
            except:
                remove_client(sock)

def broadcast_user_list_for_room(room):
    """Sends the online-user list, scoped to only that room's members."""
    usernames_in_room = [info['username'] for info in clients.values() if info['room'] == room]
    user_list = ",".join(usernames_in_room)
    for sock, info in list(clients.items()):
        if info['room'] == room:
            try:
                send_message(sock, f"USERLIST:{user_list}")
            except:
                remove_client(sock)

def find_socket_by_username(username):
    for sock, info in clients.items():
        if info['username'] == username:
            return sock
    return None

def remove_client(client_socket):
    info = clients.get(client_socket)
    if not info:
        return
    username, room = info['username'], info['room']
    del clients[client_socket]
    try:
        client_socket.close()
    except:
        pass
    log(f"[DISCONNECTED] {username} left room '{room}'. Active users: {len(clients)}")
    broadcast_to_room(room, f"SERVER: {username} has left the chat.")
    broadcast_user_list_for_room(room)

def handle_client(client_socket, address):
    try:
        # Handshake: username first, then room name
        username = receive_message(client_socket)
        room = receive_message(client_socket)
        if not room:
            room = "general"

        clients[client_socket] = {"username": username, "room": room}

        log(f"[NEW CONNECTION] {username} joined room '{room}' from {address}")
        broadcast_to_room(room, f"SERVER: {username} has joined the chat!", sender_socket=client_socket)
        send_message(client_socket, f"SERVER: Welcome, {username}! You're in room '{room}'.")
        broadcast_user_list_for_room(room)

        while True:
            message = receive_message(client_socket)
            if message is None or message == DISCONNECT_MSG:
                break

            current_room = clients[client_socket]['room']
            save_message_to_db(username, current_room, message)

            # ---------------- SWITCH ROOM ----------------
            if message.startswith("/join "):
                new_room = message[len("/join "):].strip()
                if new_room:
                    old_room = clients[client_socket]['room']
                    clients[client_socket]['room'] = new_room
                    broadcast_to_room(old_room, f"SERVER: {username} has left the chat.")
                    broadcast_user_list_for_room(old_room)
                    send_message(client_socket, f"SERVER: You joined room '{new_room}'.")
                    broadcast_to_room(new_room, f"SERVER: {username} has joined the chat!", sender_socket=client_socket)
                    broadcast_user_list_for_room(new_room)
                    log(f"[ROOM SWITCH] {username}: '{old_room}' -> '{new_room}'")

            # ---------------- PRIVATE MESSAGE (works across rooms) ----------------
            elif message.startswith("/msg "):
                try:
                    _, rest = message.split(" ", 1)
                    target_username, content = rest.split("|||", 1)
                    target_socket = find_socket_by_username(target_username)
                    if target_socket:
                        log(f"[PM] {username} -> {target_username}")
                        send_message(target_socket, f"[PM from {username}]: {content}")
                        send_message(client_socket, f"[PM to {target_username}]: {content}")
                    else:
                        send_message(client_socket, f"SERVER: User '{target_username}' not found or offline.")
                except Exception:
                    send_message(client_socket, "SERVER: Invalid private message format.")

            # ---------------- NORMAL ROOM BROADCAST ----------------
            else:
                log(f"[{username}@{current_room}] sent a broadcast message")
                broadcast_to_room(current_room, f"{username}: {message}", sender_socket=client_socket)

    except ConnectionResetError:
        pass
    finally:
        remove_client(client_socket)

def start_server():
    init_db()
    log(f"[STARTING] Server listening on {HOST}:{PORT}")
    log(f"[DATABASE] Chat history will be saved to {DB_FILE}")
    while True:
        client_socket, address = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, address), daemon=True)
        thread.start()
        log(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()
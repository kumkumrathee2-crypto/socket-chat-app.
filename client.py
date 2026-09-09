import socket
import threading

# ---------------- CONFIGURATION (must match server.py) ----------------
HOST = '127.0.0.1'    # Replace with server's actual IP if connecting over a real network
PORT = 5555
HEADER_LENGTH = 10
FORMAT = 'utf-8'
DISCONNECT_MSG = '!DISCONNECT'

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

def send_message(sock, message):
    """Encodes and sends a message using the custom header protocol."""
    encoded_message = message.encode(FORMAT)
    header = f"{len(encoded_message):<{HEADER_LENGTH}}".encode(FORMAT)
    sock.send(header + encoded_message)

def receive_message(sock):
    """Reads one full message using the custom header protocol."""
    try:
        header = sock.recv(HEADER_LENGTH).decode(FORMAT)
        if not header:
            return None
        message_length = int(header.strip())
        return sock.recv(message_length).decode(FORMAT)
    except:
        return None

def listen_for_messages():
    """Runs on a background thread — continuously listens for incoming messages."""
    while True:
        message = receive_message(client_socket)
        if message is None:
            print("\n[DISCONNECTED] Lost connection to server.")
            client_socket.close()
            break
        print(message)

def main():
    username = input("Enter your username: ")
    send_message(client_socket, username)   # Handshake: first message is the username

    listener_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listener_thread.start()

    print("Connected! Type your messages below (type '!DISCONNECT' to leave).\n")

    while True:
        message = input()
        send_message(client_socket, message)
        if message == DISCONNECT_MSG:
            break

    client_socket.close()

if __name__ == "__main__":
    main()
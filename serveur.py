import socket
import threading
import struct
import json

HOST = "0.0.0.0"
PORT = 5000

clients = {}
lock = threading.Lock()


def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def recv_frame(sock):
    header = recv_exact(sock, 4)
    if not header:
        return None
    length = struct.unpack(">I", header)[0]
    return recv_exact(sock, length)


def send_frame(sock, payload):
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)


def broadcast(payload, sender_sock=None):
    with lock:
        dead = []
        for client_sock in clients:
            if client_sock != sender_sock:
                try:
                    send_frame(client_sock, payload)
                except:
                    dead.append(client_sock)

        for client_sock in dead:
            try:
                client_sock.close()
            except:
                pass
            if client_sock in clients:
                del clients[client_sock]


def handle_client(client_sock, addr):
    username = "anonymous"

    try:
        first_payload = recv_frame(client_sock)
        if first_payload is None:
            client_sock.close()
            return

        first_message = json.loads(first_payload.decode("utf-8"))
        if first_message.get("type") == "join":
            username = first_message.get("username", "anonymous")

        with lock:
            clients[client_sock] = username

        print(f"[+] {username} connecté depuis {addr}")

        join_msg = {
            "type": "info",
            "message": f"{username} a rejoint le chat."
        }
        broadcast(json.dumps(join_msg).encode("utf-8"), sender_sock=client_sock)

        while True:
            payload = recv_frame(client_sock)
            if payload is None:
                break

            data = json.loads(payload.decode("utf-8"))

            if data.get("type") == "chat":
                msg = {
                    "type": "chat",
                    "from": username,
                    "message": data.get("message", "")
                }
                print(f"[{username}] {data.get('message', '')}")
                broadcast(json.dumps(msg).encode("utf-8"), sender_sock=client_sock)

    except Exception as e:
        print(f"[!] Erreur avec {addr} : {e}")

    finally:
        with lock:
            if client_sock in clients:
                left_username = clients[client_sock]
                del clients[client_sock]
            else:
                left_username = username

        try:
            client_sock.close()
        except:
            pass

        print(f"[-] {left_username} déconnecté")

        leave_msg = {
            "type": "info",
            "message": f"{left_username} a quitté le chat."
        }
        broadcast(json.dumps(leave_msg).encode("utf-8"))


def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(5)

    print(f"Serveur lancé sur {HOST}:{PORT}")

    try:
        while True:
            client_sock, addr = server_sock.accept()
            thread = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        with lock:
            for client_sock in list(clients.keys()):
                try:
                    client_sock.close()
                except:
                    pass
        server_sock.close()


if __name__ == "__main__":
    main()

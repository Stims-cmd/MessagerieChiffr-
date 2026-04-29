import socket
import threading
import struct
import json
import sys

#lien avec nos programmes de cryptage
import crypto as cp

HOST = str(input("Entrez l'IP du serveur : "))
PORT = 5000


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


def receive_loop(sock):
    while True:
        try:
            payload = recv_frame(sock)
            if payload is None:
                print("\n[!] Connexion fermée par le serveur.")
                break

            data = json.loads(payload.decode("utf-8"))

            if data.get("type") == "chat":
                sender = data.get("from", "unknown")
                message = data.get("message", "")
                print(f"\n{sender} : {message}")

            elif data.get("type") == "info":
                message = data.get("message", "")
                print(f"\n[INFO] {message}")

        except Exception as e:
            print(f"\n[!] Erreur réception : {e}")
            break


def main():
    if len(sys.argv) >= 2:
        username = sys.argv[1]
    else:
        username = input("Pseudo : ").strip()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    join_msg = {
        "type": "join",
        "username": username
    }
    send_frame(sock, json.dumps(join_msg).encode("utf-8"))

    #----------------------------------------------------------------
    #Generation et stockage du RSA
    #----------------------------------------------------------------
    cle_public, cle_privee=cp.recup_cle_rsa()
    #----------------------------------------------------------------

    print(f"Connecté au serveur {HOST}:{PORT}")
    print("Tape tes messages. /quit pour quitter.\n")

    thread = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
    thread.start()

    try:
        while True:
            text = input()
            if not text.strip():
                continue

            if text == "/quit":
                break

            msg = {
                "type": "chat",
                "message": text
            }

            send_frame(sock, json.dumps(msg).encode("utf-8"))

    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        print("Déconnecté.")


if __name__ == "__main__":
    main()

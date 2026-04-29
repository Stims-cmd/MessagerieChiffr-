import socket
import threading
import struct
import json

HOST = "0.0.0.0"
PORT = 5000

# Dictionnaire : socket -> {"username": str, "public_key": str}
# On stocke maintenant la clé publique en plus du pseudo
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


def broadcast_keylist():
    """
    Construit la liste des clés publiques de tous les clients connectés
    et la diffuse à tout le monde (y compris l'expéditeur cette fois,
    car tout le monde a besoin de la liste complète à jour).
    Format envoyé :
    {
        "type": "keylist",
        "keys": {
            "Alice": "-----BEGIN PUBLIC KEY-----...",
            "Bob":   "-----BEGIN PUBLIC KEY-----..."
        }
    }
    """
    with lock:
        # On construit un dict pseudo -> clé_publique pour tous les connectés
        keys = {
            info["username"]: info["public_key"]
            for info in clients.values()
        }

        keylist_msg = json.dumps({
            "type": "keylist",
            "keys": keys
        }).encode("utf-8")

        dead = []
        for client_sock in clients:
            try:
                send_frame(client_sock, keylist_msg)
            except:
                dead.append(client_sock)

        # Nettoyage des sockets morts détectés pendant l'envoi
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
        # ---- Lecture du premier message (join) ----
        first_payload = recv_frame(client_sock)
        if first_payload is None:
            client_sock.close()
            return

        first_message = json.loads(first_payload.decode("utf-8"))

        if first_message.get("type") == "join":
            username   = first_message.get("username", "anonymous")
            public_key = first_message.get("public_key", "")
            # Si le client n'a pas envoyé de clé, on log un avertissement
            if not public_key:
                print(f"[!] {username} n'a pas envoyé de clé publique")
        else:
            # Message inattendu comme premier message
            public_key = ""

        # ---- Enregistrement du client ----
        with lock:
            clients[client_sock] = {
                "username":   username,
                "public_key": public_key
            }

        print(f"[+] {username} connecté depuis {addr}")

        # ---- Notification d'arrivée aux autres ----
        join_msg = json.dumps({
            "type":    "info",
            "message": f"{username} a rejoint le chat."
        }).encode("utf-8")
        broadcast(join_msg, sender_sock=client_sock)

        # ---- Diffusion de la liste de clés mise à jour à TOUS ----
        # (y compris le nouvel arrivant, qui reçoit ainsi les clés des autres)
        broadcast_keylist()

        # ---- Boucle principale de réception ----
        while True:
            payload = recv_frame(client_sock)
            if payload is None:
                break

            data = json.loads(payload.decode("utf-8"))

            if data.get("type") == "chat":
                msg = json.dumps({
                    "type":    "chat",
                    "from":    username,
                    "message": data.get("message", "")
                }).encode("utf-8")
                #print(f"[{username}] {data.get('message', '')}")
                broadcast(msg, sender_sock=client_sock)

    except Exception as e:
        print(f"[!] Erreur avec {addr} : {e}")

    finally:
        # ---- Déconnexion : suppression de la clé et re-diffusion ----
        with lock:
            if client_sock in clients:
                left_username = clients[client_sock]["username"]
                del clients[client_sock]   # La clé publique est supprimée ici
            else:
                left_username = username

        try:
            client_sock.close()
        except:
            pass

        print(f"[-] {left_username} déconnecté")

        # On informe les autres de la déconnexion
        leave_msg = json.dumps({
            "type":    "info",
            "message": f"{left_username} a quitté le chat."
        }).encode("utf-8")
        broadcast(leave_msg)

        # On rediffuse la liste sans la clé du déconnecté
        broadcast_keylist()


def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(5)

    print(f"Serveur lancé sur {HOST}:{PORT}")

    try:
        while True:
            client_sock, addr = server_sock.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                daemon=True
            )
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
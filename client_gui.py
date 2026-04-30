import socket
import threading
import struct
import json
import tkinter as tk
import crypto as cp
from tkinter import messagebox, scrolledtext


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


class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Client Chat TCP")
        self.root.geometry("700x500")
        self.root.configure(bg="#f4f6f8")

        self.sock = None
        self.connected = False

        self.build_ui()

    def build_ui(self):
        top_frame = tk.Frame(self.root, bg="#f4f6f8")
        top_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(top_frame, text="Pseudo :", bg="#f4f6f8").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(top_frame, width=15)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        self.username_entry.insert(0, "Alice")

        tk.Label(top_frame, text="IP serveur :", bg="#f4f6f8").grid(row=0, column=2, padx=5, pady=5)
        self.host_entry = tk.Entry(top_frame, width=18)
        self.host_entry.grid(row=0, column=3, padx=5, pady=5)
        self.host_entry.insert(0, "127.0.0.1")

        tk.Label(top_frame, text="Port :", bg="#f4f6f8").grid(row=0, column=4, padx=5, pady=5)
        self.port_entry = tk.Entry(top_frame, width=8)
        self.port_entry.grid(row=0, column=5, padx=5, pady=5)
        self.port_entry.insert(0, "5000")

        self.connect_button = tk.Button(top_frame, text="Connexion", command=self.connect_to_server, bg="#2563eb", fg="white")
        self.connect_button.grid(row=0, column=6, padx=8, pady=5)

        self.disconnect_button = tk.Button(top_frame, text="Déconnexion", command=self.disconnect, state="disabled")
        self.disconnect_button.grid(row=0, column=7, padx=5, pady=5)

        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state="disabled", font=("Arial", 11))
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        bottom_frame = tk.Frame(self.root, bg="#f4f6f8")
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.message_entry = tk.Entry(bottom_frame, font=("Arial", 11))
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        self.message_entry.config(state="disabled")

        self.send_button = tk.Button(bottom_frame, text="Envoyer", command=self.send_message, bg="#16a34a", fg="white", state="disabled")
        self.send_button.pack(side="right")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, text + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state="disabled")

    def safe_log(self, text):
        self.root.after(0, lambda: self.log(text))

    def connect_to_server(self):
        if self.connected:
            return

        username = self.username_entry.get().strip()
        host = self.host_entry.get().strip()
        port_text = self.port_entry.get().strip()

        if not username:
            messagebox.showerror("Erreur", "Le pseudo est obligatoire.")
            return

        if not host:
            messagebox.showerror("Erreur", "L'IP du serveur est obligatoire.")
            return

        try:
            port = int(port_text)
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit être un nombre.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))

            join_msg = {
                "type": "join",
                "username": username
            }
            send_frame(self.sock, json.dumps(join_msg).encode("utf-8"))

            self.connected = True
            self.username = username

            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            self.message_entry.config(state="normal")
            self.send_button.config(state="normal")
            self.username_entry.config(state="disabled")
            self.host_entry.config(state="disabled")
            self.port_entry.config(state="disabled")

            self.log(f"[INFO] Connecté au serveur {host}:{port} en tant que {username}")

            thread = threading.Thread(target=self.receive_loop, daemon=True)
            thread.start()

        except Exception as e:
            messagebox.showerror("Erreur connexion", f"Impossible de se connecter : {e}")

    def receive_loop(self):
        while self.connected:
            try:
                payload = recv_frame(self.sock)
                if payload is None:
                    self.safe_log("[INFO] Connexion fermée par le serveur.")
                    break

                data = json.loads(payload.decode("utf-8"))

                if data.get("type") == "chat":
                    sender = data.get("from", "unknown")
                    message = data.get("message", "")
                    self.safe_log(f"{sender} : {message}")

                elif data.get("type") == "info":
                    message = data.get("message", "")
                    self.safe_log(f"[INFO] {message}")

            except Exception as e:
                self.safe_log(f"[ERREUR] Réception impossible : {e}")
                break

        self.root.after(0, self.reset_ui_after_disconnect)

    def send_message(self):
        if not self.connected:
            return

        text = self.message_entry.get().strip()
        if not text:
            return

        try:
            msg = {
                "type": "chat",
                "message": text
            }
            send_frame(self.sock, json.dumps(msg).encode("utf-8"))
            self.log(f"Moi : {text}")
            self.message_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Erreur envoi", f"Impossible d'envoyer le message : {e}")
            self.disconnect()

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.connected = False
        self.reset_ui_after_disconnect()
        self.log("[INFO] Déconnecté.")

    def reset_ui_after_disconnect(self):
        self.connected = False
        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")
        self.message_entry.config(state="disabled")
        self.send_button.config(state="disabled")
        self.username_entry.config(state="normal")
        self.host_entry.config(state="normal")
        self.port_entry.config(state="normal")

    def on_close(self):
        self.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()
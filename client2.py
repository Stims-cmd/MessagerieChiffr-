import socket
import threading
import struct
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext

# lien avec nos programmes de cryptage
import crypto as cp

HOST = "127.0.0.1"
PORT = 5000


# ----------------------------------------------------------------
# Fonctions réseau (inchangées depuis client.py original)
# ----------------------------------------------------------------

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


# ----------------------------------------------------------------
# Interface graphique Tkinter
# ----------------------------------------------------------------

class ClientChat:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat TCP")
        self.root.geometry("600x480")
        self.root.resizable(False, False)

        self.sock = None
        self.connected = False
        self.username = ""

        self._build_ui()

    def _build_ui(self):
        """Construit tous les widgets de la fenêtre."""

        # --- Barre de connexion ---
        frame_top = tk.Frame(self.root, pady=6)
        frame_top.pack(fill="x", padx=10)

        tk.Label(frame_top, text="Pseudo :").grid(row=0, column=0, padx=4)
        self.entry_pseudo = tk.Entry(frame_top, width=12)
        self.entry_pseudo.insert(0, "Alice")
        self.entry_pseudo.grid(row=0, column=1, padx=4)

        tk.Label(frame_top, text="IP :").grid(row=0, column=2, padx=4)
        self.entry_ip = tk.Entry(frame_top, width=14)
        self.entry_ip.insert(0, HOST)
        self.entry_ip.grid(row=0, column=3, padx=4)

        tk.Label(frame_top, text="Port :").grid(row=0, column=4, padx=4)
        self.entry_port = tk.Entry(frame_top, width=6)
        self.entry_port.insert(0, str(PORT))
        self.entry_port.grid(row=0, column=5, padx=4)

        self.btn_connect = tk.Button(
            frame_top, text="Connexion",
            bg="#2563eb", fg="white", width=10,
            command=self.se_connecter
        )
        self.btn_connect.grid(row=0, column=6, padx=6)

        self.btn_disconnect = tk.Button(
            frame_top, text="Déconnexion",
            width=11, state="disabled",
            command=self.se_deconnecter
        )
        self.btn_disconnect.grid(row=0, column=7, padx=4)

        # --- Zone de chat ---
        self.zone_chat = scrolledtext.ScrolledText(
            self.root, state="disabled",
            wrap=tk.WORD, font=("Courier", 10),
            bg="#1e1e2e", fg="#cdd6f4",
            insertbackground="white"
        )
        self.zone_chat.pack(fill="both", expand=True, padx=10, pady=6)

        # Couleurs pour les différents types de messages
        self.zone_chat.tag_config("moi",   foreground="#a6e3a1")   # vert
        self.zone_chat.tag_config("autre", foreground="#89b4fa")   # bleu
        self.zone_chat.tag_config("info",  foreground="#f9e2af")   # jaune

        # --- Barre d'envoi ---
        frame_bottom = tk.Frame(self.root, pady=6)
        frame_bottom.pack(fill="x", padx=10)

        self.entry_msg = tk.Entry(frame_bottom, font=("Arial", 11), state="disabled")
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_msg.bind("<Return>", lambda e: self.envoyer_message())

        self.btn_send = tk.Button(
            frame_bottom, text="Envoyer",
            bg="#16a34a", fg="white", width=9,
            state="disabled",
            command=self.envoyer_message
        )
        self.btn_send.pack(side="right")

        # Fermeture propre de la fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.fermer)

    # ----------------------------------------------------------------
    # Affichage dans la zone de chat
    # ----------------------------------------------------------------

    def afficher(self, texte, tag="info"):
        """Ajoute une ligne dans la zone de chat (thread-safe via after)."""
        self.root.after(0, lambda: self._ecrire(texte, tag))

    def _ecrire(self, texte, tag):
        self.zone_chat.config(state="normal")
        self.zone_chat.insert(tk.END, texte + "\n", tag)
        self.zone_chat.see(tk.END)
        self.zone_chat.config(state="disabled")

    # ----------------------------------------------------------------
    # Connexion / Déconnexion
    # ----------------------------------------------------------------

    def se_connecter(self):
        pseudo = self.entry_pseudo.get().strip()
        ip     = self.entry_ip.get().strip()
        port_s = self.entry_port.get().strip()

        if not pseudo:
            messagebox.showerror("Erreur", "Le pseudo est obligatoire.")
            return
        if not ip:
            messagebox.showerror("Erreur", "L'adresse IP est obligatoire.")
            return
        try:
            port = int(port_s)
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit être un entier.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
        except Exception as e:
            messagebox.showerror("Connexion impossible", str(e))
            return

        # Envoi du message "join" au serveur
        send_frame(self.sock, json.dumps({"type": "join", "username": pseudo}).encode())

        # Génération et stockage des clés RSA (inchangé depuis client.py)
        cle_public, cle_privee = cp.recup_cle_rsa()

        self.username  = pseudo
        self.connected = True

        # Mise à jour de l'interface
        self.entry_pseudo.config(state="disabled")
        self.entry_ip.config(state="disabled")
        self.entry_port.config(state="disabled")
        self.btn_connect.config(state="disabled")
        self.btn_disconnect.config(state="normal")
        self.entry_msg.config(state="normal")
        self.btn_send.config(state="normal")
        self.entry_msg.focus()

        self.afficher(f"[INFO] Connecté au serveur {ip}:{port} en tant que {pseudo}", "info")

        # Thread de réception (daemon = il s'arrête avec la fenêtre)
        t = threading.Thread(target=self.boucle_reception, daemon=True)
        t.start()

    def se_deconnecter(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.afficher("[INFO] Déconnecté.", "info")
        self._reset_ui()

    def _reset_ui(self):
        """Remet l'interface dans l'état 'non connecté'."""
        self.entry_pseudo.config(state="normal")
        self.entry_ip.config(state="normal")
        self.entry_port.config(state="normal")
        self.btn_connect.config(state="normal")
        self.btn_disconnect.config(state="disabled")
        self.entry_msg.config(state="disabled")
        self.btn_send.config(state="disabled")

    # ----------------------------------------------------------------
    # Réception des messages (thread secondaire)
    # ----------------------------------------------------------------

    def boucle_reception(self):
        while self.connected:
            try:
                payload = recv_frame(self.sock)
                if payload is None:
                    self.afficher("[INFO] Connexion fermée par le serveur.", "info")
                    break

                data = json.loads(payload.decode("utf-8"))

                if data.get("type") == "chat":
                    expediteur = data.get("from", "inconnu")
                    message    = data.get("message", "")
                    self.afficher(f"{expediteur} : {message}", "autre")

                elif data.get("type") == "info":
                    self.afficher(f"[INFO] {data.get('message', '')}", "info")

            except Exception as e:
                if self.connected:
                    self.afficher(f"[ERREUR] Réception : {e}", "info")
                break

        self.root.after(0, self._reset_ui)

    # ----------------------------------------------------------------
    # Envoi d'un message
    # ----------------------------------------------------------------

    def envoyer_message(self):
        if not self.connected:
            return

        texte = self.entry_msg.get().strip()
        if not texte:
            return

        if texte == "/quit":
            self.se_deconnecter()
            return

        try:
            msg = {"type": "chat", "message": texte}
            send_frame(self.sock, json.dumps(msg).encode("utf-8"))
            self.afficher(f"Moi : {texte}", "moi")
            self.entry_msg.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erreur envoi", str(e))
            self.se_deconnecter()

    # ----------------------------------------------------------------
    # Fermeture de la fenêtre
    # ----------------------------------------------------------------

    def fermer(self):
        self.se_deconnecter()
        self.root.destroy()


# ----------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientChat(root)
    root.mainloop()
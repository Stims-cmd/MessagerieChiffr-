import socket        # Fournit les outils pour créer des connexions réseau (TCP/IP)
import threading      # Permet de lancer des tâches en parallèle (ex : recevoir pendant qu'on tape)
import struct         # Permet de convertir des nombres en séquences d'octets (sérialisation binaire)
import json           # Permet d'encoder/décoder des données au format JSON (texte structuré)
import tkinter as tk  # Bibliothèque standard Python pour créer des interfaces graphiques (fenêtres, boutons...)
from tkinter import messagebox, scrolledtext  # Composants spécifiques : boîtes d'alerte et zone de texte avec scroll

import crypto as cp   # Module personnalisé (fichier crypto.py local) qui gère le chiffrement RSA


# ==============================================================
# FONCTIONS RÉSEAU
# ==============================================================

# Reçoit exactement n octets depuis le socket (pas plus, pas moins)
def recv_exact(sock, n):
    data = b""                        # On commence avec des données vides (b"" = bytes vide)
    while len(data) < n:              # On continue tant qu'on n'a pas reçu les n octets attendus
        chunk = sock.recv(n - len(data))  # On lit au maximum ce qu'il manque (évite de dépasser)
        if not chunk:                 # Si recv() renvoie des bytes vides, la connexion est coupée
            return None               # On retourne None pour signaler la déconnexion
        data += chunk                 # On ajoute le morceau reçu à l'accumulation
    return data                       # On retourne les n octets complets


# Reçoit un message complet : d'abord la taille (4 octets), puis le contenu
def recv_frame(sock):
    header = recv_exact(sock, 4)      # On lit exactement 4 octets : c'est l'entête qui contient la taille du message
    if not header:                    # Si header est None (connexion coupée), on propage l'erreur
        return None
    taille = struct.unpack(">I", header)[0]  # On décode les 4 octets en entier non signé 32 bits (big-endian)
                                             # ">I" : ">" = big-endian, "I" = unsigned int 32 bits
                                             # [0] : unpack retourne un tuple, on prend le premier élément
    return recv_exact(sock, taille)   # On lit exactement autant d'octets que indiqué dans l'entête


# Envoie un message : on préfixe avec la taille pour que le serveur sache
# combien d'octets il doit lire
def send_frame(sock, payload):
    header = struct.pack(">I", len(payload))  # On encode la longueur du message en 4 octets big-endian
    sock.sendall(header + payload)            # On envoie d'un seul coup : entête + contenu
                                              # sendall() garantit que tous les octets sont bien envoyés


# ==============================================================
# INTERFACE GRAPHIQUE
# ==============================================================

class ClientChat:  # Classe principale qui regroupe toute la logique de l'interface et du réseau

    def __init__(self, root):
        self.root = root                              # root = la fenêtre principale Tkinter
        self.root.title("Chat TCP")                   # Titre de la fenêtre (affiché dans la barre du haut)
        self.root.geometry("600x480")                 # Taille initiale de la fenêtre (largeur x hauteur en pixels)

        # Ces variables gardent l'état de la connexion
        self.sock      = None    # Le socket réseau, None quand on n'est pas connecté
        self.connected = False   # Booléen : True si on est connecté au serveur
        self.username  = ""      # Pseudo de l'utilisateur courant (rempli lors de la connexion)

        # Clés RSA générées au démarrage du client (clé publique et clé privée)
        # cp.recup_cle_rsa() est une fonction du module crypto.py
        self.cle_pub, self.cle_priv = cp.recup_cle_rsa()
        self.cles_publiques = {}  # dict pseudo -> clé_publique des autres clients
        self.build_ui()  # On construit l'interface graphique (définie plus bas)


    # ----------------------------------------------------------
    # Construction de l'interface
    # ----------------------------------------------------------

    def build_ui(self):

        # == Ligne du haut : champs pseudo / IP / port + boutons ==
        barre = tk.Frame(self.root, pady=6)  # Un Frame est un conteneur vide qui organise les widgets
                                             # pady=6 = 6 pixels de marge verticale
        barre.pack(fill="x", padx=10)        # fill="x" : le frame s'étire horizontalement ; padx=10 = marges latérales

        tk.Label(barre, text="Pseudo :").grid(row=0, column=0)  # Label texte "Pseudo :" dans la grille, colonne 0
        self.champ_pseudo = tk.Entry(barre, width=10)            # Champ de saisie texte pour le pseudo (10 caractères)
        self.champ_pseudo.insert(0, "Alice")                     # Valeur par défaut pré-remplie : "Alice"
        self.champ_pseudo.grid(row=0, column=1, padx=4)          # Placement en grille, colonne 1, avec marge

        tk.Label(barre, text="IP :").grid(row=0, column=2)  # Label "IP :" en colonne 2
        self.champ_ip = tk.Entry(barre, width=14)            # Champ de saisie pour l'adresse IP (14 caractères)
        self.champ_ip.insert(0, "127.0.0.1")                 # Valeur par défaut : localhost (propre machine)
        self.champ_ip.grid(row=0, column=3, padx=4)

        tk.Label(barre, text="Port :").grid(row=0, column=4)  # Label "Port :" en colonne 4
        self.champ_port = tk.Entry(barre, width=6)             # Champ de saisie pour le port (6 caractères)
        self.champ_port.insert(0, "5000")                      # Port par défaut : 5000
        self.champ_port.grid(row=0, column=5, padx=4)

        self.btn_co = tk.Button(barre, text="Connexion",  # Bouton "Connexion"
                                bg="#2563eb", fg="white", # Fond bleu, texte blanc
                                command=self.se_connecter) # Appelle se_connecter() au clic
        self.btn_co.grid(row=0, column=6, padx=6)

        self.btn_deco = tk.Button(barre, text="Déconnexion",  # Bouton "Déconnexion"
                                  state="disabled",            # Désactivé au démarrage (on n'est pas encore connecté)
                                  command=self.se_deconnecter) # Appelle se_deconnecter() au clic
        self.btn_deco.grid(row=0, column=7)

        # == Zone de messages ==
        self.zone_chat = scrolledtext.ScrolledText(
            self.root, state="disabled",         # "disabled" = lecture seule, on ne peut pas taper dedans
            wrap=tk.WORD, font=("Courier", 10),  # Retour à la ligne aux mots ; police Courier taille 10
            bg="#1e1e2e", fg="#cdd6f4"           # Fond sombre et texte clair (thème "Catppuccin Mocha")
        )
        self.zone_chat.pack(fill="both", expand=True, padx=10, pady=6)
        # fill="both" + expand=True : la zone remplit tout l'espace disponible quand on redimensionne

        # On définit 3 couleurs de tag : vert = moi, bleu = les autres, jaune = infos système
        self.zone_chat.tag_config("moi",   foreground="#a6e3a1")  # Vert pour ses propres messages
        self.zone_chat.tag_config("autre", foreground="#89b4fa")  # Bleu pour les messages des autres
        self.zone_chat.tag_config("info",  foreground="#f9e2af")  # Jaune/orange pour les messages système

        # == Ligne du bas : champ de saisie + bouton Envoyer ==
        bas = tk.Frame(self.root, pady=6)  # Deuxième frame pour la barre d'envoi en bas
        bas.pack(fill="x", padx=10)

        self.champ_msg = tk.Entry(bas, font=("Arial", 11), state="disabled")
        # Champ de saisie pour taper les messages, désactivé tant qu'on n'est pas connecté
        self.champ_msg.pack(side="left", fill="x", expand=True, padx=(0, 8))
        # side="left" : collé à gauche ; fill+expand : occupe tout l'espace horizontal disponible

        # Appui sur Entrée = déclenche envoyer() ; lambda e: ignore l'argument event obligatoire de Tkinter
        self.champ_msg.bind("<Return>", lambda e: self.envoyer())

        self.btn_send = tk.Button(bas, text="Envoyer",  # Bouton "Envoyer"
                                  bg="#16a34a", fg="white",  # Fond vert, texte blanc
                                  state="disabled",          # Désactivé au démarrage
                                  command=self.envoyer)      # Appelle envoyer() au clic
        self.btn_send.pack(side="right")  # Collé à droite de la barre

        # Intercepte la fermeture de fenêtre (croix rouge) pour une déconnexion propre
        self.root.protocol("WM_DELETE_WINDOW", self.fermer)


    # ----------------------------------------------------------
    # Affichage d'un message dans la zone de chat
    # ----------------------------------------------------------

    def afficher(self, texte, tag="info"):
        # root.after(0, ...) planifie l'exécution dans le thread principal Tkinter
        # C'est INDISPENSABLE car Tkinter n'est pas thread-safe :
        # modifier un widget depuis un autre thread provoquerait un crash
        self.root.after(0, lambda: self._ecrire(texte, tag))

    def _ecrire(self, texte, tag):
        self.zone_chat.config(state="normal")       # On réactive temporairement l'écriture dans la zone
        self.zone_chat.insert(tk.END, texte + "\n", tag)  # On insère le texte à la fin avec le tag de couleur
        self.zone_chat.see(tk.END)                  # On scroll automatiquement pour voir le dernier message
        self.zone_chat.config(state="disabled")     # On repasse en lecture seule pour bloquer la saisie directe


    # ----------------------------------------------------------
    # Connexion au serveur
    # ----------------------------------------------------------

    def se_connecter(self):
        pseudo = self.champ_pseudo.get().strip()  # Lecture du pseudo saisi (.strip() supprime les espaces inutiles)
        ip     = self.champ_ip.get().strip()      # Lecture de l'IP saisie

        # Vérification basique des champs obligatoires
        if not pseudo or not ip:
            messagebox.showerror("Erreur", "Pseudo et IP sont obligatoires.")
            return  # On sort de la fonction sans rien faire
        try:
            port = int(self.champ_port.get())  # On convertit le port en entier
        except ValueError:                     # int() lève ValueError si ce n'est pas un nombre
            messagebox.showerror("Erreur", "Le port doit être un nombre.")
            return

        # Tentative de connexion TCP au serveur
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # AF_INET = protocole IPv4 ; SOCK_STREAM = connexion TCP (fiable, avec vérification d'ordre)
            self.sock.connect((ip, port))  # On établit la connexion vers le serveur (bloquant jusqu'au succès)
        except Exception as e:
            messagebox.showerror("Connexion impossible", str(e))  # Affiche l'erreur système (ex: "Connection refused")
            return

        # On envoie notre pseudo au serveur sous forme de message JSON de type "join"
        # json.dumps() convertit le dict Python en chaîne JSON ; .encode() la transforme en bytes
        send_frame(self.sock, json.dumps({
            "type": "join",
            "username": pseudo,
            "public_key": self.cle_pub
        }).encode())

        self.username  = pseudo  # On mémorise le pseudo pour usage ultérieur
        self.connected = True    # On marque l'état comme connecté

        # On grise/désactive les champs de connexion (on ne peut plus changer pendant la session)
        for w in [self.champ_pseudo, self.champ_ip, self.champ_port]:
            w.config(state="disabled")
        self.btn_co.config(state="disabled")   # Le bouton "Connexion" devient inactif
        self.btn_deco.config(state="normal")   # Le bouton "Déconnexion" devient actif
        self.champ_msg.config(state="normal")  # Le champ de message devient éditable
        self.btn_send.config(state="normal")   # Le bouton "Envoyer" devient actif
        self.champ_msg.focus()                 # On place le curseur dans le champ message automatiquement

        self.afficher(f"[INFO] Connecté à {ip}:{port} en tant que {pseudo}")

        # On lance un thread daemon en arrière-plan pour écouter les messages entrants
        # daemon=True : le thread s'arrête automatiquement quand le programme principal se ferme
        t = threading.Thread(target=self.boucle_reception, daemon=True)
        t.start()  # Démarrage effectif du thread


    # ----------------------------------------------------------
    # Déconnexion
    # ----------------------------------------------------------

    def se_deconnecter(self):
        self.connected = False   # On marque comme déconnecté AVANT de fermer le socket
                                 # pour que la boucle_reception s'arrête proprement
        if self.sock:
            try:
                self.sock.close()  # On ferme le socket réseau (libère la ressource OS)
            except Exception:
                pass               # On ignore les erreurs (le socket était peut-être déjà fermé)
            self.sock = None       # On remet la variable à None
        self.afficher("[INFO] Déconnecté.")
        self.reset_ui()  # On remet l'interface dans son état initial

    def reset_ui(self):
        # Réactive tous les champs et boutons pour permettre une nouvelle connexion
        for w in [self.champ_pseudo, self.champ_ip, self.champ_port]:
            w.config(state="normal")     # Champs de connexion de nouveau éditables
        self.btn_co.config(state="normal")     # Bouton connexion réactivé
        self.btn_deco.config(state="disabled") # Bouton déconnexion désactivé
        self.champ_msg.config(state="disabled") # Champ message désactivé
        self.btn_send.config(state="disabled")  # Bouton envoyer désactivé


    # ----------------------------------------------------------
    # Réception des messages (tourne dans un thread séparé)
    # ----------------------------------------------------------

    def boucle_reception(self):
        while self.connected:  # Tant qu'on est connecté, on écoute indéfiniment
            try:
                payload = recv_frame(self.sock)  # Attente bloquante : ne continue que quand un message arrive

                # None signifie que le serveur a fermé la connexion de son côté
                if payload is None:
                    self.afficher("[INFO] Connexion fermée par le serveur.")
                    break  # On sort de la boucle

                # On décode les bytes en texte UTF-8 puis on parse le JSON
                data = json.loads(payload.decode("utf-8"))

                if data.get("type") == "chat":
                    msg_d=cp.decodage_aes(data['message'][1],data['message'][0], self.cle_priv, data['message'][2])
                    # Message de chat normal : on affiche "expediteur : texte" en bleu
                    self.afficher(f"{data['from']} : {msg_d}", "autre")

                elif data.get("type") == "info":
                    # Message système du serveur (ex: "X a rejoint le salon") en jaune
                    self.afficher(f"[INFO] {data['message']}")

                elif data.get("type") == "keylist":
                    self.cles_publiques = data["keys"]
                    # On supprime notre propre clé de la liste, on n'a pas besoin de la stocker
                    self.cles_publiques.pop(self.username, None)
                    self.afficher(f"[INFO] Liste des clés mise à jour ({len(self.cles_publiques)} connecté(s))")

            except Exception as e:
                if self.connected:    # Si on est encore censé être connecté, c'est une vraie erreur réseau
                    self.afficher(f"[ERREUR] {e}")
                break  # Dans tous les cas on sort de la boucle

        # Quand on sort de la boucle (déconnexion ou erreur), on remet l'UI à jour
        # root.after(0, ...) pour exécuter reset_ui dans le thread principal Tkinter
        self.root.after(0, self.reset_ui)


    # ----------------------------------------------------------
    # Envoi d'un message
    # ----------------------------------------------------------

    def envoyer(self):
        texte = self.champ_msg.get().strip()   # On lit le contenu du champ message
        if not texte or not self.connected:    # Si le champ est vide ou si on n'est pas connecté : on ne fait rien
            return

        if texte == "/quitter":          # Commande spéciale : "/quitter" déclenche une déconnexion propre
            self.se_deconnecter()
            return
        
        if texte == "/clepublique":      # Commande spéciale : "/clepublique" permet de vérifier si les clés publiques sont bonnes lors du developpement
            print(self.cle_pub)
            return

        if texte == "/malistecle":      # Commande spéciale : "/malistecle" permet d'afficher la liste des clés publics du client'
            print(self.cles_publiques)
            return
        
        if texte== "/testlist":
            print(list(self.cles_publiques.values()))
            return
        
        if texte== "/clepriv":
            print(self.cle_priv)
            return
        
        payload= cp.payload(texte, list(self.cles_publiques.values())[0]) #on recupere la cle et on forme le message a envoyer
        print(payload)
        try:
            # On sérialise le message en JSON et on l'envoie au serveur
            send_frame(self.sock, json.dumps({"type": "chat", "message": payload}).encode())
            self.afficher(f"Moi : {texte}", "moi")  # On affiche son propre message en vert
            self.champ_msg.delete(0, tk.END)         # On efface le champ de saisie après envoi
        except Exception as e:
            messagebox.showerror("Erreur envoi", str(e))  # En cas d'erreur réseau, on affiche une alerte
            self.se_deconnecter()                         # Et on force la déconnexion


    # ----------------------------------------------------------
    # Fermeture de la fenêtre
    # ----------------------------------------------------------

    def fermer(self):
        self.se_deconnecter()  # On se déconnecte proprement avant de fermer (libère le socket)
        self.root.destroy()    # On ferme la fenêtre Tkinter et on termine le programme


# ==============================================================
# LANCEMENT
# ==============================================================

if __name__ == "__main__":
    # Ce bloc ne s'exécute que si on lance ce fichier directement
    # (pas si on l'importe comme module depuis un autre fichier)
    root = tk.Tk()        # On crée la fenêtre principale Tkinter
    app  = ClientChat(root) # On instancie notre classe (construit l'UI et génère les clés RSA)
    root.mainloop()        # On lance la boucle événementielle Tkinter : attend les clics, frappes, etc.
                           # Le programme reste ici jusqu'à ce que la fenêtre soit fermée
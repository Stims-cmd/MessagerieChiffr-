# 🔐 Chat TCP Chiffré — Python

Projet de cryptographie appliquée — Chat en temps réel avec chiffrement de bout en bout, implémenté from scratch en Python (sans bibliothèque cryptographique tierce).

---

## 📋 Description

Ce projet implémente un système de messagerie instantanée sécurisée en Python. Les messages transitent sur le réseau de façon **entièrement chiffrée** : même un attaquant qui intercepterait le trafic TCP ne pourrait pas lire le contenu des échanges.

Le système repose sur une architecture **hybride RSA + AES** :
- **RSA** (asymétrique) pour l'échange sécurisé de clés au moment de la connexion
- **AES** (symétrique) pour le chiffrement rapide des messages en temps réel
- **SHA-256** (hachage) pour la vérification d'intégrité de chaque message

Tous les algorithmes ont été implémentés **from scratch** à partir de leurs spécifications mathématiques, sans recours à PyCryptodome, `cryptography`, ou toute autre bibliothèque cryptographique.

---

## 🗂️ Structure du projet

```
Messageriechiffre/
│
├── server.py       # Serveur TCP : gestion des connexions, routage, diffusion des clés
├── client.py       # Client TCP : interface graphique (Tkinter), envoi/réception chiffrée
├── crypto.py       # Algorithmes : RSA, AES, SHA-256, chiffrement/déchiffrement
├── my_AES.py       # Fonctions liées à AES
├── my_RSA.py       # Génération et gestion des paires de clés RSA
└── README.md       # Ce fichier
```

---

## ⚙️ Prérequis

- Python **3.8+**
- Aucune bibliothèque tierce : uniquement la bibliothèque standard Python
  - `socket`, `threading`, `struct`, `json`, `hashlib`, `os`, `base64`, `tkinter`

Vérifier la version Python :
```bash
python --version
```

---

## 🚀 Lancement

### 1. Démarrer le serveur

```bash
python server.py
```

Le serveur écoute par défaut sur `0.0.0.0:5000`. Il accepte plusieurs clients simultanément.

### 2. Démarrer un ou plusieurs clients

```bash
python client.py
```

Une interface graphique s'ouvre. Renseigner :
- **Pseudo** : le nom affiché dans le chat
- **IP** : l'adresse du serveur (ex : `127.0.0.1` pour local)
- **Port** : `5000` par défaut

Cliquer sur **Connexion**. La fenêtre de chat devient active.

### Tester en local (deux clients sur la même machine)

Ouvrir deux terminaux, lancer `python client.py` dans chacun, et se connecter avec des pseudos différents (ex : `Alice` et `Bob`).

---

## 🔑 Fonctionnement du protocole

### Phase 1 — Connexion et échange de clés

```
Client                          Serveur                         Autres clients
  |                               |                                   |
  |-- join {username, pub_key} -->|                                   |
  |                               |-- keylist {Alice: clé, ...} ----->|
  |<----- keylist {Bob: clé} -----|                                   |
```

1. Au démarrage, chaque client génère une **paire de clés RSA** (clé publique + clé privée)
2. À la connexion, le client envoie son pseudo et sa **clé publique** au serveur
3. Le serveur met à jour sa liste et **diffuse la keylist complète** à tous les clients connectés
4. Chaque client dispose ainsi des clés publiques de tous les autres participants

### Phase 2 — Échange de messages chiffrés

```
Expéditeur                                          Destinataire
  |                                                      |
  | 1. Saisie du message en clair                        |
  | 2. Chiffrement AES (clé de session)                  |
  | 3. Chiffrement de la clé AES avec RSA (clé pub dest) |
  | 4. Hachage SHA-256 du message chiffré                |
  |-------- {message_chiffré, clé_chiffrée, hash} ------>|
  |                                                      | 5. Vérif intégrité (SHA-256)
  |                                                      | 6. Déchiffrement clé AES (clé privée RSA)
  |                                                      | 7. Déchiffrement message (AES)
  |                                                      | 8. Affichage en clair
```

### Phase 3 — Déconnexion

Quand un client se déconnecte, le serveur supprime sa clé publique et rediffuse la keylist mise à jour à tous les clients restants.

---

## 🛡️ Algorithmes implémentés

### RSA (dans `keygen.py` et `crypto.py`)
- Génération de deux grands nombres premiers `p` et `q`
- Calcul de `n = p * q` et `φ(n) = (p-1)(q-1)`
- Choix de l'exposant public `e` et calcul de `d` (inverse modulaire)
- Chiffrement : `c = m^e mod n` / Déchiffrement : `m = c^d mod n`

### AES simplifié (dans `crypto.py`)
- Utilisé pour le chiffrement des messages (plus rapide que RSA sur de longs textes)
- Une clé AES aléatoire est générée par message, puis chiffrée avec RSA

### SHA-256 (dans `crypto.py`)
- Hachage du message chiffré avant envoi
- Vérification côté récepteur : si le hash ne correspond pas, le message est rejeté

---

## 📡 Format des trames réseau

Tous les messages utilisent le format **length-prefixed** :

```
┌─────────────────┬─────────────────────────────┐
│  4 octets       │  N octets                   │
│  (taille, BE)   │ (payload JSON encodé UTF-8) │
└─────────────────┴─────────────────────────────┘
```

### Types de messages JSON

| `type`      | Direction          | Contenu                                      |
|-------------|--------------------|----------------------------------------------|
| `join`      | Client → Serveur   | `username`, `public_key`                     |
| `chat`      | Client → Serveur   | `message` (chiffré), `encrypted_key`, `hash` |
| `chat`      | Serveur → Client   | `from`, `message`, `encrypted_key`, `hash`   |
| `keylist`   | Serveur → Client   | `keys` : dict `{pseudo: clé_publique}`       |
| `info`      | Serveur → Client   | `message` (notification système)             |

---

## 🧪 Tests réalisés

| Scénario | Résultat |
|---|---|
| Échange de messages sur localhost | ✅ |
| Connexion de 3 clients simultanés | ✅ |
| Déconnexion brutale (fermeture fenêtre) | ✅ (keylist mise à jour) |
| Messages avec caractères spéciaux (accents, emojis) | ✅ |
| Message intercepté (affiché brut côté réseau) | ✅ illisible |
| Vérification d'intégrité (hash SHA-256) | ✅ |

---

## ⚠️ Failles connues et limites

**Man-in-the-Middle (MITM)**
Le serveur distribue les clés publiques sans les authentifier. Un attaquant contrôlant le serveur pourrait substituer ses propres clés. Une PKI ou un mécanisme de vérification hors-bande serait nécessaire pour y remédier.

**Serveur de confiance implicite**
Le serveur voit passer les messages chiffrés mais connaît aussi à qui chaque message est destiné (métadonnées). Il n'est pas lui-même chiffré.

**Pas de Perfect Forward Secrecy**
Si la clé privée RSA d'un utilisateur est compromise, les sessions passées enregistrées pourraient être déchiffrées. Un échange Diffie-Hellman éphémère résoudrait ce problème.

**Replay attack**
Un message chiffré intercepté pourrait être renvoyé ultérieurement. L'ajout d'un nonce (nombre aléatoire unique par message) ou d'un timestamp dans le hash permettrait de s'en prémunir.

---

## 🔧 Pistes d'amélioration

- Implémenter **Diffie-Hellman** pour un échange de clé sans RSA (et apporter le PFS)
- Ajouter un **nonce** dans chaque message pour contrer les replay attacks
- Authentifier les clés publiques avec une **signature numérique**
- Chiffrer également les **métadonnées** (qui parle à qui, quand)
- Ajouter un **IV (vecteur d'initialisation) aléatoire** par message pour AES

---

## 👥 Auteurs

Projet réalisé avec mon ami [Squarish](https://github.com/squarish2810) dans le cadre du cours de **Cryptographie** de l'école Guardia CS.

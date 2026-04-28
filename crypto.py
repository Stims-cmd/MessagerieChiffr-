import my_RSA as rsa
import my_AES as aes

def encodage_rsa(cle_aes):
    """
    encodage de la clé de chiffrement AES avec la clé RSA
    """

def encodage_aes(message):
    """
    encode le message avec AES
    """

def decodage_rsa(message, cle_rsa):
    """
    decode la clé AES chiffrée par RSA
    """

def decodage_aes(message, cle_aes):
    """
    decode le message chiffré par AES
    """

def recup_cle_rsa():
    """
    genere les clés RSA de l'utilisateur
    """
    temp= rsa.gen_cle()
    cle_public=temp[0]
    cle_privee=temp[1]

    return cle_public, cle_privee
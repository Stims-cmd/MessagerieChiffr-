import my_RSA as rsa
import my_AES as aes
import numpy as np

def encodage_rsa(cle_aes, cle_public):
    """
    encodage de la clé de chiffrement AES avec la clé RSA
    """
    #transformation de la cle AES en un nombre encodable par RSA
    cle_aes= cle_aes.tobytes()  #transformation en bytes
    cle_aes= int.from_bytes(cle_brute, byteorder='big')  #transformation en un entier

    #format cle_public: (e, n)
    cle_encode=pow(cle_aes, cle_public[0], cle_public[1])

    return cle_encode




def encodage_aes(message):
    """
    encode le message avec AES
    """

def decodage_rsa(message, cle_privee):
    """
    decode la clé AES chiffrée par RSA
    """
    #on decode la cle grace a la cle_privee (d, n)
    cle_decode= pow(message, cle_privee[0], cle_privee[1])
    #on retransforme la cle AES en matrice exploitable
    cle_aes= cle_decode.to_bytes(4, byteorder='big')
    cle_aes=np.array(cle_aes)
    cle_aes.reshape(4, 4)
    
    return cle_aes



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
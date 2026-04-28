import secrets as sc
import numpy as np


def cle_msg(message):
    """
    generation de la clé AES et decoupage du message
    """
    taille=calcul_taille(message)
    msg=creation_matrice(taille[0], taille[1], message)
    cle= gen_cle()

    return (cle, msg)


def calcul_taille(message):
    """
    Calcul du nombre de matrice de 4*4 necessaire
    """
    #calcul de la taille du message
    if len(message)%16==0:
        nb=len(message)//16
        reste=0
    else:
        nb=len(message)//16
        reste=len(message)%16
    
    return (nb, reste)


def creation_matrice(nombre, complement, message):
    """
    creation des matrices
    """
    #encodage du message en utf8
    msg_utf8=message.encode('utf-8')
    msg_utf8=list(msg_utf8)

    #initialisation des listes necessaires
    liste_matrice=[]
    matrice_temp=[]

    #creation de chaque matrice de 16 octets
    for k in range(nombre):
        while len(matrice_temp)!=16:
            matrice_temp.append(msg_utf8.pop(0))

        #on passe les listes en matrice numpy
        matrice_temp=np.array(matrice_temp)
        matrice_temp.reshape(4, 4)

        #on ajoute la matrice complete a la liste de matrices
        liste_matrice.append(matrice_temp)
        matrice_temp=[]
    
    #on gere les matrices incompletes
    #si les matrices sont completes, on ajoute une matrice vie pour que l'ordinateur connaisse la fin du message
    if complement==0:
        for i in range(16):
            matrice_temp.append(16)
    else:   #sinon on complete les matrices avec le nombre d'octet vide
        for elt in msg_utf8:
            matrice_temp.append(elt)
        for l in range(16-complement):
            matrice_temp.append(16-complement)
    liste_matrice.append(matrice_temp)
    
    return(liste_matrice)
            

def gen_cle():
    """
    genere une clé aleatoire pour le chiffrement AES
    """
    cle=[]
    #generation de la clé
    for k in range(16):
        cle.append(sc.randbelow(255))
    #transformation de la clé en matrice de 4 par 4
    cle=np.array(cle)
    cle.reshape(4, 4)

    return cle

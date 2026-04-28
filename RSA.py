import secrets as sc 


def gen_cle():
    """
    generation des cles
    """
    #entiers sous la forme (n, phi, e)
    entiers=gen_entier()
    #creation de d
    d= egcd(entiers[2], entiers[1])[1]
    d= d%entiers[1] #verification qu'il soit positif

    #creation des clés
    cle_public=(entiers[2], entiers[0]) #cle_public(e, n)
    cle_privee=(d, entiers[0]) #cle_public(d, n)

    return (cle_public, cle_privee)





def gen_entier():
    """
    generation des entiers necessaires RSA
    """
    p=nb_premiers()
    q=nb_premiers()
    #on verifie que p et q sont differents
    while p==q:
        q=nb_premiers()

    #on cherche E
    phi=(p-1)*(q-1) 
    n = p*q
    e=verif_E(phi)

    return (n, phi, e)
    


def nb_premiers():
    """
    generation des nombres premiers
    """
    while True:
        # generation d'un nombre sur 1024 bits
        nb = sc.randbits(1024) 
        #verification que le nombre est impair et de la bonne taille
        nb |= (1 << 1023) | 1
        # On verifie que le nombre est premier avec le test de Miller-Rabin
        if test_MR(nb, 40):
            return nb


def test_MR(nombre, tours):
    """
    verification que le nombre testé est premier
    """
    #initialisation des variables
    d= nombre-1
    s=0
    #calcul du nombre de divisions possible 
    while d%2==0:
        d= d//2
        s+=1

    for k in range(tours):
        temp= sc.randbelow(nombre-4)+2
        test= pow(temp, d, nombre)

        if test==1 or test==nombre-1:
            continue

        for i in range(s-1):
            test=pow(test, 2, nombre)
            if test == nombre-1:
                break
        else:
            return False
    
    return True


def verif_E(phi):
    """
    Creation de l'exposant public
    """
    e=3
    while pgcd(e, phi)!=1:
        e+=2
    return e
    

def pgcd(a, b):
    """
    calcul du pgcd
    """
    inf, sup=min(a,b), max(a,b)
    while inf != 0:
        sup, inf= inf, sup%inf
    return sup


def egcd(a, b):
    """
    calcul de d
    """
    if a==0:
        return (b, 0, 1)
    g, y, x =egcd(b%a, a)
    return g, x-(b//a)*y, y

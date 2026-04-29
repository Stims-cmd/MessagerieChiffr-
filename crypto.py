import my_RSA as rsa
import my_AES as aes
import numpy as np


def payload(message, cle_public):
    """
    creer le paquet qui sera envoyé
    """
    #on recupere le message et la clé
    cle_aes, msg=encodage_aes(message)
    #on encode la clé AES avec rsa
    cle_aes_chiffre= encodage_rsa(cle_aes, cle_public)
    #on creer le paquet
    for k in range(len(msg)):
        msg[k]=msg[k].flatten().tolist()

    payload=(cle_aes_chiffre, msg)

    return payload



def encodage_rsa(cle_aes, cle_public):
    """
    encodage de la clé de chiffrement AES avec la clé RSA
    """
    #transformation de la cle AES en un nombre encodable par RSA
    cle_aes= cle_aes.tobytes()  #transformation en bytes
    cle_aes= int.from_bytes(cle_aes, byteorder='big')  #transformation en un entier

    #format cle_public: (e, n)
    print(cle_public)
    cle_encode=pow(cle_aes, cle_public[0][0], cle_public[0][1])

    return cle_encode




def encodage_aes(message):
    """
    encode le message avec AES
    """
    msg_encode=[]
    #on decoupe le message et on genere la cle
    cle, msg= aes.cle_msg(message)
    #substitution des octets
    msg=substitution(msg, True)

    cle_temp=cle
    round =0
    for i in range(4):
        for k in range(len(msg)):
            msg[k]=msg[k]^cle_temp
        round+=1
        cle_temp=aes.mod_key(cle_temp, round)

    return (cle, msg)




def decodage_rsa(message, cle_privee):
    """
    decode la clé AES chiffrée par RSA
    """
    #on decode la cle grace a la cle_privee (d, n)
    cle_decode= pow(message, cle_privee[0][0], cle_privee[0][1])
    #on retransforme la cle AES en matrice exploitable
    cle_aes= cle_decode.to_bytes(4, byteorder='big')
    cle_aes=np.array(cle_aes)
    cle_aes=cle_aes.reshape(4, 4)
    
    return cle_aes


def decodage_aes(message, cle_aes):
    """
    decode le message chiffré par AES
    """
    #on decode la cle et on recupere ses variantes
    cle=decodage_rsa(cle_aes)
    liste_cle=[cle]
    for k in range(1, 4):
        liste_cle.append(aes.mod_key(cle, k))
    #on decode le message
    msg_decode=message
    for k in range(1, 5):
        for elt in msg_decode:
            elt=elt^liste_cle[-k]

    #on applique la substitution inverse
    msg_decode=substitution(msg_decode, False)

    #on enleve le vide et on rend le message lisible
    msg=str(aes.traduction(msg_decode))

    return msg



def recup_cle_rsa():
    """
    genere les clés RSA de l'utilisateur
    """
    temp= rsa.gen_cle()
    cle_public=temp[0]
    cle_privee=temp[1]

    return cle_public, cle_privee

def substitution(message, choix):
    """
    substitu les octets un a un dans le message
    """
    #sbox necessaires pour la substitution
    sbox={0: 21, 1: 26, 2: 216, 3: 111, 4: 3, 5: 195, 6: 131, 7: 163, 8: 106, 9: 47, 10: 82, 11: 119, 12: 144, 13: 79, 14: 1, 15: 168, 16: 19, 17: 229, 18: 247, 19: 139, 20: 33, 21: 91, 22: 39, 23: 197, 24: 232, 25: 41, 26: 14, 27: 231, 28: 206, 29: 128, 30: 147, 31: 108, 32: 86, 33: 255, 34: 170, 35: 63, 36: 175, 37: 199, 38: 136, 39: 243, 40: 73, 41: 250, 42: 5, 43: 9, 44: 13, 45: 110, 46: 28, 47: 15, 48: 70, 49: 180, 50: 22, 51: 72, 52: 188, 53: 127, 54: 98, 55: 84, 56: 54, 57: 49, 58: 179, 59: 169, 60: 133, 61: 253, 62: 183, 63: 55, 64: 161, 65: 225, 66: 120, 67: 97, 68: 74, 69: 240, 70: 45, 71: 69, 72: 186, 73: 249, 74: 162, 75: 95, 76: 248, 77: 246, 78: 193, 79: 202, 80: 62, 81: 166, 82: 173, 83: 156, 84: 148, 85: 52, 86: 196, 87: 81, 88: 121, 89: 92, 90: 177, 91: 6, 92: 93, 93: 48, 94: 17, 95: 143, 96: 145, 97: 154, 98: 135, 99: 89, 100: 60, 101: 25, 102: 140, 103: 56, 104: 217, 105: 4, 106: 172, 107: 68, 108: 150, 109: 107, 110: 66, 111: 153, 112: 219, 113: 59, 114: 7, 115: 201, 116: 99, 117: 215, 118: 210, 119: 8, 120: 132, 121: 181, 122: 78, 123: 204, 124: 198, 125: 71, 126: 137, 127: 103, 128: 116, 129: 220, 130: 235, 131: 12, 132: 42, 133: 105, 134: 165, 135: 184, 136: 222, 137: 208, 138: 227, 139: 185, 140: 192, 141: 38, 142: 32, 143: 104, 144: 20, 145: 178, 146: 10, 147: 182, 148: 31, 149: 207, 150: 245, 151: 87, 152: 254, 153: 160, 154: 129, 155: 34, 156: 57, 157: 24, 158: 187, 159: 239, 160: 190, 161: 30, 162: 194, 163: 252, 164: 125, 165: 115, 166: 146, 167: 157, 168: 2, 169: 83, 170: 80, 171: 46, 172: 226, 173: 138, 174: 124, 175: 251, 176: 223, 177: 27, 178: 40, 179: 11, 180: 159, 181: 141, 182: 101, 183: 189, 184: 94, 185: 230, 186: 109, 187: 221, 188: 102, 189: 117, 190: 238, 191: 214, 192: 236, 193: 203, 194: 218, 195: 53, 196: 242, 197: 90, 198: 176, 199: 174, 200: 23, 201: 212, 202: 237, 203: 244, 204: 152, 205: 158, 206: 209, 207: 123, 208: 0, 209: 134, 210: 75, 211: 58, 212: 118, 213: 100, 214: 164, 215: 88, 216: 171, 217: 142, 218: 43, 219: 16, 220: 234, 221: 228, 222: 65, 223: 77, 224: 36, 225: 112, 226: 241, 227: 50, 228: 113, 229: 18, 230: 114, 231: 37, 232: 211, 233: 200, 234: 213, 235: 67, 236: 61, 237: 44, 238: 29, 239: 96, 240: 205, 241: 224, 242: 151, 243: 85, 244: 64, 245: 51, 246: 149, 247: 233, 248: 76, 249: 126, 250: 191, 251: 122, 252: 155, 253: 130, 254: 35, 255: 167}
    sbox_inv={0: 208, 1: 14, 2: 168, 3: 4, 4: 105, 5: 42, 6: 91, 7: 114, 8: 119, 9: 43, 10: 146, 11: 179, 12: 131, 13: 44, 14: 26, 15: 47, 16: 219, 17: 94, 18: 229, 19: 16, 20: 144, 21: 0, 22: 50, 23: 200, 24: 157, 25: 101, 26: 1, 27: 177, 28: 46, 29: 238, 30: 161, 31: 148, 32: 142, 33: 20, 34: 155, 35: 254, 36: 224, 37: 231, 38: 141, 39: 22, 40: 178, 41: 25, 42: 132, 43: 218, 44: 237, 45: 70, 46: 171, 47: 9, 48: 93, 49: 57, 50: 227, 51: 245, 52: 85, 53: 195, 54: 56, 55: 63, 56: 103, 57: 156, 58: 211, 59: 113, 60: 100, 61: 236, 62: 80, 63: 35, 64: 244, 65: 222, 66: 110, 67: 235, 68: 107, 69: 71, 70: 48, 71: 125, 72: 51, 73: 40, 74: 68, 75: 210, 76: 248, 77: 223, 78: 122, 79: 13, 80: 170, 81: 87, 82: 10, 83: 169, 84: 55, 85: 243, 86: 32, 87: 151, 88: 215, 89: 99, 90: 197, 91: 21, 92: 89, 93: 92, 94: 184, 95: 75, 96: 239, 97: 67, 98: 54, 99: 116, 100: 213, 101: 182, 102: 188, 103: 127, 104: 143, 105: 133, 106: 8, 107: 109, 108: 31, 109: 186, 110: 45, 111: 3, 112: 225, 113: 228, 114: 230, 115: 165, 116: 128, 117: 189, 118: 212, 119: 11, 120: 66, 121: 88, 122: 251, 123: 207, 124: 174, 125: 164, 126: 249, 127: 53, 128: 29, 129: 154, 130: 253, 131: 6, 132: 120, 133: 60, 134: 209, 135: 98, 136: 38, 137: 126, 138: 173, 139: 19, 140: 102, 141: 181, 142: 217, 143: 95, 144: 12, 145: 96, 146: 166, 147: 30, 148: 84, 149: 246, 150: 108, 151: 242, 152: 204, 153: 111, 154: 97, 155: 252, 156: 83, 157: 167, 158: 205, 159: 180, 160: 153, 161: 64, 162: 74, 163: 7, 164: 214, 165: 134, 166: 81, 167: 255, 168: 15, 169: 59, 170: 34, 171: 216, 172: 106, 173: 82, 174: 199, 175: 36, 176: 198, 177: 90, 178: 145, 179: 58, 180: 49, 181: 121, 182: 147, 183: 62, 184: 135, 185: 139, 186: 72, 187: 158, 188: 52, 189: 183, 190: 160, 191: 250, 192: 140, 193: 78, 194: 162, 195: 5, 196: 86, 197: 23, 198: 124, 199: 37, 200: 233, 201: 115, 202: 79, 203: 193, 204: 123, 205: 240, 206: 28, 207: 149, 208: 137, 209: 206, 210: 118, 211: 232, 212: 201, 213: 234, 214: 191, 215: 117, 216: 2, 217: 104, 218: 194, 219: 112, 220: 129, 221: 187, 222: 136, 223: 176, 224: 241, 225: 65, 226: 172, 227: 138, 228: 221, 229: 17, 230: 185, 231: 27, 232: 24, 233: 247, 234: 220, 235: 130, 236: 192, 237: 202, 238: 190, 239: 159, 240: 69, 241: 226, 242: 196, 243: 39, 244: 203, 245: 150, 246: 77, 247: 18, 248: 76, 249: 73, 250: 41, 251: 175, 252: 163, 253: 61, 254: 152, 255: 33}
    print(message)
    #On transforme la matrice en list
    for k in range(len(message)):
        message[k]=message[k].flatten().tolist()
    #on substitu on en fonction de choix (true ou false)
    if choix is True:
        for elt in message:
            for i in range(len(elt)):
                elt[i]=sbox[elt[i]]
    else:
        for elt in message:
            for i in range(len(elt)):
                elt[i]=sbox_inv[elt[i]]
    
    msg_sub=[]
    for k in range(len(message)):
        message[k]=np.array(message[k])
        message[k]=message[k].reshape(4, 4)
        msg_sub.append(message[k])
    
    return msg_sub

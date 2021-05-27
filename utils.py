import socket
import struct
import json

def get_config():
    json_data = {}
    with open('config.json', 'r') as f:
        json_data = json.load(f)
    return json_data

multi = get_config()['multicast']
ip_grupo = str(multi['ip_grupo'])
porta = multi['porta']
grupo_multicast = (ip_grupo, porta)

def cria_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    group = socket.inet_aton(ip_grupo)
    membership = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    sock.bind(('', porta))
    return sock

def aguarda_mensagem(sock, codigos):
    while True:
        mensagem, endereco = sock.recvfrom(1024)
        if mensagem[0:2] in codigos:
            return mensagem[0:2], mensagem[2:]

def envia(sock, mensagem):
    sock.sendto(mensagem, grupo_multicast)

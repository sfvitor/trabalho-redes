import socket
import sys

from utils import get_config, cria_socket_multicast, aguarda_mensagem, envia

config = get_config()
codigo_mensagens = config['codigo_mensagens']
codigos_orquestrador = codigo_mensagens['orquestrador']
codigos_cliente = codigo_mensagens['cliente']
codigos_servidor = codigo_mensagens['servidor']

ip_multicast, porta_multicast = sys.argv[1].split(':')
porta_multicast = int(porta_multicast)
grupo_multicast = (ip_multicast, porta_multicast)
ip_tcp, porta_tcp = sys.argv[2].split(':')
porta_tcp = int(porta_tcp)

sock = cria_socket_multicast(ip_multicast, porta_multicast)

def espera_orquestrador():
    codigo, mensagem = aguarda_mensagem(sock, (
        codigos_orquestrador['comecar'],
        codigos_orquestrador['shutdown']
    ))
    return (codigo == codigos_orquestrador['comecar']) and mensagem

def espera_servidor():
    aguarda_mensagem(sock, (codigos_servidor['comecar'],))

def comeca_teste(opcoes, sockCliente):
    tamanho_mensagem = 2**int(opcoes[0])
    repeticoes = 2**int(opcoes[1])
    for i in range(repeticoes):
        print 'Testando repeticao %d/%d'%(i+1, repeticoes)
        # inicia timer
        mensagem = 'a'*tamanho_mensagem
        sockCliente.send(codigos_cliente['teste'] + mensagem)
        retorno = sockCliente.recv(tamanho_mensagem+2)
        # finaliza timer
        print 'Servidor respondeu: %s'%retorno[2:]
        # salva tempo

def termina_teste():
    envia(sock, codigos_cliente['terminar'], grupo_multicast)

def novo_socket_tcp():
    sockCliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockCliente.connect((ip_tcp, porta_tcp))
    return sockCliente

while True:
    print 'Cliente aguardando orquestrador para comecar novo teste...'
    opcoes = espera_orquestrador()
    if not opcoes:
        envia(sock, codigos_cliente['terminar'], grupo_multicast)
        print 'Orquestrador encerrou os testes. Fechando conexao...'
        break
    envia(sock, codigos_cliente['comecar'], grupo_multicast)
    print 'opcoes recebidas:', opcoes
    espera_servidor()
    sockCliente = novo_socket_tcp()
    print 'recebido ack do servidor'
    comeca_teste(opcoes, sockCliente)
    sockCliente.close()
    termina_teste()

sock.close()

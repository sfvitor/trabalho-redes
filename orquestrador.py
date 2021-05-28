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

sock = cria_socket_multicast(ip_multicast, porta_multicast)

def envia_configuracoes(comando):
    envia(sock, codigos_orquestrador['comecar']+comando, grupo_multicast)

def espera_cliente_e_servidor_comecarem():
    for i in range(2):
        aguarda_mensagem(sock, (
            codigos_cliente['comecar'],
            codigos_servidor['comecar']
        ))

def espera_cliente_e_servidor_terminarem():
    for i in range(2):
        aguarda_mensagem(sock, (
            codigos_cliente['terminar'],
            codigos_servidor['terminar']
        ))

def encerra_cliente_e_servidor():
    envia(sock, codigos_orquestrador['shutdown'], grupo_multicast)

def principal():
    repeticoes = int(raw_input('Digite a quantidade de repeticoes:'))

    while True:
        comando = ''
        print 'Digite o tamanho da mensagem'
        print 'Ou digite shutdown para encerrar o cliente e o servidor'
        while True:
            comando = raw_input()
            if comando == 'shutdown':
                encerra_cliente_e_servidor()
                return
            try:
                tamanho_mensagem = int(comando)
                comando = '%d%d'%(tamanho_mensagem, repeticoes)
                break
            except:
                print 'Valores incorretos, tente novamente'
        print 'Enviando configuracoes para novo teste...'
        envia_configuracoes(comando)
        espera_cliente_e_servidor_comecarem()
        print 'Aguardando testes terminarem...'
        espera_cliente_e_servidor_terminarem()

        

principal()
sock.close()

import socket
import sys
import time
import struct

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
        tuple(codigos_orquestrador['comecar']),
        tuple(codigos_orquestrador['shutdown'])
    ))
    return (codigo == tuple(codigos_orquestrador['comecar'])) and mensagem

def espera_servidor():
    aguarda_mensagem(sock, (tuple(codigos_servidor['comecar']),))

def comeca_teste(opcoes, sockCliente):
    tamanho_mensagem = 2**opcoes[0]
    repeticoes = 2**opcoes[1]
    tempos = []
    for i in range(repeticoes):
        print 'Testando repeticao %d/%d'%(i+1, repeticoes)
        itens_mensagem = codigos_cliente['teste'] + [1]*tamanho_mensagem
        mensagem = struct.pack(
            '%db'%(2+tamanho_mensagem),
            *itens_mensagem
        )
        # inicia timer
        inicio = time.time()
        sockCliente.send(mensagem)
        retorno_byte = ''
        while len(retorno_byte)-2 < tamanho_mensagem:
            tamanho_retorno = 2+tamanho_mensagem-len(retorno_byte)
            retorno_byte += sockCliente.recv(tamanho_retorno)
        # finaliza timer
        tempos.append((time.time() - inicio)*1000)
        print 'Servidor respondeu. Tamanho:', len(retorno_byte)-2
    return tempos

def termina_teste():
    envia(sock, tuple(codigos_cliente['terminar']), grupo_multicast)

def novo_socket_tcp():
    sockCliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockCliente.connect((ip_tcp, porta_tcp))
    return sockCliente

def calcula_desvio(media, tempos):
    return (sum([(t-media)**2 for t in tempos])/len(tempos))**0.5

grafico = {}
repeticoes = 0

while True:
    print 'Cliente aguardando orquestrador para comecar novo teste...'
    opcoes = espera_orquestrador()
    if not opcoes:
        envia(sock, tuple(codigos_cliente['terminar']), grupo_multicast)
        print 'Orquestrador encerrou os testes. Fechando conexao...'
        break
    envia(sock, tuple(codigos_cliente['comecar']), grupo_multicast)
    print 'opcoes recebidas:', opcoes
    repeticoes = 2**opcoes[1]
    espera_servidor()
    sockCliente = novo_socket_tcp()
    print 'recebido ack do servidor'
    tempos = comeca_teste(opcoes, sockCliente)
    media = sum(tempos)/len(tempos)
    desvio = calcula_desvio(media, tempos)
    grafico[2**opcoes[0]] = {
        'media': media,
        'desvio': desvio
    }
    sockCliente.close()
    termina_teste()

sock.close()

grafico_keys = sorted(grafico.keys())
linha_tamanhos = 'TCP/1  ' + ' '.join(['%10s'%('%d'%k) for k in grafico_keys])
linha_medias =   'MED    ' + ' '.join(['%10s'%('%.4f'%grafico[k]['media']) for k in grafico_keys])
linha_desvios =  'DVP    ' + ' '.join(['%10s'%('%.4f'%grafico[k]['desvio']) for k in grafico_keys])

with open('resultados.txt', 'w') as f:
    f.write('Observacao: medias e desvios em milissegundos\n')
    f.write('Repeticoes: %d\n'%repeticoes)
    f.write('%s\n'%linha_tamanhos)
    f.write('%s\n'%linha_medias)
    f.write(linha_desvios)

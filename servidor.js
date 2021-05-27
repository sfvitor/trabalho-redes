const config = require('./config.json');
const {
    orquestrador: codigosOrquestrador,
    cliente: codigosCliente,
    servidor: codigosServidor,
} = config.codigo_mensagens;

const dgram = require('dgram');
const net = require('net');
const { exit } = require('process');
const servidorMulticast = dgram.createSocket('udp4');

const [ipMulticast, portaMulticast] = process.argv[2].split(':');
const [ipTCP, portaTCP] = process.argv[3].split(':');
const host = '0.0.0.0';
// const host = '192.168.0.172';

servidorMulticast.on('listening', function () {
    console.log('Servidor aguardando orquestrador para comecar novo teste...');
    servidorMulticast.addMembership(ipMulticast, host);
});

function separaMensagem(mensagem) {
    const codigo = mensagem.substr(0, 2);
    const opcoes = mensagem.substr(2);
    return [codigo, opcoes];
}

function envia(mensagem) {
    servidorMulticast.send(mensagem, 0, mensagem.length, parseInt(portaMulticast), ipMulticast);
}

let tamanhoMensagem, repeticoes;

servidorMulticast.on('message', function (mensagemRemota) {   
    const [codigo, mensagem] = separaMensagem(mensagemRemota.toString());
    if (codigo === codigosOrquestrador.comecar) {
        tamanhoMensagem = 2**parseInt(mensagem[0]);
        repeticoes = 2**parseInt(mensagem[1]);
        console.log(`recebido: tamanho ${tamanhoMensagem} repeticoes ${repeticoes}`);
        envia(codigosServidor.comecar);
        console.log(`enviado ack para comecar`);
        return;
    }
    if (codigo === codigosCliente.teste) {
        console.log(`recebida mensagem de teste: ${mensagem}`);
        envia(codigosServidor.teste + mensagem);
        console.log(`feito o echo da mensagem`);
        repeticoes--;
        if (repeticoes === 0) {
            console.log('repeticoes acabaram');
            envia(codigosServidor.terminar);
            console.log('enviado ack de termino');
        }
        return;
    }
    if (codigo === codigosOrquestrador.shutdown) {
        console.log('Orquestrador encerrou os testes. Fechando conexao...');
        servidorMulticast.close();
        exit(0);
    }
});

servidorMulticast.bind(parseInt(portaMulticast), host);

const servidorTCP = net.createServer(function (socket) {
    socket.addListener('data', function (data) {
        const response = data.toString();
        socket.write(response);
        repeticoes--;
        if (repeticoes === 0) {
            console.log('repeticoes acabaram');
            envia(codigosServidor.terminar);
            console.log('enviado ack de termino');
            socket.end();
        }
    });
});

servidorTCP.listen(parseInt(portaTCP), ipTCP);

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

const mensagemServidorEsperando = 'Servidor aguardando orquestrador para comecar novo teste...';

servidorMulticast.on('listening', function () {
    console.log(mensagemServidorEsperando);
    servidorMulticast.addMembership(ipMulticast, host);
});

function pegaItensMensagem(mensagem) {
    return Buffer.from(mensagem).toJSON().data;
}

function separaMensagem(itensMensagem) {
    const codigo = itensMensagem.slice(0, 2);
    const opcoes = itensMensagem.slice(2);
    return [codigo, opcoes];
}

function envia(itensMensagem) {
    const mensagem = Buffer.from(itensMensagem).toString();
    servidorMulticast.send(mensagem, 0, mensagem.length, parseInt(portaMulticast), ipMulticast);
}

let tamanhoMensagem, repeticoes, clienteTerminou;

servidorMulticast.on('message', function (mensagemRemota) {   
    const [codigo, mensagem] = separaMensagem(pegaItensMensagem(mensagemRemota));
    if (codigo.toString() === codigosOrquestrador.comecar.toString()) {
        clienteTerminou = false;
        tamanhoMensagem = 2**mensagem[0];
        repeticoes = 2**mensagem[1];
        console.log(`recebido: tamanho ${tamanhoMensagem} repeticoes ${repeticoes}`);
        envia(codigosServidor.comecar);
        console.log(`enviado ack para comecar`);
        return;
    }
    if (codigo.toString() === codigosCliente.terminar.toString()) {
        clienteTerminou = true;
        return;
    }
    if (codigo.toString() === codigosOrquestrador.shutdown.toString()) {
        console.log('Orquestrador encerrou os testes. Fechando conexao...');
        servidorMulticast.close();
        exit(0);
    }
});

servidorMulticast.bind(parseInt(portaMulticast), host);

let mensagemCompleta = [];

const servidorTCP = net.createServer(function (socket) {
    socket.addListener('data', function (data) {
        const itensMensagem = pegaItensMensagem(data);
        if (mensagemCompleta.length > 0) {
            mensagemCompleta = mensagemCompleta.concat(itensMensagem);
            if (mensagemCompleta.length < tamanhoMensagem) {
                return;
            }
        }
        else {
            [_, mensagemCompleta] = separaMensagem(itensMensagem);
            if (mensagemCompleta.length < tamanhoMensagem) {
                return;
            }
        }
        console.log(`recebida mensagem de teste. Tamanho: ${mensagemCompleta.length}`);
        const itensResposta = codigosServidor.teste.concat(mensagemCompleta);
        socket.write(Buffer.from(itensResposta).toString());
        console.log(`feito o echo da mensagem`);
        repeticoes--;
        if (repeticoes === 0) {
            console.log('repeticoes acabaram');
            envia(codigosServidor.terminar);
            console.log('enviado ack de termino');
            // console.log('esperando cliente terminar');
            // while (!clienteTerminou) {}
            // socket.end();
            console.log(mensagemServidorEsperando);
        }
        mensagemCompleta = [];
    });
});

servidorTCP.listen(parseInt(portaTCP), ipTCP);

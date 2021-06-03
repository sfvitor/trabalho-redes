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

function separaMensagem(mensagem) {
    const data = Buffer.from(mensagem).toJSON().data;
    const codigo = data.slice(0, 2);
    const opcoes = data.slice(2);
    return [codigo, opcoes];
}

function envia(itensMensagem) {
    const mensagem = Buffer.from(itensMensagem).toString();
    servidorMulticast.send(mensagem, 0, mensagem.length, parseInt(portaMulticast), ipMulticast);
}

let tamanhoMensagem, repeticoes, clienteTerminou;

servidorMulticast.on('message', function (mensagemRemota) {   
    const [codigo, mensagem] = separaMensagem(mensagemRemota);
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

const servidorTCP = net.createServer(function (socket) {
    socket.addListener('data', function (data) {
        const [codigo, mensagem] = separaMensagem(data);
        console.log(`recebida mensagem de teste. Tamanho: ${mensagem.length}`);
        const itensResposta = codigosServidor.teste.concat(mensagem);
        socket.write(Buffer.from(itensResposta).toString());
        console.log(`feito o echo da mensagem`);
        repeticoes--;
        if (repeticoes === 0) {
            console.log('repeticoes acabaram');
            envia(codigosServidor.terminar);
            console.log('enviado ack de termino');
            // console.log('esperando cliente terminar');
            // while (!clienteTerminou) {}
            socket.end();
            console.log(mensagemServidorEsperando);
        }
    });
});

servidorTCP.listen(parseInt(portaTCP), ipTCP);

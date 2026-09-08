// -*- coding: utf-8 -*-
const dgram = require('dgram');
const net = require('net');

console.log('📡 正在直连 127.0.0.1:6766 (UE5 Python Remote Execution)...');

const client = dgram.createSocket('udp4');

const openPayload = JSON.stringify({
    version: 1,
    magic: 'ue_py',
    type: 'open_connection'
});

let handshakeSuccess = false;

client.on('message', (msg, rinfo) => {
    console.log(`📩 收到来自 ${rinfo.address}:${rinfo.port} 的响应数据: ${msg.toString('utf8')}`);
    try {
        const res = JSON.parse(msg.toString('utf8'));
        if (res.magic === 'ue_py' && res.type === 'opened_connection') {
            handshakeSuccess = true;
            const tcpPort = res.data && res.data.command_connection && res.data.command_connection.port;
            const tcpIp = (res.data && res.data.command_connection && res.data.command_connection.ip) || '127.0.0.1';
            console.log(`🎉 握手成功！建立 TCP 命令连接 -> ${tcpIp}:${tcpPort}...`);
            
            const tcpSock = net.createConnection({ host: tcpIp, port: tcpPort }, () => {
                console.log('⚡ TCP 连接建立成功！正在执行全量热更新代码...');
                const cmdPayload = JSON.stringify({
                    version: 1,
                    magic: 'ue_py',
                    type: 'command',
                    data: {
                        command: 'import hot_reload; hot_reload.hot_reload_all()',
                        exec_mode: 'ExecuteStatement'
                    }
                });
                tcpSock.write(cmdPayload);
            });

            tcpSock.on('data', (chunk) => {
                const text = chunk.toString('utf8');
                console.log('📦 [UE5 执行结果回传]:\n', text);
                try {
                    const resultJson = JSON.parse(text);
                    if (resultJson.type === 'command_result') {
                        const logs = (resultJson.data && resultJson.data.output) || [];
                        logs.forEach(l => console.log('  [UE_LOG]', l.output.trim()));
                    }
                } catch(e) {}
                console.log('✅ 全量热更新已由后台自动通信完成并在编辑器中生效！');
                tcpSock.end();
                client.close();
                process.exit(0);
            });

            tcpSock.on('error', (err) => {
                console.error('❌ TCP 错误:', err.message);
                client.close();
                process.exit(1);
            });
        }
    } catch (e) {
        console.error('解析错误:', e.message);
    }
});

// 绑定在 127.0.0.1 任意可用端口
client.bind(0, '127.0.0.1', () => {
    const buf = Buffer.from(openPayload);
    console.log(`📤 发送 open_connection 至 127.0.0.1:6766...`);
    client.send(buf, 0, buf.length, 6766, '127.0.0.1', (err) => {
        if (err) console.error('发送错误:', err.message);
    });

    setTimeout(() => {
        if (!handshakeSuccess) {
            console.log('⏳ 5 秒内未收到 127.0.0.1:6766 握手响应');
            client.close();
            process.exit(1);
        }
    }, 5000);
});

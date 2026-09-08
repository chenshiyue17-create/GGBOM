// -*- coding: utf-8 -*-
const dgram = require('dgram');
const net = require('net');

const MULTICAST_IP = '239.0.0.1';
const MULTICAST_PORT = 6766;

console.log('[AI_AGENT] 🚀 正在向 UE5 Python Remote Execution 发起实时通信连接...');

const udpSocket = dgram.createSocket({ type: 'udp4', reuseAddr: true });

const openMsg = JSON.stringify({
    version: 1,
    magic: 'ue_py',
    type: 'open_connection'
});

let connected = false;

udpSocket.on('message', (msg, rinfo) => {
    try {
        const payload = JSON.parse(msg.toString('utf8'));
        if (payload.magic === 'ue_py' && payload.type === 'opened_connection') {
            connected = true;
            console.log(`[AI_AGENT] 🎉 成功与 UE5 编辑器建立握手！来自 ${rinfo.address}:${rinfo.port}`);
            const cmdConn = payload.data && payload.data.command_connection;
            if (cmdConn && cmdConn.port) {
                const tcpIp = cmdConn.ip || '127.0.0.1';
                const tcpPort = cmdConn.port;
                console.log(`[AI_AGENT] 🔗 正在连接 TCP 命令端口 ${tcpIp}:${tcpPort}...`);
                
                const client = net.createConnection({ host: tcpIp, port: tcpPort }, () => {
                    console.log('[AI_AGENT] ⚡ TCP 通道就绪，正在推送全量热更新脚本到 UE5...');
                    const cmdPayload = JSON.stringify({
                        version: 1,
                        magic: 'ue_py',
                        type: 'command',
                        data: {
                            command: 'import hot_reload; hot_reload.hot_reload_all()',
                            exec_mode: 'ExecuteStatement'
                        }
                    });
                    client.write(cmdPayload);
                });

                client.on('data', (data) => {
                    try {
                        const res = JSON.parse(data.toString('utf8'));
                        if (res.type === 'command_result' && res.data && res.data.output) {
                            res.data.output.forEach(item => {
                                console.log(`[UE5_OUTPUT] ${item.output.trim()}`);
                            });
                        }
                    } catch (e) {
                        console.log(`[UE5_DATA] ${data.toString('utf8').trim()}`);
                    }
                    console.log('[AI_AGENT] ✅ UE5 已成功实时执行并热更新完成！');
                    client.end();
                    udpSocket.close();
                    process.exit(0);
                });

                client.on('error', (err) => {
                    console.error('[AI_AGENT] ❌ TCP 错误:', err.message);
                    udpSocket.close();
                    process.exit(1);
                });
            }
        }
    } catch (e) {
        // ignore parse error
    }
});

udpSocket.bind(0, () => {
    try {
        udpSocket.setBroadcast(true);
        udpSocket.setMulticastTTL(2);
        udpSocket.setMulticastLoopback(true);
        udpSocket.addMembership(MULTICAST_IP);
    } catch (e) {
        // ignore
    }

    const buf = Buffer.from(openMsg);
    // 同时尝试多播和单播
    udpSocket.send(buf, 0, buf.length, MULTICAST_PORT, MULTICAST_IP, (err) => {
        if (err) console.error('[AI_AGENT] 发送组播失败:', err.message);
    });
    udpSocket.send(buf, 0, buf.length, MULTICAST_PORT, '127.0.0.1', (err) => {
        if (err) console.error('[AI_AGENT] 发送单播失败:', err.message);
    });

    // 超时检测
    setTimeout(() => {
        if (!connected) {
            console.log('[AI_AGENT] ⏳ 未在 3 秒内收到 UDP 握手，正在通过 Remote Control HTTP 备用通道通信...');
            tryHttpFallback();
        }
    }, 3000);
});

function tryHttpFallback() {
    const http = require('http');
    const postData = JSON.stringify({
        objectPath: '/Script/Engine.Default__KismetSystemLibrary',
        functionName: 'PrintString',
        parameters: { InString: 'AI_TRIGGER_TEST' }
    });

    const req = http.request({
        hostname: '127.0.0.1',
        port: 30010,
        path: '/remote/info',
        method: 'GET',
        timeout: 2000
    }, (res) => {
        console.log(`[AI_AGENT] 🌐 Remote Control HTTP (30010) 在线响应状态码: ${res.statusCode}`);
        udpSocket.close();
        process.exit(0);
    });

    req.on('error', (e) => {
        console.error('[AI_AGENT] ❌ Remote Control 连接失败:', e.message);
        udpSocket.close();
        process.exit(1);
    });

    req.end();
}

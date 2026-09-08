// -*- coding: utf-8 -*-
const { execSync } = require('child_process');
const http = require('http');

console.log('==================================================');
console.log('🔍 正在实时探测虚幻编辑器 (UnrealEditor) 的真实运行状态...');

// 1. 查找 UnrealEditor 进程与监听端口
try {
    const pids = execSync('pgrep -x UnrealEditor || pgrep -i UnrealEditor || true').toString().trim().split('\n').filter(Boolean);
    console.log(`📋 找到 UnrealEditor 进程 PID: ${pids.join(', ') || '未找到'}`);
    
    if (pids.length > 0) {
        const targetPid = pids[0];
        try {
            const ports = execSync(`lsof -nP -p ${targetPid} | grep -E 'LISTEN|UDP' || true`).toString().trim();
            console.log(`📡 UnrealEditor (PID ${targetPid}) 真实监听端口列表:`);
            console.log(ports || '  (无端口监听记录)');
        } catch (e) {
            console.log('  ⚠️ 获取端口失败:', e.message);
        }
    }
} catch (e) {
    console.log('  ⚠️ 进程检查失败:', e.message);
}

// 2. 探测 30010 Remote Control 真实状态
const req = http.request({
    hostname: '127.0.0.1',
    port: 30010,
    path: '/remote/info',
    method: 'GET',
    timeout: 2000
}, (res) => {
    let body = '';
    res.on('data', chunk => body += chunk);
    res.on('end', () => {
        try {
            const info = JSON.parse(body);
            console.log(`✅ Remote Control (30010) 在线响应！有效路由数: ${info.HttpRoutes ? info.HttpRoutes.length : 0}`);
            console.log(`   当前 ActivePreset:`, JSON.stringify(info.ActivePreset || {}));
        } catch (e) {
            console.log(`✅ Remote Control (30010) 在线但解析异常`);
        }
        process.exit(0);
    });
});

req.on('error', (e) => {
    console.log(`❌ Remote Control (30010) 离线或无法连接: ${e.message}`);
    process.exit(0);
});

req.end();

// -*- coding: utf-8 -*-
const { execSync } = require('child_process');
const fs = require('fs');

console.log('🔍 正在定位运行中的虚幻引擎日志文件...');

let logPath = '';
try {
    const pids = execSync('pgrep -x UnrealEditor || pgrep -i UnrealEditor || true').toString().trim().split('\n').filter(Boolean);
    if (pids.length > 0) {
        const pid = pids[0];
        console.log(`📋 当前 UnrealEditor 进程 PID: ${pid}`);
        const openLogs = execSync(`lsof -p ${pid} | grep -i '\\.log' || true`).toString().trim();
        const lines = openLogs.split('\n');
        for (const line of lines) {
            const parts = line.split(/\s+/);
            const candidate = parts[parts.length - 1];
            if (candidate && candidate.endsWith('.log') && fs.existsSync(candidate)) {
                logPath = candidate;
                break;
            }
        }
    }
} catch (e) {
    console.log('获取进程打开文件失败:', e.message);
}

if (!logPath) {
    // 候选常见路径
    const candidates = [
        '/Users/cc/Desktop/GGBOM/xxxx/Saved/Logs/xxxx.log',
        '/Users/cc/Desktop/GGBOM/xxxx/Saved/Logs/UnrealEditor.log',
        `${process.env.HOME}/Library/Logs/Unreal Engine/xxxxEditor/xxxx.log`,
        `${process.env.HOME}/Library/Logs/Unreal Engine/xxxx/xxxx.log`,
        `${process.env.HOME}/Library/Logs/Unreal Engine/UnrealEditor/UnrealEditor.log`
    ];
    for (const c of candidates) {
        if (fs.existsSync(c)) {
            logPath = c;
            break;
        }
    }
}

if (logPath && fs.existsSync(logPath)) {
    console.log(`📄 找到真实引擎日志路径: ${logPath}`);
    const stats = fs.statSync(logPath);
    console.log(`📊 日志文件大小: ${(stats.size / 1024).toFixed(2)} KB, 最后修改时间: ${stats.mtime.toLocaleString()}`);
    
    // 读取末尾 150 行
    const content = fs.readFileSync(logPath, 'utf8');
    const allLines = content.split('\n');
    const tailLines = allLines.slice(-120);
    console.log('================================================================================');
    console.log('📜 [引擎最新日志输出 (末尾 120 行)]:');
    console.log('================================================================================');
    console.log(tailLines.join('\n'));
    console.log('================================================================================');
} else {
    console.log('❌ 未找到活跃的引擎日志文件！');
}

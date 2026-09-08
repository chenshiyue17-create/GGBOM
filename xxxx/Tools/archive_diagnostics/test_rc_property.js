const http = require('http');

function testReadProperty(objectPath, propertyName) {
    const postData = JSON.stringify({
        objectPath: objectPath,
        propertyName: propertyName
    });

    const options = {
        hostname: '127.0.0.1',
        port: 30010,
        path: '/remote/object/property',
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData)
        }
    };

    const req = http.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
            console.log(`[HTTP ${res.statusCode}] ${propertyName}:`, body);
        });
    });

    req.on('error', (e) => {
        console.error('Error:', e.message);
    });

    req.write(postData);
    req.end();
}

console.log('测试读取关卡对象属性...');
testReadProperty('/Game/GGBOM/Maps/MAP_GGBOM_Main.MAP_GGBOM_Main:PersistentLevel.PortraitCamera_9x16', 'RootComponent');
testReadProperty('/Engine/Transient.World_0:PersistentLevel.PortraitCamera_9x16', 'RootComponent');

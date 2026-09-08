const http = require('http');

function searchAssets(query) {
    const postData = JSON.stringify({
        Query: query,
        Filter: {
            ClassNames: ['Actor', 'CameraActor', 'PaperSpriteActor']
        }
    });

    const options = {
        hostname: '127.0.0.1',
        port: 30010,
        path: '/remote/search/assets',
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
            console.log(`[HTTP ${res.statusCode}] Search Results:`, body);
        });
    });

    req.on('error', (e) => console.error('Error:', e.message));
    req.write(postData);
    req.end();
}

searchAssets('Camera');
searchAssets('Player');

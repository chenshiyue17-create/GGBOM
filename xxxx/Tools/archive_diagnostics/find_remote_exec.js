const { execSync } = require('child_process');

try {
    const res = execSync('find "/Volumes" -name "remote_execution.py" 2>/dev/null || true').toString().trim();
    console.log('Found remote_execution.py in Volumes:');
    console.log(res);
} catch (e) {
    console.log('Error:', e.message);
}

const fs = require('fs');
const path = require('path');

const candidates = [
    '/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py',
    '/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py',
    '/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py',
    '/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py',
];

for (const c of candidates) {
    if (fs.existsSync(c)) {
        console.log('FOUND:', c);
        const content = fs.readFileSync(c, 'utf8');
        console.log('FILE LENGTH:', content.length);
        fs.writeFileSync('/Users/cc/Desktop/GGBOM/xxxx/Tools/official_remote_execution.py', content, 'utf8');
        console.log('Successfully copied to Tools/official_remote_execution.py');
        break;
    }
}

const https = require('https');
const fs = require('fs');
const path = require('path');
const unzip = require('unzipper');
const { spawnSync } = require('child_process');

const PYTHON_VERSION = '3.11.8';
const PYTHON_EMBED_URL = `https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-embed-amd64.zip`;
const PYTHON_EMBED_DIR = path.join(__dirname, '..', 'src', 'python-embed');
const REQUIREMENTS = path.join(__dirname, '..', 'requirements.txt');
const GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py';
const GET_PIP_PATH = path.join(PYTHON_EMBED_DIR, 'get-pip.py');

function download(url, dest) {
    return new Promise((resolve, reject) => {
        if (fs.existsSync(dest)) return resolve();
        const file = fs.createWriteStream(dest);
        https.get(url, response => {
            if (response.statusCode !== 200) return reject(new Error('Failed to download: ' + url));
            response.pipe(file);
            file.on('finish', () => file.close(resolve));
        }).on('error', err => reject(err));
    });
}

async function extract(zipPath, destDir) {
    await fs.createReadStream(zipPath)
        .pipe(unzip.Extract({ path: destDir }))
        .promise();
}

async function fixPthFile() {
    // Trova il file pythonXY._pth (es: python311._pth)
    const files = fs.readdirSync(PYTHON_EMBED_DIR);
    const pthFile = files.find(f => /^python\d+\._pth$/.test(f));
    if (!pthFile) {
        console.warn('File ._pth non trovato, skip fix');
        return;
    }
    const pthPath = path.join(PYTHON_EMBED_DIR, pthFile);
    let content = fs.readFileSync(pthPath, 'utf-8');
    // Decommenta import site se necessario
    if (content.includes('#import site')) {
        content = content.replace('#import site', 'import site');
        fs.writeFileSync(pthPath, content, 'utf-8');
        console.log('Modificato', pthFile, ': decommentato import site');
    }
}

async function main() {
    if (!fs.existsSync(PYTHON_EMBED_DIR)) fs.mkdirSync(PYTHON_EMBED_DIR, { recursive: true });

    const zipPath = path.join(PYTHON_EMBED_DIR, 'python-embed.zip');
    console.log('Scarico Python embedded...');
    await download(PYTHON_EMBED_URL, zipPath);

    console.log('Estraggo Python embedded...');
    await extract(zipPath, PYTHON_EMBED_DIR);

    // Fix ._pth file to enable site-packages
    await fixPthFile();

    // Scarica get-pip.py
    console.log('Scarico get-pip.py...');
    await download(GET_PIP_URL, GET_PIP_PATH);

    // Installa pip nell'environment embedded
    const pythonExe = path.join(PYTHON_EMBED_DIR, 'python.exe');
    console.log('Installo pip...');
    let pipResult = spawnSync(pythonExe, [GET_PIP_PATH], { cwd: PYTHON_EMBED_DIR, stdio: 'inherit' });
    if (pipResult.status !== 0) {
        console.error('Installazione pip fallita');
        process.exit(1);
    }

    // Installa requirements
    if (fs.existsSync(REQUIREMENTS)) {
        console.log('Installo requirements...');
        let reqResult = spawnSync(pythonExe, ['-m', 'pip', 'install', '-r', REQUIREMENTS, '--target', path.join(PYTHON_EMBED_DIR, 'Lib', 'site-packages')], { stdio: 'inherit' });
        if (reqResult.status !== 0) {
            console.error('Installazione requirements fallita');
            process.exit(1);
        }
    } else {
        console.warn('requirements.txt non trovato, skip installazione pacchetti');
    }

    console.log('Python embedded pronto in:', PYTHON_EMBED_DIR);
}

main().catch(err => {
    console.error('Errore:', err);
    process.exit(1);
});

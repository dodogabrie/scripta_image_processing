import fs from 'fs';
import path from 'path';
import https from 'https';
import unzipper from 'unzipper';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const vipsVersion = '8.17.0';
const vipsUrl = `https://github.com/libvips/build-win64-mxe/releases/download/v${vipsVersion}/vips-dev-w64-all-${vipsVersion}.zip`;
const destDir = path.join(__dirname, '..', 'src', 'python-embed', 'vips-bin');
const destZip = path.join(destDir, `vips.zip`);
const expectedDll = path.join(destDir, `vips-dev-w64-all-${vipsVersion}`, 'bin', 'libvips-42.dll');

if (fs.existsSync(expectedDll)) {
  console.log('libvips DLLs already present, skipping download.');
  process.exit(0);
}

fs.mkdirSync(destDir, { recursive: true });

function download(url, dest, cb) {
  const file = fs.createWriteStream(dest);
  https.get(url, response => {
    if ([301, 302].includes(response.statusCode)) {
      download(response.headers.location, dest, cb);
      return;
    }
    if (response.statusCode !== 200) {
      cb(new Error(`Failed to get '${url}' (${response.statusCode})`));
      return;
    }
    response.pipe(file);
    file.on('finish', () => file.close(cb));
  }).on('error', err => {
    fs.unlink(dest, () => cb(err));
  });
}

console.log('Downloading libvips...');
download(vipsUrl, destZip, err => {
  if (err) {
    console.error('Download failed:', err);
    process.exit(1);
  }
  console.log('Extracting libvips...');
  fs.createReadStream(destZip)
    .pipe(unzipper.Extract({ path: destDir }))
    .on('close', () => {
      fs.unlinkSync(destZip);
      console.log('libvips DLLs ready.');
    })
    .on('error', err => {
      console.error('Extraction failed:', err);
      process.exit(1);
    });
});

#!/usr/bin/env node
// Download optimization tools for Windows (cwebp, jpegoptim, oxipng, ffmpeg)
// Style: callback-based, CommonJS, Windows-only, modeled after download-libvips-win.js

const fs = require('fs');
const path = require('path');
const https = require('https');
const unzipper = require('unzipper');

const TOOLS = [
  {
    name: 'cwebp',
    url: 'https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.4.0-windows-x64.zip',
    zipSubPath: 'bin/cwebp.exe',
  },
  {
    name: 'jpegoptim',
    url: 'https://github.com/tjko/jpegoptim/releases/download/v1.5.5/jpegoptim-1.5.5-x64-windows.zip',
    zipSubPath: 'jpegoptim.exe',
  },
  {
    name: 'oxipng',
    url: 'https://github.com/shssoichiro/oxipng/releases/download/v9.0.0/oxipng-9.0.0-x86_64-pc-windows-msvc.zip',
    zipSubPath: 'oxipng.exe',
  },
  {
    name: 'ffmpeg',
    url: 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
    zipSubPath: 'bin/ffmpeg.exe',
  },
];

const TOOLS_DIR = path.join(__dirname, '..', 'src', 'tools', 'windows');

if (process.platform !== 'win32') {
  console.log('This script only supports Windows. Skipping.');
  process.exit(0);
}

fs.mkdirSync(TOOLS_DIR, { recursive: true });

function download(url, dest, cb) {
  const file = fs.createWriteStream(dest);
  https.get(url, response => {
    // Handle all redirect status codes
    if ([301, 302, 303, 307, 308].includes(response.statusCode)) {
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

function extractAndCopy(zipPath, subPath, outPath, cb) {
  let found = false;
  fs.createReadStream(zipPath)
    .pipe(unzipper.Parse())
    .on('entry', entry => {
      const entryPath = entry.path.replace(/\\/g, '/');
      if (entryPath.endsWith(subPath)) {
        found = true;
        entry.pipe(fs.createWriteStream(outPath))
          .on('finish', () => {
            fs.chmodSync(outPath, 0o755);
            cb();
          });
      } else {
        entry.autodrain();
      }
    })
    .on('close', () => {
      if (!found) cb(new Error(`Did not find ${subPath} in archive`));
    })
    .on('error', cb);
}

function setupTool(tool, cb) {
  const outExe = path.join(TOOLS_DIR, tool.name + '.exe');
  if (fs.existsSync(outExe)) {
    console.log(`${tool.name} already present, skipping.`);
    cb();
    return;
  }
  const zipPath = path.join(TOOLS_DIR, tool.name + '.zip');
  console.log(`Downloading ${tool.name}...`);
  download(tool.url, zipPath, err => {
    if (err) {
      console.error(`Download failed for ${tool.name}:`, err);
      process.exit(1);
    }
    console.log(`Extracting ${tool.name}...`);
    extractAndCopy(zipPath, tool.zipSubPath, outExe, err2 => {
      fs.unlinkSync(zipPath);
      if (err2) {
        console.error(`Extraction failed for ${tool.name}:`, err2);
        process.exit(1);
      }
      console.log(`${tool.name} ready.`);
      cb();
    });
  });
}

function setupAll(i) {
  if (i >= TOOLS.length) {
    console.log('All tools ready.');
    return;
  }
  setupTool(TOOLS[i], () => setupAll(i + 1));
}

setupAll(0);

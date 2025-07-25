#!/usr/bin/env node
// Download optimization tools for Windows (cwebp, jpegoptim, oxipng, ffmpeg, ffprobe, exiftool)

const fs = require('fs');
const path = require('path');
const https = require('https');
const unzipper = require('unzipper');

const TOOLS = [
  {
    url: 'https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.4.0-windows-x64.zip',
    files: [{ zipSubPath: 'bin/cwebp.exe', outName: 'cwebp.exe' }],
  },
  {
    url: 'https://github.com/tjko/jpegoptim/releases/download/v1.5.5/jpegoptim-1.5.5-x64-windows.zip',
    files: [{ zipSubPath: 'jpegoptim.exe', outName: 'jpegoptim.exe' }],
  },
  {
    url: 'https://github.com/shssoichiro/oxipng/releases/download/v9.0.0/oxipng-9.0.0-x86_64-pc-windows-msvc.zip',
    files: [{ zipSubPath: 'oxipng.exe', outName: 'oxipng.exe' }],
  },
  {
    url: 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
    files: [
      { zipSubPath: 'bin/ffmpeg.exe', outName: 'ffmpeg.exe' },
      { zipSubPath: 'bin/ffprobe.exe', outName: 'ffprobe.exe' },
    ],
  },
  {
    url: 'https://exiftool.org/exiftool-13.32_64.zip',
    files: [{ zipSubPath: 'exiftool(-k).exe', outName: 'exiftool.exe' }],
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

function extractAndCopyMultiple(zipPath, files, cb) {
  const remaining = new Set(files.map(f => f.zipSubPath));
  fs.createReadStream(zipPath)
    .pipe(unzipper.Parse())
    .on('entry', entry => {
      const entryPath = entry.path.replace(/\\/g, '/');
      const match = files.find(f => entryPath.endsWith(f.zipSubPath));
      if (match) {
        remaining.delete(match.zipSubPath);
        const outPath = path.join(TOOLS_DIR, match.outName);
        const tmpPath = match.zipSubPath === 'exiftool(-k).exe'
          ? outPath.replace(/\.exe$/, '-k.exe')
          : outPath;
        entry.pipe(fs.createWriteStream(tmpPath))
          .on('finish', () => {
            if (tmpPath !== outPath) fs.renameSync(tmpPath, outPath);
            fs.chmodSync(outPath, 0o755);
            if (remaining.size === 0) cb();
          });
      } else {
        entry.autodrain();
      }
    })
    .on('close', () => {
      if (remaining.size > 0) {
        const missing = [...remaining].join(', ');
        cb(new Error(`Missing from archive: ${missing}`));
      }
    })
    .on('error', cb);
}

function setupTool(tool, cb) {
  const needFiles = tool.files.filter(f =>
    !fs.existsSync(path.join(TOOLS_DIR, f.outName))
  );
  if (needFiles.length === 0) {
    console.log(`${tool.files.map(f => f.outName).join(', ')} already present, skipping.`);
    cb();
    return;
  }
  const zipPath = path.join(TOOLS_DIR, path.basename(tool.url));
  console.log(`Downloading from ${tool.url}...`);
  download(tool.url, zipPath, err => {
    if (err) {
      console.error(`Download failed:`, err);
      process.exit(1);
    }
    console.log(`Extracting ${needFiles.map(f => f.outName).join(', ')}...`);
    extractAndCopyMultiple(zipPath, needFiles, err2 => {
      fs.unlinkSync(zipPath);
      if (err2) {
        console.error(`Extraction failed:`, err2);
        process.exit(1);
      }
      console.log(`✔ Ready: ${needFiles.map(f => f.outName).join(', ')}`);
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

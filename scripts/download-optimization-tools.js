#!/usr/bin/env node
/**
 * Download optimization tools for bundling with Electron app
 * This script downloads platform-specific binaries for image/video optimization
 */

import fs from 'fs';
import path from 'path';
import https from 'https';
import { execSync } from 'child_process';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const TOOLS_DIR = path.join(__dirname, '..', 'src', 'tools');
const platform = os.platform();
const arch = os.arch();

// Tool configurations with download URLs
const TOOLS_CONFIG = {
  // WebP tools
  cwebp: {
    windows: {
      url: 'https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-2.3.2-windows-x64.zip',
      binary: 'bin/cwebp.exe',
      extract: true
    },
    linux: {
      url: 'https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.3.2-linux-x86-64.tar.gz',
      binary: 'bin/cwebp',
      extract: true
    },
    darwin: {
      url: 'https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.3.2-mac-x86-64.tar.gz',
      binary: 'bin/cwebp',
      extract: true
    }
  },

  // JPEG optimization tools
  jpegoptim: {
    windows: {
      url: 'https://github.com/tjko/jpegoptim/releases/download/v1.5.5/jpegoptim-1.5.5-x64-windows.zip',
      binary: 'jpegoptim.exe',
      extract: true
    },
    linux: {
      // Use system tools on Linux - user must install them
      useSystemTools: true,
      requiredCommands: ['jpegoptim'],
      installInstructions: 'sudo apt-get install jpegoptim'
    },
    darwin: {
      // Use system tools on macOS - user must install them
      useSystemTools: true,
      requiredCommands: ['jpegoptim'],
      installInstructions: 'brew install jpegoptim'
    }
  },

  // PNG optimization tools
  oxipng: {
    windows: {
      url: 'https://github.com/shssoichiro/oxipng/releases/download/v9.0.0/oxipng-9.0.0-x86_64-pc-windows-msvc.zip',
      binary: 'oxipng.exe',
      extract: true
    },
    linux: {
      url: 'https://github.com/shssoichiro/oxipng/releases/download/v9.0.0/oxipng-9.0.0-x86_64-unknown-linux-musl.tar.gz',
      binary: 'oxipng',
      extract: true
    },
    darwin: {
      url: 'https://github.com/shssoichiro/oxipng/releases/download/v9.0.0/oxipng-9.0.0-x86_64-apple-darwin.tar.gz',
      binary: 'oxipng',
      extract: true
    }
  },

  // FFmpeg for video processing
  ffmpeg: {
    windows: {
      url: 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
      binary: 'bin/ffmpeg.exe',
      extract: true
    },
    linux: {
      // Use system tools on Linux - user must install them
      useSystemTools: true,
      requiredCommands: ['ffmpeg', 'ffprobe'],
      installInstructions: 'sudo apt-get install ffmpeg'
    },
    darwin: {
      url: 'https://evermeet.cx/ffmpeg/ffmpeg-latest.zip',
      binary: 'ffmpeg',
      extract: true
    }
  }
};

/**
 * Download and extract a file with timeout and progress
 */
async function downloadFile(url, outputPath, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    console.log(`Starting download: ${url}`);
    
    const file = fs.createWriteStream(outputPath);
    let downloadedBytes = 0;
    let totalBytes = 0;
    
    const timeout = setTimeout(() => {
      file.destroy();
      fs.unlink(outputPath, () => {});
      reject(new Error(`Download timeout after ${timeoutMs}ms`));
    }, timeoutMs);
    
    const request = https.get(url, (response) => {
      if (response.statusCode === 302 || response.statusCode === 301) {
        clearTimeout(timeout);
        file.destroy();
        fs.unlink(outputPath, () => {});
        // Handle redirects
        return downloadFile(response.headers.location, outputPath, timeoutMs)
          .then(resolve)
          .catch(reject);
      }
      
      if (response.statusCode !== 200) {
        clearTimeout(timeout);
        file.destroy();
        fs.unlink(outputPath, () => {});
        reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
        return;
      }
      
      totalBytes = parseInt(response.headers['content-length'] || '0');
      if (totalBytes > 0) {
        console.log(`Download size: ${(totalBytes / 1024 / 1024).toFixed(2)} MB`);
      }
      
      response.on('data', (chunk) => {
        downloadedBytes += chunk.length;
        if (totalBytes > 0) {
          const progress = ((downloadedBytes / totalBytes) * 100).toFixed(1);
          process.stdout.write(`\rProgress: ${progress}% (${(downloadedBytes / 1024 / 1024).toFixed(2)} MB)`);
        }
      });
      
      response.pipe(file);
      
      file.on('finish', () => {
        clearTimeout(timeout);
        file.close();
        console.log(`\nDownload completed: ${outputPath}`);
        resolve();
      });
      
      file.on('error', (err) => {
        clearTimeout(timeout);
        fs.unlink(outputPath, () => {});
        reject(err);
      });
    });
    
    request.on('error', (err) => {
      clearTimeout(timeout);
      file.destroy();
      fs.unlink(outputPath, () => {});
      reject(err);
    });
    
    request.setTimeout(timeoutMs, () => {
      clearTimeout(timeout);
      request.destroy();
      file.destroy();
      fs.unlink(outputPath, () => {});
      reject(new Error(`Request timeout after ${timeoutMs}ms`));
    });
  });
}

/**
 * Download with retry logic
 */
async function downloadWithRetry(url, outputPath, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`Attempt ${attempt}/${maxRetries} for ${path.basename(outputPath)}`);
      await downloadFile(url, outputPath);
      return; // Success
    } catch (error) {
      console.error(`Attempt ${attempt} failed:`, error.message);
      if (attempt === maxRetries) {
        throw error; // Final attempt failed
      }
      console.log(`Retrying in 2 seconds...`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}

/**
 * Extract archive
 */
function extractArchive(archivePath, extractDir) {
  const ext = path.extname(archivePath).toLowerCase();
  const basename = path.basename(archivePath).toLowerCase();
  
  try {
    if (ext === '.zip') {
      if (platform === 'win32') {
        execSync(`powershell Expand-Archive -Path "${archivePath}" -DestinationPath "${extractDir}" -Force`);
      } else {
        execSync(`unzip -o "${archivePath}" -d "${extractDir}"`);
      }
    } else if (ext === '.gz' || archivePath.includes('.tar.gz')) {
      execSync(`tar -xzf "${archivePath}" -C "${extractDir}"`);
    } else if (ext === '.xz' || archivePath.includes('.tar.xz')) {
      execSync(`tar -xJf "${archivePath}" -C "${extractDir}"`);
    } else if (archivePath.includes('.tar.')) {
      // Generic tar file
      execSync(`tar -xf "${archivePath}" -C "${extractDir}"`);
    }
    
    // Remove archive after extraction
    fs.unlinkSync(archivePath);
  } catch (error) {
    console.error(`Failed to extract ${archivePath}:`, error.message);
  }
}

/**
 * Find and move binary to the correct location
 */
function findAndMoveBinary(toolDir, expectedBinaryName, platformConfig) {
  try {
    // Function to recursively find a file
    function findFileRecursively(dir, filename) {
      const files = fs.readdirSync(dir, { withFileTypes: true });
      for (const file of files) {
        const fullPath = path.join(dir, file.name);
        if (file.isDirectory()) {
          const found = findFileRecursively(fullPath, filename);
          if (found) return found;
        } else if (file.name === filename) {
          return fullPath;
        }
      }
      return null;
    }

    const binaryPath = findFileRecursively(toolDir, expectedBinaryName);
    if (binaryPath) {
      const targetPath = path.join(toolDir, expectedBinaryName);
      if (binaryPath !== targetPath) {
        console.log(`Moving binary from ${binaryPath} to ${targetPath}`);
        fs.copyFileSync(binaryPath, targetPath);
        fs.chmodSync(targetPath, '755');
        
        // Clean up nested directories if needed
        const extractedDir = path.dirname(binaryPath);
        if (extractedDir !== toolDir) {
          fs.rmSync(extractedDir, { recursive: true, force: true });
        }
      }
      return true;
    }
    return false;
  } catch (error) {
    console.error(`Error finding/moving binary:`, error.message);
    return false;
  }
}

/**
 * Install tool using package manager
 */
function installWithPackageManager(packageName) {
  // Skip package manager installation if not running as root on Linux
  if (platform === 'linux' && process.getuid && process.getuid() !== 0) {
    console.log(`Skipping package manager installation for ${packageName} (not running as root)`);
    console.log(`Please install manually: sudo apt-get install ${packageName}`);
    return false;
  }

  try {
    if (platform === 'linux') {
      // Try different package managers
      try {
        execSync(`apt-get update && apt-get install -y ${packageName}`, { stdio: 'inherit' });
      } catch {
        try {
          execSync(`yum install -y ${packageName}`, { stdio: 'inherit' });
        } catch {
          execSync(`dnf install -y ${packageName}`, { stdio: 'inherit' });
        }
      }
    } else if (platform === 'darwin') {
      execSync(`brew install ${packageName}`, { stdio: 'inherit' });
    }
    return true;
  } catch (error) {
    console.warn(`Failed to install ${packageName} via package manager:`, error.message);
    return false;
  }
}

/**
 * Copy system binaries to tools directory
 */
function copySystemBinaries(toolDir, binaryNames) {
  let copied = 0;
  for (const binaryName of binaryNames) {
    try {
      const systemPath = execSync(`which ${binaryName}`, { encoding: 'utf8' }).trim();
      if (systemPath && fs.existsSync(systemPath)) {
        const targetPath = path.join(toolDir, binaryName);
        fs.copyFileSync(systemPath, targetPath);
        fs.chmodSync(targetPath, '755');
        console.log(`Copied system binary: ${systemPath} -> ${targetPath}`);
        copied++;
      }
    } catch (error) {
      console.warn(`System binary ${binaryName} not found`);
    }
  }
  return copied;
}

/**
 * Download and setup a specific tool
 */
async function setupTool(toolName, config) {
  const platformConfig = config[platform];
  if (!platformConfig) {
    console.warn(`No configuration for ${toolName} on ${platform}`);
    return;
  }

  console.log(`Setting up ${toolName} for ${platform}...`);

  if (platformConfig.useSystemTools) {
    // For Linux/system tools - just check if they're available and inform user
    console.log(`Checking system tools for ${toolName}...`);
    const missingTools = [];
    
    for (const cmd of platformConfig.requiredCommands) {
      try {
        execSync(`which ${cmd}`, { stdio: 'pipe' });
        console.log(`✅ Found system tool: ${cmd}`);
      } catch {
        missingTools.push(cmd);
      }
    }
    
    if (missingTools.length > 0) {
      console.warn(`❌ Missing system tools: ${missingTools.join(', ')}`);
      console.warn(`Please install them with: ${platformConfig.installInstructions}`);
    } else {
      console.log(`✅ All system tools for ${toolName} are available`);
    }
    return;
  }

  // For Windows/Mac - download and bundle tools
  const toolDir = path.join(TOOLS_DIR, platform, toolName);
  fs.mkdirSync(toolDir, { recursive: true });

  if (platformConfig.url) {
    // Download binary
    const filename = path.basename(platformConfig.url);
    const downloadPath = path.join(toolDir, filename);
    
    console.log(`Downloading ${toolName} from ${platformConfig.url}...`);
    await downloadWithRetry(platformConfig.url, downloadPath);
    
    if (platformConfig.extract) {
      console.log(`Extracting ${toolName}...`);
      extractArchive(downloadPath, toolDir);
      
      // Find and move binary to correct location
      const binaryName = path.basename(platformConfig.binary);
      const binaryMoved = findAndMoveBinary(toolDir, binaryName, platformConfig);
      if (!binaryMoved) {
        console.warn(`Warning: Could not find binary ${binaryName} after extraction`);
      }
    }
    
    // Make binary executable on Unix systems
    if (platform !== 'win32') {
      const binaryPath = path.join(toolDir, path.basename(platformConfig.binary));
      if (fs.existsSync(binaryPath)) {
        fs.chmodSync(binaryPath, '755');
        console.log(`Made ${binaryPath} executable`);
      }
    }
  }

  console.log(`✅ ${toolName} setup completed`);
}

/**
 * Main setup function
 */
async function main() {
  console.log(`Setting up optimization tools for ${platform}-${arch}...`);
  
  // Create tools directory
  fs.mkdirSync(TOOLS_DIR, { recursive: true });
  
  // Setup each tool
  for (const [toolName, config] of Object.entries(TOOLS_CONFIG)) {
    try {
      await setupTool(toolName, config);
    } catch (error) {
      console.error(`Failed to setup ${toolName}:`, error.message);
    }
  }
  
  console.log('🎉 All tools setup completed!');
  
  // Generate tools manifest
  const manifest = {
    platform,
    arch,
    tools: Object.keys(TOOLS_CONFIG),
    generated: new Date().toISOString()
  };
  console.log('Generating tools manifest...');
  
  fs.writeFileSync(
    path.join(TOOLS_DIR, 'manifest.json'),
    JSON.stringify(manifest, null, 2)
  );
  console.log('✅ Tools manifest generated at:', path.join(TOOLS_DIR, 'manifest.json'));
}

// Check if this script is being run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { setupTool, TOOLS_CONFIG };

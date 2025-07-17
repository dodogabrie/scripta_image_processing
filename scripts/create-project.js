import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function createProject(projectName, projectDisplayName, projectDescription) {
    const projectsDir = path.join(__dirname, '..', 'src', 'projects');
    const projectDir = path.join(projectsDir, projectName);
    
    // Check if project already exists
    if (fs.existsSync(projectDir)) {
        console.error(`Project ${projectName} already exists!`);
        process.exit(1);
    }
    
    // Create project directory structure
    const dirs = [
        projectDir,
        path.join(projectDir, 'renderer'),
        path.join(projectDir, 'renderer', 'assets'),
        path.join(projectDir, 'python')
    ];
    
    dirs.forEach(dir => {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`Created directory: ${dir}`);
    });
    
    // Create config.json
    const config = {
        "name": projectDisplayName,
        "description": projectDescription,
        "icon": "renderer/assets/icon.svg",
        "version": "1.0.0",
        "main": `renderer/Project${projectName.charAt(0).toUpperCase() + projectName.slice(1)}Component.vue`,
        "python_scripts": [
            "python/main.py"
        ],
        "requirements": [
            "opencv-python==4.10.0.84",
            "numpy==2.2.1"
        ]
    };
    
    fs.writeFileSync(
        path.join(projectDir, 'config.json'),
        JSON.stringify(config, null, 2),
        'utf-8'
    );
    
    const componentName = `Project${projectName.charAt(0).toUpperCase() + projectName.slice(1)}Component.vue`;
    const vueComponent = `<template>
      <div class="container py-4">
        <h1>${projectDisplayName}</h1>
        <p class="text-muted">${projectDescription}</p>

        <!-- UI logica qui -->
        <button @click="selectInputDir" class="btn btn-primary mb-2">Input</button>
        <button @click="selectOutputDir" class="btn btn-secondary mb-2">Output</button>

        <div v-if="processing" class="text-muted">Elaborazione...</div>
        <div v-if="elaborazioneCompletata" class="alert alert-success">Completato!</div>
      </div>
    </template>

    <script>
    export default {
      name: '${componentName.replace('.vue', '')}',
      data() {
        return {
          inputDir: null,
          outputDir: null,
          processing: false,
          elaborazioneCompletata: false,
          consoleLines: [],
        };
      },
      methods: {
        async selectInputDir() {
          this.inputDir = await window.electronAPI.selectDirectory();
        },
        async selectOutputDir() {
          this.outputDir = await window.electronAPI.selectDirectory();
        },
        async processData() {
          this.processing = true;
          const result = await window.electronAPI.runProjectScript('${projectName}', 'main.py', [this.inputDir, this.outputDir]);
          this.processing = false;
          this.elaborazioneCompletata = result.success;
        },
        goBack() {
          this.$emit('goBack');
        }
      }
    };
    </script>
    `;

    fs.writeFileSync(
      path.join(projectDir, 'renderer', componentName),
      vueComponent,
      'utf-8'
    );

    
    // Create Python main.py
    const pythonMain = `#!/usr/bin/env python3
# filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/${projectName}/python/main.py

import sys
import os
import argparse

def main(input_dir, output_dir):
    """
    Main processing function for ${projectDisplayName}
    
    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path
    """
    print(f"Processing started...")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Add your processing logic here
    print("Processing logic goes here...")
    
    print("Processing complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="${projectDescription}")
    parser.add_argument("input_dir", type=str, help="Input directory")
    parser.add_argument("output_dir", type=str, help="Output directory")
    
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir)`;
    
    fs.writeFileSync(
        path.join(projectDir, 'python', 'main.py'),
        pythonMain,
        'utf-8'
    );
    
    // Create placeholder icon
    const iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-gear" viewBox="0 0 16 16">
  <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"/>
  <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115l.094-.319z"/>
</svg>`;
    
    fs.writeFileSync(
        path.join(projectDir, 'renderer', 'assets', 'icon.svg'),
        iconSvg,
        'utf-8'
    );
    
    console.log(`\n✅ Project ${projectName} created successfully!`);
    console.log(`📁 Location: ${projectDir}`);
    console.log(`\nNext steps:`);
    console.log(`1. Customize the template in renderer/${projectName}.template.html`);
    console.log(`2. Add your processing logic in python/main.py`);
    console.log(`3. Update config.json with specific requirements`);
    console.log(`4. Test your project in the main application`);
}

// Parse command line arguments
if (process.argv.length < 5) {
    console.log('Usage: node create-project.js <project_name> <display_name> <description>');
    console.log('Example: node create-project.js project2 "Image Enhancer" "Enhance image quality using AI algorithms"');
    process.exit(1);
}

const [,, projectName, displayName, description] = process.argv;

// Validate project name
if (!/^[a-z][a-z0-9]*$/.test(projectName)) {
    console.error('Project name must be lowercase letters and numbers only, starting with a letter');
    process.exit(1);
}

createProject(projectName, displayName, description);

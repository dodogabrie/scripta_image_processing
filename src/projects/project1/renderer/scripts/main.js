const { createApp } = Vue;

createApp({
    data() {
        return {
            imageLoaded: false,
            processing: false,
            originalImage: null,
            processedImage: null,
            imagePath: null,
            borderPixels: 20,
            showStepByStep: false
        };
    },
    
    methods: {
        async loadImage(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            // Check file type
            const allowedTypes = ['image/tiff', 'image/tif', 'image/jpeg', 'image/jpg', 'image/png'];
            if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().match(/\.(tiff|tif|jpg|jpeg|png)$/)) {
                alert('Formato file non supportato. Usa TIFF, TIF, JPG o PNG.');
                return;
            }
            
            try {
                // Save image to temp directory
                const result = await window.electronAPI.saveImageToTemp(file);
                if (result.success) {
                    this.imagePath = result.path;
                    this.originalImage = `data:${file.type};base64,${result.base64}`;
                    this.imageLoaded = true;
                    this.processedImage = null;
                }
            } catch (error) {
                console.error('Errore caricamento immagine:', error);
                alert('Errore durante il caricamento dell\'immagine');
            }
        },
        
        async processImage() {
            if (!this.imagePath) return;
            
            this.processing = true;
            
            try {
                const result = await window.electronAPI.runProjectScript('project1', 'microperspective_wrapper.py', [
                    this.imagePath,
                    this.borderPixels.toString(),
                    this.showStepByStep.toString()
                ]);
                
                if (result.success) {
                    // The Python script returns the path to the processed image
                    const processedImagePath = result.output.trim();
                    const processedImageData = await window.electronAPI.loadImageAsBase64(processedImagePath);
                    if (processedImageData.success) {
                        this.processedImage = `data:image/png;base64,${processedImageData.base64}`;
                    } else {
                        throw new Error('Impossibile caricare l\'immagine elaborata');
                    }
                } else {
                    console.error('Errore elaborazione:', result.error);
                    alert(`Errore durante l'elaborazione: ${result.error}`);
                }
            } catch (error) {
                console.error('Errore:', error);
                alert(`Errore: ${error.message}`);
            } finally {
                this.processing = false;
            }
        },
        
        resetImage() {
            this.imageLoaded = false;
            this.originalImage = null;
            this.processedImage = null;
            this.imagePath = null;
            this.$refs.fileInput.value = '';
        },
        
        onDragOver(event) {
            event.target.classList.add('dragover');
        },
        
        onDragLeave(event) {
            event.target.classList.remove('dragover');
        },
        
        onDrop(event) {
            event.target.classList.remove('dragover');
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                this.$refs.fileInput.files = files;
                this.loadImage({ target: { files: files } });
            }
        },
        
        goBack() {
            window.electronAPI.goBackToMain();
        }
    }
}).mount('#app');

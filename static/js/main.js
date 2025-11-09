// State Management
let currentState = {
    uploadedFile: null,
    filename: null,
    jobId: null
};

// DOM Elements
const dropZone = document.getElementById('dropZone');
const imageInput = document.getElementById('imageInput');
const previewImg = document.getElementById('previewImg');
const imagePreview = document.getElementById('imagePreview');
const removeImageBtn = document.getElementById('removeImage');
const continueBtn = document.getElementById('continueBtn');

const uploadSection = document.getElementById('upload-section');
const configSection = document.getElementById('config-section');
const processingSection = document.getElementById('processing-section');
const completeSection = document.getElementById('complete-section');
const errorSection = document.getElementById('error-section');

const videoForm = document.getElementById('videoForm');
const backBtn = document.getElementById('backBtn');
const generateBtn = document.getElementById('generateBtn');

const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const jobIdSpan = document.getElementById('jobId');
const currentStageSpan = document.getElementById('currentStage');

const resultVideo = document.getElementById('resultVideo');
const downloadBtn = document.getElementById('downloadBtn');
const newVideoBtn = document.getElementById('newVideoBtn');

const errorText = document.getElementById('errorText');
const retryBtn = document.getElementById('retryBtn');

// Initialize
init();

function init() {
    setupEventListeners();
}

// Event Listeners
function setupEventListeners() {
    // Upload area
    dropZone.addEventListener('click', () => imageInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    
    imageInput.addEventListener('change', handleFileSelect);
    removeImageBtn.addEventListener('click', resetUpload);
    continueBtn.addEventListener('click', showConfigSection);
    
    // Form
    backBtn.addEventListener('click', () => {
        showSection('upload');
    });
    
    videoForm.addEventListener('submit', handleGenerate);
    
    // Complete
    downloadBtn.addEventListener('click', downloadVideo);
    newVideoBtn.addEventListener('click', resetAll);
    retryBtn.addEventListener('click', resetAll);
}

// Drag & Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--primary)';
    dropZone.style.background = 'rgba(99, 102, 241, 0.1)';
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border)';
    dropZone.style.background = 'transparent';
}

function handleDrop(e) {
    e.preventDefault();
    handleDragLeave(e);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// File Handling
async function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showError('Please select an image file');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        imagePreview.classList.remove('hidden');
        document.querySelector('.upload-content').style.display = 'none';
        continueBtn.disabled = false;
    };
    reader.readAsDataURL(file);
    
    // Upload to server
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentState.filename = data.filename;
            currentState.uploadedFile = file;
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        showError('Failed to upload image: ' + error.message);
    }
}

function resetUpload() {
    imagePreview.classList.add('hidden');
    document.querySelector('.upload-content').style.display = 'block';
    previewImg.src = '';
    imageInput.value = '';
    continueBtn.disabled = true;
    currentState.filename = null;
    currentState.uploadedFile = null;
}

// Section Navigation
function showSection(section) {
    uploadSection.classList.add('hidden');
    configSection.classList.add('hidden');
    processingSection.classList.add('hidden');
    completeSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    
    switch(section) {
        case 'upload':
            uploadSection.classList.remove('hidden');
            break;
        case 'config':
            configSection.classList.remove('hidden');
            break;
        case 'processing':
            processingSection.classList.remove('hidden');
            break;
        case 'complete':
            completeSection.classList.remove('hidden');
            break;
        case 'error':
            errorSection.classList.remove('hidden');
            break;
    }
}

function showConfigSection() {
    showSection('config');
}

// Video Generation
async function handleGenerate(e) {
    e.preventDefault();
    
    if (!currentState.filename) {
        showError('No image uploaded');
        return;
    }
    
    const formData = new FormData();
    formData.append('filename', currentState.filename);
    formData.append('prompt', document.getElementById('prompt').value);
    formData.append('duration', document.getElementById('duration').value);
    formData.append('ratio', document.getElementById('ratio').value);
    formData.append('voice_text', document.getElementById('voiceText').value);
    formData.append('voice_type', document.getElementById('voiceType').value);
    
    try {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Starting...';
        
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentState.jobId = data.job_id;
            showSection('processing');
            jobIdSpan.textContent = data.job_id;
            pollJobStatus(data.job_id);
        } else {
            throw new Error(data.message || 'Generation failed');
        }
    } catch (error) {
        showError('Failed to start generation: ' + error.message);
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Video';
    }
}

// Job Status Polling
async function pollJobStatus(jobId) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            const data = await response.json();
            
            if (data.success) {
                updateProgress(data);
                
                if (data.stage === 'completed') {
                    clearInterval(pollInterval);
                    showComplete(data);
                } else if (data.stage === 'failed') {
                    clearInterval(pollInterval);
                    showError(data.errors?.[0]?.message || 'Generation failed');
                }
            }
        } catch (error) {
            console.error('Status poll error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

function updateProgress(data) {
    progressFill.style.width = data.progress + '%';
    currentStageSpan.textContent = data.stage;
    
    const stageMessages = {
        'initialized': 'Initializing...',
        'image_uploaded': 'Image uploaded, starting generation...',
        'video_generated': 'Video generated, downloading...',
        'video_downloaded': 'Adding audio...',
        'audio_added': 'Finalizing...',
        'completed': 'Complete!'
    };
    
    progressText.textContent = stageMessages[data.stage] || 'Processing...';
}

function showComplete(data) {
    showSection('complete');
    
    // Set video source
    if (data.runware_data?.video_url) {
        resultVideo.src = data.runware_data.video_url;
    }
}

// Download
async function downloadVideo() {
    if (!currentState.jobId) return;
    
    try {
        window.location.href = `/api/download/${currentState.jobId}`;
    } catch (error) {
        showError('Failed to download video: ' + error.message);
    }
}

// Error Handling
function showError(message) {
    errorText.textContent = message;
    showSection('error');
}

// Reset
function resetAll() {
    currentState = {
        uploadedFile: null,
        filename: null,
        jobId: null
    };
    
    resetUpload();
    videoForm.reset();
    progressFill.style.width = '0%';
    resultVideo.src = '';
    
    showSection('upload');
}
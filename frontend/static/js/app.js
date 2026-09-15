// ===== State Management =====
const state = {
    currentTab: 'search',
    chatHistory: [],
    isLoading: false,
    availableFiles: [],
    selectedFile: null
};

// ===== DOM Elements =====
const elements = {
    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Search
    searchInput: document.getElementById('search-input'),
    searchBtn: document.getElementById('search-btn'),
    topKSelect: document.getElementById('top-k-select'),
    searchResults: document.getElementById('search-results'),
    
    // Chat
    chatMessages: document.getElementById('chat-messages'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    clearChatBtn: document.getElementById('clear-chat-btn'),
    useRagCheckbox: document.getElementById('use-rag'),
    exampleBtns: document.querySelectorAll('#chat-tab .example-btn'),
    searchExampleBtns: document.querySelectorAll('#search-tab .example-btn'),
    fileSelect: document.getElementById('file-select'),
    searchFileSelect: document.getElementById('search-file-select'),
    manageFilesBtn: document.getElementById('manage-files-btn'),
    
    // Modal
    fileModal: document.getElementById('file-modal'),
    closeModal: document.getElementById('close-modal'),
    uploadBox: document.getElementById('upload-box'),
    fileInput: document.getElementById('file-input'),
    browseBtn: document.getElementById('browse-btn'),
    filesList: document.getElementById('files-list'),
    uploadProgress: document.getElementById('upload-progress'),
    
    // Loading
    loadingOverlay: document.getElementById('loading-overlay')
};

// ===== API Functions =====
// One conversation per browser tab. The API keys chat history by session_id;
// without this every tab would share the "default" history.
const SESSION_ID = (() => {
    const KEY = 'rp_session_id';
    let id = sessionStorage.getItem(KEY);
    if (!id) {
        id = `ui-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
        sessionStorage.setItem(KEY, id);
    }
    return id;
})();

// FastAPI reports failures as {"detail": "..."}. Prefer that text over a
// generic message so the user sees what actually went wrong.
async function apiError(response, fallback) {
    try {
        const body = await response.json();
        if (body && body.detail) {
            return new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : JSON.stringify(body.detail)
            );
        }
    } catch (e) {
        // Response had no JSON body; fall through.
    }
    return new Error(fallback);
}

const API = {
    baseURL: window.location.origin,
    
    async search(query, topK = 5, selectedFile = null) {
        const response = await fetch(`${this.baseURL}/api/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, top_k: topK, selected_file: selectedFile })
        });
        
        if (!response.ok) {
            throw await apiError(response, 'Search failed');
        }
        
        return await response.json();
    },
    
    async chat(message, useRag = true, topK = 3, selectedFile = null) {
        const response = await fetch(`${this.baseURL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message, 
                use_rag: useRag,
                top_k: topK,
                selected_file: selectedFile,
                session_id: SESSION_ID
            })
        });
        
        if (!response.ok) {
            throw await apiError(response, 'Chat failed');
        }
        
        return await response.json();
    },
    
    async clearChat() {
        const response = await fetch(
            `${this.baseURL}/api/chat/clear?session_id=${encodeURIComponent(SESSION_ID)}`,
            { method: 'POST' }
        );
        
        if (!response.ok) {
            throw await apiError(response, 'Clear chat failed');
        }
        
        return await response.json();
    },
    
    async getFiles() {
        const response = await fetch(`${this.baseURL}/api/files`);
        
        if (!response.ok) {
            throw await apiError(response, 'Failed to get files');
        }
        
        return await response.json();
    },
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseURL}/api/files/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw await apiError(response, 'File upload failed');
        }
        
        return await response.json();
    },
    
    async processFile(filename) {
        const response = await fetch(`${this.baseURL}/api/files/process/${encodeURIComponent(filename)}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw await apiError(response, 'File processing failed');
        }
        
        return await response.json();
    }
};

// ===== UI Functions =====
const UI = {
    showLoading() {
        elements.loadingOverlay.classList.add('active');
        state.isLoading = true;
    },
    
    hideLoading() {
        elements.loadingOverlay.classList.remove('active');
        state.isLoading = false;
    },
    
    showError(message) {
        alert(`Error: ${message}`);
    },
    
    switchTab(tabName) {
        // Update nav buttons
        elements.navBtns.forEach(btn => {
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Update tab contents
        elements.tabContents.forEach(content => {
            if (content.id === `${tabName}-tab`) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
        
        state.currentTab = tabName;
    },
    
    renderSearchResults(results) {
        if (!results || results.length === 0) {
            const nothingIndexed = !state.availableFiles
                || !state.availableFiles.some(f => f.indexed);
            elements.searchResults.innerHTML = nothingIndexed
                ? `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <h3>No papers indexed yet</h3>
                    <p>
                        Add a PDF with <strong>Manage Files</strong> in the AI
                        Assistant tab, then click <strong>Process</strong> to make
                        it searchable.
                    </p>
                </div>
            `
                : `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>No results found</h3>
                    <p>Try rephrasing, or widen <strong>In:</strong> to all papers.</p>
                </div>
            `;
            return;
        }
        
        const html = results.map((result, index) => {
            const similarity = (result.similarity * 100).toFixed(1);
            const fileName = result.source.split('/').pop();
            const pageLabel = result.page !== null && result.page !== undefined
                ? ` &middot; page ${result.page + 1}`
                : '';
            // A uniformly green badge implies every hit is a strong match.
            // Grade it so a weak result reads as weak.
            const strength = result.similarity >= 0.5
                ? 'strong'
                : result.similarity >= 0.35 ? 'moderate' : 'weak';
            
            return`
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-number">Result ${index + 1}</span>
                        <span class="similarity-badge similarity-${strength}"
                              title="Cosine similarity to your query">
                            ${similarity}% match
                        </span>
                    </div>
                    <div class="result-source">
                        <i class="fas fa-file-pdf"></i>
                        ${fileName}${pageLabel}
                    </div>
                    <div class="result-content">
                        ${result.content}
                    </div>
                </div>
            `;
        }).join('');
        
        elements.searchResults.innerHTML = html;
    },
    
    addChatMessage(role, content, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = role === 'user' 
            ? '<i class="fas fa-user"></i>' 
            : '<i class="fas fa-robot"></i>';
        
        let metaHtml = '';
        if (metadata.contextUsed) {
            let sourcesHtml = '';
            if (metadata.sources && metadata.sources.length > 0) {
                sourcesHtml = `
                    <div class="source-tags">
                        ${metadata.sources.map(source => 
                            `<span class="source-tag">
                                <i class="fas fa-file-pdf"></i>
                                ${source}
                            </span>`
                        ).join('')}
                    </div>
                `;
            }
            
            metaHtml = `
                <div class="message-meta">
                    <span class="context-badge">
                        <i class="fas fa-book"></i>
                        Context from papers
                    </span>
                    <span>${metadata.model || ''}</span>
                </div>
                ${sourcesHtml}
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-bubble">${this.formatMessage(content)}</div>
                ${metaHtml}
            </div>
        `;
        
        // Remove welcome message if exists
        const welcomeMsg = elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        elements.chatMessages.appendChild(messageDiv);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    },
    
    formatMessage(text) {
        // Convert markdown-style formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    },
    
    clearChatMessages() {
        elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-robot"></i>
                <h3>Welcome to AI Research Assistant</h3>
                <p>I can help you understand research papers and answer questions about AI, machine learning, and deep learning.</p>
                <div class="example-questions">
                    <p><strong>Try asking:</strong></p>
                    <button class="example-btn">Explain the attention mechanism</button>
                    <button class="example-btn">What is a transformer model?</button>
                    <button class="example-btn">How does ResNet work?</button>
                </div>
            </div>
        `;
        
        // Re-attach event listeners to new example buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                elements.chatInput.value = btn.textContent;
                elements.chatInput.focus();
            });
        });
    },
    
    showModal() {
        elements.fileModal.classList.add('active');
        this.loadFiles();
    },
    
    hideModal() {
        elements.fileModal.classList.remove('active');
    },
    
    async loadFiles() {
        try {
            elements.filesList.innerHTML = '<p class="loading-text">Loading files...</p>';
            
            const response = await API.getFiles();
            state.availableFiles = response.files;
            
            this.renderFilesList();
            this.updateFileSelect();
        } catch (error) {
            elements.filesList.innerHTML = '<p class="loading-text">Error loading files</p>';
            console.error('Error loading files:', error);
        }
    },
    
    renderFilesList() {
        if (!state.availableFiles || state.availableFiles.length === 0) {
            elements.filesList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-pdf"></i>
                    <h3>No papers found</h3>
                    <p>Upload a PDF to get started</p>
                </div>
            `;
            return;
        }
        
        const html = state.availableFiles.map(file => {
            const sizeKB = Math.round(file.size / 1024);
            const badgeClass = file.type === 'uploaded' ? 'uploaded' : '';
            const indexedBadge = file.indexed
                ? '<span class="file-badge indexed"><i class="fas fa-check-circle"></i> Indexed</span>'
                : '<span class="file-badge not-indexed"><i class="fas fa-exclamation-circle"></i> Not indexed</span>';
            
            return `
                <div class="file-item">
                    <div class="file-info">
                        <i class="fas fa-file-pdf file-icon"></i>
                        <div class="file-details">
                            <div class="file-name">${file.name}</div>
                            <div class="file-meta">
                                <span><i class="fas fa-weight-hanging"></i> ${sizeKB} KB</span>
                                <span class="file-badge ${badgeClass}">
                                    ${file.type === 'uploaded' ? 'Uploaded' : 'Existing'}
                                </span>
                                ${indexedBadge}
                            </div>
                        </div>
                    </div>
                    <div class="file-actions">
                        ${file.indexed ? `
                            <button class="btn btn-primary select-file-btn" data-filename="${file.name}">
                                <i class="fas fa-check"></i>
                                Select
                            </button>
                        ` : ''}
                        ${!file.indexed || file.type === 'uploaded' ? `
                            <button class="btn btn-secondary process-file-btn" data-filename="${file.name}">
                                <i class="fas fa-cog"></i>
                                ${file.indexed ? 'Reprocess' : 'Process'}
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        elements.filesList.innerHTML = html;
        
        // Add event listeners
        document.querySelectorAll('.select-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filename = e.target.closest('button').dataset.filename;
                this.selectFile(filename);
            });
        });
        
        document.querySelectorAll('.process-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filename = e.target.closest('button').dataset.filename;
                this.processFile(filename);
            });
        });
    },
    
    updateFileSelect() {
        // Only indexed papers can be searched, so don't offer the rest.
        const indexed = state.availableFiles.filter(f => f.indexed);

        [elements.fileSelect, elements.searchFileSelect].forEach(select => {
            if (!select) return;
            const previous = select.value;
            select.innerHTML = '<option value="">All papers</option>';

            indexed.forEach(file => {
                const option = document.createElement('option');
                option.value = file.name;
                option.textContent = file.name;
                select.appendChild(option);
            });

            const wanted = select === elements.fileSelect
                ? (state.selectedFile || previous)
                : previous;
            if (wanted && indexed.some(f => f.name === wanted)) {
                select.value = wanted;
            } else if (select === elements.fileSelect && state.selectedFile) {
                // Previously selected paper is no longer searchable.
                state.selectedFile = null;
                select.value = '';
            }
        });
    },
    
    selectFile(filename) {
        const file = (state.availableFiles || []).find(f => f.name === filename);
        if (file && !file.indexed) {
            this.showNotification(
                `${filename} is not indexed yet. Click Process first.`,
                'error'
            );
            return;
        }

        state.selectedFile = filename;
        elements.fileSelect.value = filename;
        this.hideModal();
        
        // Show notification
        this.showNotification(`Selected: ${filename}`, 'success');
    },
    
    async processFile(filename) {
        try {
            UI.showLoading();
            const result = await API.processFile(filename);
            
            this.showNotification(
                `Processed ${filename}: ${result.chunks_inserted} chunks added`, 
                'success'
            );
            
            this.loadFiles(); // Refresh file list
        } catch (error) {
            this.showNotification(`Error processing ${filename}: ${error.message}`, 'error');
        } finally {
            UI.hideLoading();
        }
    },
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show with animation
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Errors can carry a full explanation (e.g. why a PDF has no text),
        // so give them long enough to actually read.
        const duration = type === 'error' ? 12000 : 3000;
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
};

// ===== Event Handlers =====
const handlers = {
    async handleSearch() {
        const query = elements.searchInput.value.trim();
        
        if (!query) {
            UI.showError('Please enter a search query');
            return;
        }
        
        const topK = parseInt(elements.topKSelect.value);
        const selectedFile = elements.searchFileSelect?.value || null;
        
        try {
            UI.showLoading();
            const results = await API.search(query, topK, selectedFile);
            UI.renderSearchResults(results);
        } catch (error) {
            UI.showError(error.message);
        } finally {
            UI.hideLoading();
        }
    },
    
    async handleChat() {
        const message = elements.chatInput.value.trim();
        
        if (!message) {
            return;
        }
        
        const useRag = elements.useRagCheckbox.checked;
        const selectedFile = elements.fileSelect.value;
        
        // Add user message to UI
        UI.addChatMessage('user', message);
        
        // Clear input
        elements.chatInput.value = '';
        elements.chatInput.style.height = 'auto';
        
        try {
            UI.showLoading();
            const response = await API.chat(message, useRag, 3, selectedFile);
            
            UI.addChatMessage('assistant', response.response, {
                contextUsed: response.context_used,
                model: response.model,
                sources: response.sources
            });
            
            state.chatHistory.push(
                { role: 'user', content: message },
                { role: 'assistant', content: response.response }
            );
        } catch (error) {
            UI.showError(error.message);
            UI.addChatMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        } finally {
            UI.hideLoading();
        }
    },
    
    async handleClearChat() {
        if (!confirm('Are you sure you want to clear the chat history?')) {
            return;
        }
        
        try {
            await API.clearChat();
            UI.clearChatMessages();
            state.chatHistory = [];
        } catch (error) {
            UI.showError(error.message);
        }
    },
    
    handleFileUpload(files) {
        if (!files || files.length === 0) return;
        
        const file = files[0];
        
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            UI.showError('Please select a PDF file');
            return;
        }
        
        // Validate file size (max 50MB)
        if (file.size > 50 * 1024 * 1024) {
            UI.showError('File size must be less than 50MB');
            return;
        }
        
        this.uploadFile(file);
    },
    
    async uploadFile(file) {
        try {
            // Show upload progress
            elements.uploadProgress.style.display = 'block';
            const progressFill = elements.uploadProgress.querySelector('.progress-fill');
            const progressText = elements.uploadProgress.querySelector('.progress-text');
            
            progressText.textContent = 'Uploading...';
            progressFill.style.width = '50%';
            
            const result = await API.uploadFile(file);
            
            progressFill.style.width = '100%';
            progressText.textContent = 'Upload complete!';
            
            UI.showNotification(`Uploaded: ${result.filename}`, 'success');
            
            // Refresh files list
            UI.loadFiles();
            
            // Hide progress after delay
            setTimeout(() => {
                elements.uploadProgress.style.display = 'none';
                progressFill.style.width = '0%';
            }, 2000);
            
        } catch (error) {
            elements.uploadProgress.style.display = 'none';
            UI.showError(`Upload failed: ${error.message}`);
        }
    }
};

// ===== Event Listeners =====
function initEventListeners() {
    // Navigation
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            UI.switchTab(btn.dataset.tab);
        });
    });
    
    // Search
    elements.searchBtn.addEventListener('click', handlers.handleSearch);
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handlers.handleSearch();
        }
    });
    
    // Chat
    elements.sendBtn.addEventListener('click', handlers.handleChat);
    elements.chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handlers.handleChat();
        }
    });
    
    // Auto-resize textarea
    elements.chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });
    
    elements.clearChatBtn.addEventListener('click', handlers.handleClearChat);
    
    // File management
    elements.manageFilesBtn.addEventListener('click', () => UI.showModal());
    elements.closeModal.addEventListener('click', () => UI.hideModal());
    
    // Modal close on backdrop click
    elements.fileModal.addEventListener('click', (e) => {
        if (e.target === elements.fileModal) {
            UI.hideModal();
        }
    });
    
    // File upload
    elements.browseBtn.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', (e) => {
        handlers.handleFileUpload(e.target.files);
    });
    
    // Drag and drop
    elements.uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadBox.classList.add('drag-over');
    });
    
    elements.uploadBox.addEventListener('dragleave', (e) => {
        e.preventDefault();
        elements.uploadBox.classList.remove('drag-over');
    });
    
    elements.uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadBox.classList.remove('drag-over');
        handlers.handleFileUpload(e.dataTransfer.files);
    });
    
    elements.uploadBox.addEventListener('click', () => elements.fileInput.click());
    
    // Example questions (chat tab)
    elements.exampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.chatInput.value = btn.textContent.trim();
            elements.chatInput.focus();
        });
    });

    // Example queries (search tab) - fill the box and run the search.
    elements.searchExampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.searchInput.value = btn.dataset.query || btn.textContent.trim();
            handlers.handleSearch();
        });
    });
}

// ===== Initialize App =====
function init() {
    initEventListeners();
    
    // Load available files on startup
    UI.loadFiles().catch(console.error);
    
    console.log('Research AI Assistant initialized');
    
    // Show initialization message
    const initMsg = document.createElement('div');
    initMsg.className = 'init-message';
    initMsg.textContent = 'Research AI Assistant ready!';
    document.body.appendChild(initMsg);
    
    setTimeout(() => initMsg.remove(), 3000);
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

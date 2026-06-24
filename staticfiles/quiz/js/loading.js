// Loading functionality for Online Quiz Portal
class LoadingManager {
    constructor() {
        this.init();
    }

    init() {
        this.createLoadingOverlay();
        this.setupNetworkMonitoring();
        this.setupPageTransitions();
        this.setupFormSubmissions();
    }

    createLoadingOverlay() {
        // Create loading overlay element
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.id = 'globalLoadingOverlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-dots">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
                <div class="loading-text" id="loadingMessage">Loading, please wait...</div>
                <div class="loading-details" id="loadingDetails">Preparing your content</div>
                <div class="progress-container">
                    <div class="progress-bar" id="loadingProgress"></div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // Create network status indicator
        const networkStatus = document.createElement('div');
        networkStatus.className = 'network-status';
        networkStatus.id = 'networkStatus';
        document.body.appendChild(networkStatus);

        // Create page transition loader
        const pageLoader = document.createElement('div');
        pageLoader.className = 'page-transition-loader';
        pageLoader.id = 'pageTransitionLoader';
        document.body.appendChild(pageLoader);
    }

    setupNetworkMonitoring() {
        // Monitor online/offline status
        window.addEventListener('online', () => {
            this.showNetworkStatus('Connection restored', 'online');
            this.hideLoading();
        });

        window.addEventListener('offline', () => {
            this.showNetworkStatus('No internet connection', 'offline');
            this.showLoading('Waiting for network...', 'Your actions will be saved when connection is restored');
        });

        // Check initial status
        if (!navigator.onLine) {
            this.showNetworkStatus('No internet connection', 'offline');
        }
    }

    setupPageTransitions() {
        // Show loader when navigating between pages
        document.addEventListener('DOMContentLoaded', () => {
            this.hideLoading();
        });

        // Show loader when links are clicked
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href && !link.href.includes('javascript:') && !link.target) {
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && !href.includes('logout')) {
                    this.showPageTransition();
                }
            }
        });

        // Handle browser back/forward buttons
        window.addEventListener('beforeunload', () => {
            this.showPageTransition();
        });
    }

    setupFormSubmissions() {
        // Handle form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.method === 'post' || form.method === 'POST') {
                this.showLoading('Submitting...', 'Please wait while we process your request');
                
                // Add loading state to submit button
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('btn-loading');
                    submitBtn.disabled = true;
                }
            }
        });

        // Handle quiz form specifically
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'quizForm') {
                this.showLoading('Submitting Quiz...', 'Saving your answers and calculating score');
            }
        });
    }

    showLoading(message = 'Loading, please wait...', details = '') {
        const overlay = document.getElementById('globalLoadingOverlay');
        const loadingMessage = document.getElementById('loadingMessage');
        const loadingDetails = document.getElementById('loadingDetails');
        const progressBar = document.getElementById('loadingProgress');

        if (overlay && loadingMessage) {
            loadingMessage.textContent = message;
            loadingDetails.textContent = details;
            progressBar.style.width = '0%';
            overlay.classList.add('active');

            // Simulate progress for longer operations
            if (message.includes('Submitting') || message.includes('Saving')) {
                this.simulateProgress();
            }
        }
    }

    hideLoading() {
        const overlay = document.getElementById('globalLoadingOverlay');
        if (overlay) {
            overlay.classList.remove('active');
            
            // Remove button loading states
            const loadingButtons = document.querySelectorAll('.btn-loading');
            loadingButtons.forEach(btn => {
                btn.classList.remove('btn-loading');
                btn.disabled = false;
            });
        }
    }

    showPageTransition() {
        const loader = document.getElementById('pageTransitionLoader');
        if (loader) {
            loader.style.display = 'block';
        }
    }

    hidePageTransition() {
        const loader = document.getElementById('pageTransitionLoader');
        if (loader) {
            loader.style.display = 'none';
        }
    }

    showNetworkStatus(message, type) {
        const status = document.getElementById('networkStatus');
        if (status) {
            status.textContent = message;
            status.className = `network-status ${type} show`;
            
            // Auto hide after 5 seconds for online status
            if (type === 'online') {
                setTimeout(() => {
                    status.classList.remove('show');
                }, 5000);
            }
        }
    }

    simulateProgress() {
        const progressBar = document.getElementById('loadingProgress');
        if (!progressBar) return;

        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress >= 90) {
                progress = 90; // Stay at 90% until actual completion
                clearInterval(interval);
            }
            progressBar.style.width = progress + '%';
        }, 300);
    }

    setQuizLoading() {
        const overlay = document.getElementById('globalLoadingOverlay');
        if (overlay) {
            overlay.classList.add('quiz-loading');
        }
    }

    // Specific loading methods for different scenarios
    showQuizLoading() {
        this.setQuizLoading();
        this.showLoading('Loading Quiz...', 'Preparing questions and timer');
    }

    showResultsLoading() {
        this.showLoading('Calculating Results...', 'Please wait while we evaluate your answers');
    }

    showLoginLoading() {
        this.showLoading('Signing In...', 'Verifying your credentials');
    }
}

// Initialize loading manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.loadingManager = new LoadingManager();
    
    // Hide page transition loader when page is fully loaded
    window.addEventListener('load', function() {
        setTimeout(() => {
            window.loadingManager.hidePageTransition();
            window.loadingManager.hideLoading();
        }, 500);
    });

    // Handle AJAX requests (if any in the future)
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        window.loadingManager.showLoading('Processing Request...', 'Please wait');
        return originalFetch.apply(this, args)
            .then(response => {
                setTimeout(() => {
                    window.loadingManager.hideLoading();
                }, 500);
                return response;
            })
            .catch(error => {
                window.loadingManager.hideLoading();
                throw error;
            });
    };
});

// Utility functions for manual control
window.showLoading = (message, details) => {
    if (window.loadingManager) {
        window.loadingManager.showLoading(message, details);
    }
};

window.hideLoading = () => {
    if (window.loadingManager) {
        window.loadingManager.hideLoading();
    }
};

window.showQuizLoading = () => {
    if (window.loadingManager) {
        window.loadingManager.showQuizLoading();
    }
};
// Dynamic Panel Navigation System for Digital Garden
(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        panelWidth: 660, // Fixed width matching Andy Matuschak's design
        animationDuration: 300,
        contentTypes: ['notes', 'til', 'how_to', 'bookmarks']
    };

    // Panel Manager Class
    class PanelManager {
        constructor() {
            this.panels = [];
            this.currentPanel = -1;
            this.container = null;
            this.init();
        }

        init() {
            // Create or get panel container
            this.container = document.getElementById('panel-container');
            if (!this.container) {
                this.createContainer();
            }

            // Intercept internal link clicks
            this.setupLinkInterception();
            
            // Setup keyboard navigation
            this.setupKeyboardNavigation();
            
            // Initialize from URL if needed
            this.initFromURL();
            
            // Disable HTMX for internal content links
            this.disableHTMXForContentLinks();
        }

        createContainer() {
            this.container = document.createElement('div');
            this.container.id = 'panel-container';
            this.container.className = 'fixed inset-0 z-50 hidden';
            this.container.innerHTML = `
                <div class="panel-overlay absolute inset-0 bg-black bg-opacity-30"></div>
                <div class="panel-wrapper flex flex-row h-full relative" style="overflow-x: auto; scroll-behavior: smooth;">
                    <!-- Panels will be inserted here dynamically -->
                </div>
            `;
            document.body.appendChild(this.container);

            // Close on overlay click
            const overlay = this.container.querySelector('.panel-overlay');
            overlay.addEventListener('click', () => this.closeAll());
        }

        setupLinkInterception() {
            document.addEventListener('click', (e) => {
                const link = e.target.closest('a');
                if (!link) return;

                const href = link.getAttribute('href');
                if (!href) return;

                // Check if it's an internal content link
                const match = href.match(/^\/(notes|til|how_to|bookmarks)\/([^\/]+)$/);
                if (match) {
                    e.preventDefault();
                    e.stopPropagation();
                    const [, contentType, contentId] = match;
                    this.openPanel(contentType, contentId, link);
                    return false;
                }
            }, true); // Use capture phase to intercept before other handlers
        }

        disableHTMXForContentLinks() {
            // Remove HTMX attributes from internal content links
            // This prevents HTMX from intercepting our panel navigation
            const observer = new MutationObserver((mutations) => {
                document.querySelectorAll('a[href^="/notes/"], a[href^="/til/"], a[href^="/how_to/"], a[href^="/bookmarks/"]').forEach(link => {
                    // Remove HTMX attributes if they exist
                    ['hx-get', 'hx-post', 'hx-put', 'hx-delete', 'hx-patch', 'hx-target', 'hx-swap'].forEach(attr => {
                        if (link.hasAttribute(attr)) {
                            link.removeAttribute(attr);
                        }
                    });
                });
            });

            // Start observing
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            // Initial cleanup
            document.querySelectorAll('a[href^="/notes/"], a[href^="/til/"], a[href^="/how_to/"], a[href^="/bookmarks/"]').forEach(link => {
                ['hx-get', 'hx-post', 'hx-put', 'hx-delete', 'hx-patch', 'hx-target', 'hx-swap'].forEach(attr => {
                    if (link.hasAttribute(attr)) {
                        link.removeAttribute(attr);
                    }
                });
            });
        }

        setupKeyboardNavigation() {
            document.addEventListener('keydown', (e) => {
                if (this.panels.length === 0) return;

                switch(e.key) {
                    case 'Escape':
                        this.closeCurrentPanel();
                        break;
                    case 'ArrowLeft':
                        this.navigateLeft();
                        break;
                    case 'ArrowRight':
                        this.navigateRight();
                        break;
                }
            });
        }

        async openPanel(contentType, contentId, sourceElement = null) {
            // Show container if hidden
            if (this.panels.length === 0) {
                this.container.classList.remove('hidden');
            }

            // Check if panel already exists
            const existingIndex = this.panels.findIndex(p => p.id === `${contentType}/${contentId}`);
            if (existingIndex !== -1) {
                this.currentPanel = existingIndex;
                this.scrollToPanel(existingIndex);
                this.updateURL();
                return;
            }

            // Remove panels after current position if adding from middle
            if (this.currentPanel < this.panels.length - 1) {
                // Remove panels to the right of current panel
                const wrapper = this.container.querySelector('.panel-wrapper');
                const panelsToRemove = this.panels.slice(this.currentPanel + 1);
                panelsToRemove.forEach(panel => {
                    const panelEl = wrapper.querySelector(`[data-panel-id="${panel.id}"]`);
                    if (panelEl) panelEl.remove();
                });
                this.panels = this.panels.slice(0, this.currentPanel + 1);
            }

            // No limit on number of panels - Andy Matuschak style allows unlimited panels

            try {
                // Fetch content
                const response = await fetch(`/${contentType}/${contentId}`, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest' // Signal we want partial content
                    }
                });

                if (!response.ok) throw new Error('Failed to load content');

                const html = await response.text();
                
                // Parse the response to extract title and content
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // Try to find the title
                let title = doc.querySelector('h1')?.textContent || 
                           doc.querySelector('.page-title')?.textContent ||
                           contentId.replace(/-/g, ' ');

                // Create panel
                const panel = {
                    id: `${contentType}/${contentId}`,
                    title: title,
                    content: html,
                    contentType: contentType,
                    contentId: contentId
                };

                this.panels.push(panel);
                this.currentPanel = this.panels.length - 1;

                // Render panel
                this.renderPanel(panel, this.currentPanel);
                
                // Update URL
                this.updateURL();

                // Scroll to new panel
                setTimeout(() => this.scrollToPanel(this.currentPanel), 100);

            } catch (error) {
                console.error('Failed to open panel:', error);
                this.showError('Failed to load content');
            }
        }

        renderPanel(panel, index) {
            const wrapper = this.container.querySelector('.panel-wrapper');
            
            const panelEl = document.createElement('div');
            panelEl.className = 'panel bg-white dark:bg-gray-900 shadow-2xl flex flex-col';
            panelEl.style.width = `${CONFIG.panelWidth}px`;
            panelEl.style.minWidth = `${CONFIG.panelWidth}px`;
            panelEl.style.height = '100vh';
            panelEl.style.borderRight = '1px solid rgba(0, 0, 0, 0.1)';
            panelEl.dataset.panelId = panel.id;
            panelEl.dataset.index = index;

            panelEl.innerHTML = `
                <div class="panel-header flex justify-between items-center px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
                    <h2 class="text-xl font-medium text-gray-900 dark:text-gray-100 truncate flex-1">${panel.title}</h2>
                    <button class="close-btn p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors" title="Close panel" aria-label="Close panel">
                        <svg class="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="panel-content flex-1 overflow-y-auto px-8 py-6 bg-white dark:bg-gray-900">
                    <div class="prose prose-lg dark:prose-invert max-w-none">
                        ${panel.content}
                    </div>
                </div>
            `;

            // Add event listeners
            const closeBtn = panelEl.querySelector('.close-btn');
            closeBtn.addEventListener('click', () => this.closePanelAt(index));

            // Setup internal link interception within panel
            this.setupPanelLinks(panelEl);

            wrapper.appendChild(panelEl);

            // Smooth entrance animation
            panelEl.style.transform = 'translateX(100px)';
            panelEl.style.opacity = '0';
            panelEl.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
            
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    panelEl.style.transform = 'translateX(0)';
                    panelEl.style.opacity = '1';
                });
            });
        }

        setupPanelLinks(panelEl) {
            panelEl.addEventListener('click', (e) => {
                const link = e.target.closest('a');
                if (!link) return;

                const href = link.getAttribute('href');
                if (!href) return;

                // Check if it's an internal content link
                const match = href.match(/^\/(notes|til|how_to|bookmarks)\/([^\/]+)$/);
                if (match) {
                    e.preventDefault();
                    const [, contentType, contentId] = match;
                    this.openPanel(contentType, contentId, link);
                }
            });
        }

        // Fullscreen functionality removed - not part of Andy Matuschak design

        closePanelAt(index) {
            const wrapper = this.container.querySelector('.panel-wrapper');
            const panelEl = wrapper.querySelectorAll('.panel')[index];
            
            if (panelEl) {
                // Animate out
                panelEl.style.transform = 'translateX(100%)';
                panelEl.style.opacity = '0';
                
                setTimeout(() => {
                    panelEl.remove();
                    this.panels.splice(index, 1);
                    
                    // Adjust current panel index
                    if (this.currentPanel >= index && this.currentPanel > 0) {
                        this.currentPanel--;
                    }
                    
                    // Update indices of remaining panels
                    wrapper.querySelectorAll('.panel').forEach((p, i) => {
                        p.dataset.index = i;
                    });
                    
                    // Close container if no panels left
                    if (this.panels.length === 0) {
                        this.closeAll();
                    } else {
                        this.updateURL();
                        this.scrollToPanel(this.currentPanel);
                    }
                }, CONFIG.animationDuration);
            }
        }

        closeCurrentPanel() {
            if (this.currentPanel >= 0 && this.currentPanel < this.panels.length) {
                this.closePanelAt(this.currentPanel);
            }
        }

        closeAll() {
            this.panels = [];
            this.currentPanel = -1;
            this.container.classList.add('hidden');
            const wrapper = this.container.querySelector('.panel-wrapper');
            wrapper.innerHTML = '';
            this.updateURL();
        }

        navigateLeft() {
            if (this.currentPanel > 0) {
                this.currentPanel--;
                this.scrollToPanel(this.currentPanel);
                this.updateURL();
            }
        }

        navigateRight() {
            if (this.currentPanel < this.panels.length - 1) {
                this.currentPanel++;
                this.scrollToPanel(this.currentPanel);
                this.updateURL();
            }
        }

        scrollToPanel(index) {
            const wrapper = this.container.querySelector('.panel-wrapper');
            const panels = wrapper.querySelectorAll('.panel');
            
            if (panels[index]) {
                panels[index].scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'nearest', 
                    inline: 'center' 
                });
                
                // Update active state visually
                panels.forEach((panel, i) => {
                    if (i === index) {
                        panel.classList.add('ring-2', 'ring-emerald-500');
                    } else {
                        panel.classList.remove('ring-2', 'ring-emerald-500');
                    }
                });
            }
        }

        updateURL() {
            const params = new URLSearchParams(window.location.search);
            
            if (this.panels.length > 0) {
                const path = this.panels.map(p => p.id).join(',');
                params.set('panels', path);
                params.set('focus', this.currentPanel);
            } else {
                params.delete('panels');
                params.delete('focus');
            }

            const newURL = params.toString() ? 
                `${window.location.pathname}?${params.toString()}` : 
                window.location.pathname;

            window.history.replaceState(
                { panels: this.panels, focus: this.currentPanel },
                '',
                newURL
            );
        }

        initFromURL() {
            const params = new URLSearchParams(window.location.search);
            const panelsParam = params.get('panels');
            const focusParam = params.get('focus');

            if (panelsParam) {
                const panelIds = panelsParam.split(',');
                const focus = parseInt(focusParam) || 0;

                // Open panels in sequence
                panelIds.forEach((id, index) => {
                    const [contentType, contentId] = id.split('/');
                    if (contentType && contentId) {
                        setTimeout(() => {
                            this.openPanel(contentType, contentId);
                            if (index === panelIds.length - 1) {
                                // Set focus after all panels are loaded
                                setTimeout(() => {
                                    this.currentPanel = Math.min(focus, this.panels.length - 1);
                                    this.scrollToPanel(this.currentPanel);
                                }, 500);
                            }
                        }, index * 200);
                    }
                });
            }
        }

        showError(message) {
            // Simple error notification
            const notification = document.createElement('div');
            notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded shadow-lg z-[60]';
            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.panelManager = new PanelManager();
        });
    } else {
        window.panelManager = new PanelManager();
    }
})();
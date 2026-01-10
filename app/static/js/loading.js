/**
 * Loading Utilities - React Suspense Style
 * JavaScript helpers for managing loading states
 */

const LoadingManager = {
    /**
     * Page Loading Overlay
     */
    pageOverlay: null,
    topBar: null,

    init() {
        // Create page loading overlay if doesn't exist
        if (!this.pageOverlay) {
            this.pageOverlay = document.createElement('div');
            this.pageOverlay.className = 'page-loading-overlay';
            this.pageOverlay.innerHTML = `
                <div class="page-loading-spinner">
                    <div class="spinner spinner-lg"></div>
                    <span class="page-loading-text">กำลังโหลด...</span>
                </div>
            `;
            document.body.appendChild(this.pageOverlay);
        }

        // Create top loading bar if doesn't exist
        if (!this.topBar) {
            this.topBar = document.createElement('div');
            this.topBar.className = 'top-loading-bar';
            document.body.appendChild(this.topBar);
        }
    },

    /**
     * Show page loading overlay
     */
    showPageLoading(message = 'กำลังโหลด...') {
        this.init();
        const textEl = this.pageOverlay.querySelector('.page-loading-text');
        if (textEl) textEl.textContent = message;
        this.pageOverlay.classList.add('active');
    },

    /**
     * Hide page loading overlay
     */
    hidePageLoading() {
        if (this.pageOverlay) {
            this.pageOverlay.classList.remove('active');
        }
    },

    /**
     * Top loading bar (YouTube/Next.js style)
     */
    startTopBar() {
        this.init();
        this.topBar.className = 'top-loading-bar starting';
        setTimeout(() => {
            this.topBar.className = 'top-loading-bar loading';
        }, 100);
    },

    finishTopBar() {
        if (this.topBar) {
            this.topBar.className = 'top-loading-bar finishing';
            setTimeout(() => {
                this.topBar.className = 'top-loading-bar complete';
                setTimeout(() => {
                    this.topBar.className = 'top-loading-bar';
                }, 300);
            }, 300);
        }
    },

    /**
     * Button Loading State
     */
    setButtonLoading(button, loading = true) {
        if (!button) return;

        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.classList.add('btn-loading');
        } else {
            button.disabled = false;
            button.classList.remove('btn-loading');
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
                delete button.dataset.originalText;
            }
        }
    },

    /**
     * Show skeleton loading for an element
     */
    showSkeleton(element, type = 'card') {
        if (!element) return;

        element.dataset.originalContent = element.innerHTML;
        element.innerHTML = this.getSkeletonHTML(type);
    },

    hideSkeleton(element) {
        if (!element || !element.dataset.originalContent) return;

        element.innerHTML = element.dataset.originalContent;
        delete element.dataset.originalContent;
    },

    /**
     * Get skeleton HTML by type
     */
    getSkeletonHTML(type) {
        const templates = {
            card: `
                <div class="skeleton-card">
                    <div class="skeleton-card-header">
                        <div class="skeleton skeleton-avatar"></div>
                        <div style="flex: 1;">
                            <div class="skeleton skeleton-text" style="width: 60%;"></div>
                            <div class="skeleton skeleton-text-sm"></div>
                        </div>
                    </div>
                    <div class="skeleton-card-body">
                        <div class="skeleton skeleton-text"></div>
                        <div class="skeleton skeleton-text" style="width: 90%;"></div>
                        <div class="skeleton skeleton-text" style="width: 75%;"></div>
                    </div>
                </div>
            `,
            list: `
                <div class="skeleton-list">
                    <div class="skeleton-list-item">
                        <div class="skeleton skeleton-avatar"></div>
                        <div style="flex: 1;">
                            <div class="skeleton skeleton-text" style="width: 70%;"></div>
                            <div class="skeleton skeleton-text-sm"></div>
                        </div>
                    </div>
                    <div class="skeleton-list-item">
                        <div class="skeleton skeleton-avatar"></div>
                        <div style="flex: 1;">
                            <div class="skeleton skeleton-text" style="width: 60%;"></div>
                            <div class="skeleton skeleton-text-sm"></div>
                        </div>
                    </div>
                    <div class="skeleton-list-item">
                        <div class="skeleton skeleton-avatar"></div>
                        <div style="flex: 1;">
                            <div class="skeleton skeleton-text" style="width: 65%;"></div>
                            <div class="skeleton skeleton-text-sm"></div>
                        </div>
                    </div>
                </div>
            `,
            table: `
                <div>
                    <div class="skeleton-table-row">
                        <div class="skeleton skeleton-text"></div>
                        <div class="skeleton skeleton-text"></div>
                        <div class="skeleton skeleton-text"></div>
                    </div>
                    <div class="skeleton-table-row">
                        <div class="skeleton skeleton-text"></div>
                        <div class="skeleton skeleton-text"></div>
                        <div class="skeleton skeleton-text"></div>
                    </div>
                    <div class="skeleton-table-row">
                        <div class="skeleton skeleton-text"></div>
                        <div class="skeleton skeleton-text"></div>
                        <div class="skeleton skeleton-text"></div>
                    </div>
                </div>
            `,
            text: `
                <div class="skeleton skeleton-text"></div>
                <div class="skeleton skeleton-text" style="width: 90%;"></div>
                <div class="skeleton skeleton-text" style="width: 75%;"></div>
            `
        };

        return templates[type] || templates.card;
    },

    /**
     * Wrap async function with loading state
     */
    async withLoading(fn, options = {}) {
        const {
            button = null,
            overlay = false,
            topBar = false,
            element = null,
            skeletonType = 'card'
        } = options;

        try {
            // Show loading states
            if (button) this.setButtonLoading(button, true);
            if (overlay) this.showPageLoading();
            if (topBar) this.startTopBar();
            if (element) this.showSkeleton(element, skeletonType);

            // Execute function
            const result = await fn();

            return result;
        } finally {
            // Hide loading states
            if (button) this.setButtonLoading(button, false);
            if (overlay) this.hidePageLoading();
            if (topBar) this.finishTopBar();
            if (element) this.hideSkeleton(element);
        }
    }
};

/**
 * Page Transition Handler
 */
const PageTransition = {
    init() {
        // Handle all internal links
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (!link || link.target === '_blank') return;

            // Skip if it's a hash link
            if (link.getAttribute('href').startsWith('#')) return;

            // Skip if it has data-no-transition attribute
            if (link.hasAttribute('data-no-transition')) return;

            e.preventDefault();
            this.navigate(link.href);
        });

        // Show page with fade in on load
        window.addEventListener('DOMContentLoaded', () => {
            const container = document.querySelector('.mobile-container');
            if (container) {
                container.classList.remove('page-loading');
                container.classList.add('page-loaded');
            }
        });
    },

    navigate(url) {
        LoadingManager.startTopBar();

        // Fade out current page
        const container = document.querySelector('.mobile-container');
        if (container) {
            container.classList.add('fade-out');
        }

        // Navigate after fade out
        setTimeout(() => {
            window.location.href = url;
        }, 200);
    }
};

/**
 * Auto-initialize on page load
 */
if (typeof window !== 'undefined') {
    window.LoadingManager = LoadingManager;
    window.PageTransition = PageTransition;

    // Auto-init page transitions
    document.addEventListener('DOMContentLoaded', () => {
        PageTransition.init();
    });
}

/**
 * Toast Notification System
 * Simple, elegant toast notifications for user feedback
 */

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in ms (default: 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toast if any
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    // Icon mapping
    const icons = {
        'success': 'check-circle',
        'error': 'alert-circle',
        'info': 'info',
        'warning': 'alert-triangle'
    };

    const icon = icons[type] || 'info';

    // Set content
    toast.innerHTML = `
        <i data-lucide="${icon}" class="toast-icon"></i>
        <span class="toast-message">${message}</span>
    `;

    // Add to body
    document.body.appendChild(toast);

    // Initialize Lucide icons for the toast
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Show animation (delayed to trigger CSS transition)
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Auto hide after duration
    setTimeout(() => {
        hideToast(toast);
    }, duration);

    return toast;
}

/**
 * Hide and remove a toast
 * @param {HTMLElement} toast - Toast element to hide
 */
function hideToast(toast) {
    if (!toast) return;

    toast.classList.remove('show');

    // Remove from DOM after transition
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

/**
 * Convenience methods for specific toast types
 */
const Toast = {
    success: (message, duration) => showToast(message, 'success', duration),
    error: (message, duration) => showToast(message, 'error', duration),
    warning: (message, duration) => showToast(message, 'warning', duration),
    info: (message, duration) => showToast(message, 'info', duration)
};

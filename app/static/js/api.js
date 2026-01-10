/**
 * API Utilities
 * Helper functions for making API requests with consistent error handling
 */

/**
 * Get current project ID from page context
 * Assumes project ID is set in a global variable or data attribute
 * @returns {string|null} Project ID or null
 */
function getProjectId() {
    // Try to get from window global variable (set in templates)
    if (typeof window.PROJECT_ID !== 'undefined') {
        return window.PROJECT_ID;
    }

    // Try to get from data attribute on body
    const projectId = document.body.dataset.projectId;
    if (projectId) {
        return projectId;
    }

    // Try to get from localStorage (fallback)
    const storedProjectId = localStorage.getItem('current_project_id');
    if (storedProjectId) {
        return storedProjectId;
    }

    console.warn('Project ID not found. Please set PROJECT_ID variable or data-project-id attribute.');
    return null;
}

/**
 * Handle API error responses
 * @param {Response} response - Fetch response object
 * @param {Object} data - Parsed JSON data (may contain error info)
 * @returns {string} Error message to display
 */
function handleApiError(response, data) {
    // Check if response has error object
    if (data && data.error) {
        return data.error.message || 'เกิดข้อผิดพลาด';
    }

    // Handle HTTP status codes
    switch (response.status) {
        case 400:
            return 'ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบและลองใหม่';
        case 401:
            return 'กรุณาเข้าสู่ระบบ';
        case 403:
            return 'คุณไม่มีสิทธิ์ในการดำเนินการนี้';
        case 404:
            return 'ไม่พบข้อมูลที่ต้องการ';
        case 500:
            return 'เกิดข้อผิดพลาดจากเซิร์ฟเวอร์ กรุณาลองใหม่';
        default:
            return 'เกิดข้อผิดพลาด กรุณาลองใหม่';
    }
}

/**
 * Make an API request with error handling
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} Promise resolving to response data
 * @throws {Error} Throws error with user-friendly message
 */
async function apiRequest(url, options = {}) {
    // Set default headers
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    try {
        const response = await fetch(url, defaultOptions);

        // Check content type before parsing
        const contentType = response.headers.get('content-type');
        const isJson = contentType && contentType.includes('application/json');

        let data = null;
        if (isJson) {
            try {
                data = await response.json();
            } catch (jsonError) {
                console.error('JSON Parse Error:', jsonError);
                throw new Error('เซิร์ฟเวอร์ส่งข้อมูลผิดรูปแบบ');
            }
        } else {
            // Response is not JSON (probably HTML error page)
            const text = await response.text();
            console.error('Non-JSON response:', response.status, text.substring(0, 200));

            // Check if it's a redirect to login page
            if (text.includes('login') || text.includes('<!DOCTYPE')) {
                throw new Error('กรุณาเข้าสู่ระบบอีกครั้ง');
            }

            throw new Error(`เซิร์ฟเวอร์ส่ง HTML แทน JSON (Status: ${response.status})`);
        }

        if (!response.ok) {
            const errorMessage = handleApiError(response, data);
            throw new Error(errorMessage);
        }

        return data;
    } catch (error) {
        // If it's already our custom error, re-throw it
        if (error.message && !error.message.includes('fetch')) {
            throw error;
        }

        // Network errors
        console.error('API Request Error:', error);
        throw new Error('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต');
    }
}

/**
 * API Helper methods for common CRUD operations
 */
const API = {
    /**
     * GET request
     * @param {string} endpoint - API endpoint (e.g., '/api/v1/projects/123/transactions')
     * @returns {Promise<Object>}
     */
    get: async (endpoint) => {
        return apiRequest(endpoint, {
            method: 'GET'
        });
    },

    /**
     * POST request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Data to send
     * @returns {Promise<Object>}
     */
    post: async (endpoint, data) => {
        return apiRequest(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * PUT request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Data to send
     * @returns {Promise<Object>}
     */
    put: async (endpoint, data) => {
        return apiRequest(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    /**
     * DELETE request
     * @param {string} endpoint - API endpoint
     * @returns {Promise<Object>}
     */
    delete: async (endpoint) => {
        return apiRequest(endpoint, {
            method: 'DELETE'
        });
    }
};

/**
 * Helper to build API endpoint URLs
 * @param {string} resource - Resource path (e.g., 'transactions', 'recurring')
 * @param {string|null} resourceId - Optional resource ID
 * @returns {string} Full API endpoint URL
 */
function buildApiUrl(resource, resourceId = null, action = null) {
    const projectId = getProjectId();
    if (!projectId) {
        throw new Error('Project ID is required');
    }

    let url = `/api/v1/projects/${projectId}/${resource}`;
    if (resourceId) {
        url += `/${resourceId}`;
    }
    if (action) {
        url += `/${action}`;
    }

    return url;
}

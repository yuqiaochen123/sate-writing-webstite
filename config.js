// Configuration for backend API endpoints
const CONFIG = {
    // Set this to 'local' for development or 'deployed' for production
    environment: 'deployed',
    
    // Backend URLs
    local: {
        baseUrl: 'http://127.0.0.1:5001'
    },
    
    // Replace this with your actual deployed URL
    deployed: {
        baseUrl: 'https://satb-writing-webstie-production.up.railway.app'
    }
};

// Get the current backend URL based on environment
function getBackendUrl() {
    const env = CONFIG.environment;
    return CONFIG[env].baseUrl;
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG, getBackendUrl };
}

(function configureApp() {
    const config = {
        // Set this when frontend and backend are on different domains.
        // Example: 'https://your-backend.onrender.com'
        API_BASE_URL: '',
    };

    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';

    const apiUrl = config.API_BASE_URL
        ? config.API_BASE_URL
        : (isLocal ? 'http://127.0.0.1:8002' : window.location.origin);

    window.APP_CONFIG = {
        API_URL: apiUrl,
    };
})();

/** Custom initialization for Swagger UI with Data Portal theme */
(function() {
    // Inject custom CSS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = '/api-static/ninja/swagger-ui-custom.css';
    document.head.appendChild(link);
    
    // Wait for Swagger UI to be initialized, then apply additional customizations
    const observer = new MutationObserver(function(mutations) {
        const swaggerUI = document.getElementById('swagger-ui');
        if (swaggerUI && swaggerUI.querySelector('.swagger-ui')) {
            // Additional customizations can be added here if needed
            observer.disconnect();
        }
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();


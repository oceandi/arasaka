/**
 * Frontend Logging Utility
 * Client-side error tracking and user action logging
 */

class FrontendLogger {
    constructor() {
        this.endpoint = '/api/log';
        this.enabled = true;
        this.maxRetries = 3;
        this.setupErrorHandlers();
    }

    setupErrorHandlers() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.logError('JavaScript Error', {
                message: event.message,
                filename: event.filename,
                line: event.lineno,
                column: event.colno,
                stack: event.error?.stack
            });
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Unhandled Promise Rejection', {
                reason: event.reason?.toString(),
                stack: event.reason?.stack
            });
        });

        // AJAX error handler
        this.setupAjaxErrorHandling();
    }

    setupAjaxErrorHandling() {
        // Override fetch to add error logging
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (!response.ok) {
                    this.logError('API Request Failed', {
                        url: args[0],
                        status: response.status,
                        statusText: response.statusText,
                        method: args[1]?.method || 'GET'
                    });
                }
                
                return response;
            } catch (error) {
                this.logError('Network Error', {
                    url: args[0],
                    error: error.message,
                    method: args[1]?.method || 'GET'
                });
                throw error;
            }
        };

        // jQuery AJAX error handler (if jQuery is used)
        if (window.$ && $.ajaxSetup) {
            $(document).ajaxError((event, xhr, settings, thrownError) => {
                this.logError('AJAX Error', {
                    url: settings.url,
                    status: xhr.status,
                    statusText: xhr.statusText,
                    method: settings.type,
                    error: thrownError
                });
            });
        }
    }

    async sendLog(level, message, data = {}) {
        if (!this.enabled) return;

        const logEntry = {
            timestamp: new Date().toISOString(),
            level: level,
            message: message,
            url: window.location.href,
            userAgent: navigator.userAgent,
            userId: this.getUserId(),
            sessionId: this.getSessionId(),
            ...data
        };

        try {
            const response = await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(logEntry)
            });

            if (!response.ok) {
                console.error('Failed to send log to server:', response.statusText);
            }
        } catch (error) {
            console.error('Error sending log:', error);
            // Fallback to console logging
            console[level.toLowerCase()](message, data);
        }
    }

    logError(message, data = {}) {
        this.sendLog('ERROR', message, data);
        console.error(message, data);
    }

    logWarning(message, data = {}) {
        this.sendLog('WARNING', message, data);
        console.warn(message, data);
    }

    logInfo(message, data = {}) {
        this.sendLog('INFO', message, data);
        console.info(message, data);
    }

    logUserAction(action, details = {}) {
        this.sendLog('INFO', `User Action: ${action}`, {
            action: action,
            details: details,
            timestamp: new Date().toISOString()
        });
    }

    logPerformance(metric, value, details = {}) {
        this.sendLog('INFO', `Performance: ${metric}`, {
            metric: metric,
            value: value,
            details: details
        });
    }

    getUserId() {
        // Try to get user ID from various sources
        return localStorage.getItem('userId') || 
               sessionStorage.getItem('userId') || 
               'anonymous';
    }

    getSessionId() {
        // Generate or retrieve session ID
        let sessionId = sessionStorage.getItem('sessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('sessionId', sessionId);
        }
        return sessionId;
    }

    // Performance monitoring
    startPerformanceTimer(name) {
        performance.mark(`${name}_start`);
    }

    endPerformanceTimer(name) {
        performance.mark(`${name}_end`);
        performance.measure(name, `${name}_start`, `${name}_end`);
        
        const measure = performance.getEntriesByName(name)[0];
        this.logPerformance(name, measure.duration, {
            startTime: measure.startTime,
            duration: measure.duration
        });
    }

    // File operation logging
    logFileOperation(operation, filename, success = true, error = null) {
        const data = {
            operation: operation,
            filename: filename,
            success: success
        };

        if (error) {
            data.error = error;
            this.logError(`File operation failed: ${operation}`, data);
        } else {
            this.logInfo(`File operation: ${operation}`, data);
        }
    }

    // Map interaction logging
    logMapInteraction(action, coordinates = null, details = {}) {
        this.logUserAction(`Map: ${action}`, {
            coordinates: coordinates,
            ...details
        });
    }

    // AI interaction logging
    logAIInteraction(action, model = null, success = true, error = null) {
        const data = {
            action: action,
            model: model,
            success: success
        };

        if (error) {
            data.error = error;
            this.logError(`AI interaction failed: ${action}`, data);
        } else {
            this.logInfo(`AI interaction: ${action}`, data);
        }
    }

    // Data export logging
    logDataExport(format, recordCount, success = true, error = null) {
        const data = {
            format: format,
            recordCount: recordCount,
            success: success
        };

        if (error) {
            data.error = error;
            this.logError(`Data export failed: ${format}`, data);
        } else {
            this.logInfo(`Data export: ${format}`, data);
        }
    }

    // Module interaction logging
    logModuleInteraction(moduleName, action, details = {}) {
        this.logUserAction(`Module: ${moduleName} - ${action}`, details);
    }

    // Disable logging (for GDPR compliance or debugging)
    disable() {
        this.enabled = false;
    }

    enable() {
        this.enabled = true;
    }
}

// Initialize global logger
window.logger = new FrontendLogger();

// Convenience functions
window.logError = (message, data) => window.logger.logError(message, data);
window.logWarning = (message, data) => window.logger.logWarning(message, data);
window.logInfo = (message, data) => window.logger.logInfo(message, data);
window.logUserAction = (action, details) => window.logger.logUserAction(action, details);

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FrontendLogger;
}
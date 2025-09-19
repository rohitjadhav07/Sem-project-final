/**
 * Enhanced Location Handler with comprehensive error handling and user guidance
 */

class LocationHandler {
    constructor() {
        this.isSupported = !!navigator.geolocation;
        this.permissionState = 'unknown';
        this.lastKnownPosition = null;
        this.watchId = null;
        
        this.init();
    }
    
    async init() {
        if (!this.isSupported) {
            console.error('Geolocation not supported');
            return;
        }
        
        // Check permission state if available
        if (navigator.permissions) {
            try {
                const permission = await navigator.permissions.query({name: 'geolocation'});
                this.permissionState = permission.state;
                console.log('Initial permission state:', this.permissionState);
                
                // Listen for permission changes
                permission.addEventListener('change', () => {
                    this.permissionState = permission.state;
                    console.log('Permission state changed to:', this.permissionState);
                });
            } catch (error) {
                console.log('Permissions API not fully supported');
            }
        }
    }
    
    /**
     * Get current location with enhanced error handling
     */
    async getCurrentLocation(options = {}) {
        return new Promise((resolve, reject) => {
            if (!this.isSupported) {
                reject(new Error('GEOLOCATION_NOT_SUPPORTED'));
                return;
            }
            
            const defaultOptions = {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 60000
            };
            
            const finalOptions = { ...defaultOptions, ...options };
            
            console.log('Requesting location with options:', finalOptions);
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    console.log('Location obtained:', position);
                    this.lastKnownPosition = position;
                    resolve(position);
                },
                (error) => {
                    console.error('Location error:', error);
                    reject(this.handleLocationError(error));
                },
                finalOptions
            );
        });
    }
    
    /**
     * Enhanced error handling with specific error types
     */
    handleLocationError(error) {
        const errorInfo = {
            code: error.code,
            message: error.message,
            type: 'UNKNOWN_ERROR',
            userMessage: 'Unable to get your location.',
            suggestions: []
        };
        
        switch (error.code) {
            case error.PERMISSION_DENIED:
                errorInfo.type = 'PERMISSION_DENIED';
                errorInfo.userMessage = 'Location access was denied. Please allow location access to continue.';
                errorInfo.suggestions = [
                    'Click the location icon in your browser\'s address bar',
                    'Select "Allow" for location access',
                    'Refresh the page and try again',
                    'Check if you\'re in incognito/private mode (location may be blocked)'
                ];
                break;
                
            case error.POSITION_UNAVAILABLE:
                errorInfo.type = 'POSITION_UNAVAILABLE';
                errorInfo.userMessage = 'Your location is currently unavailable.';
                errorInfo.suggestions = [
                    'Ensure GPS/Location Services are enabled on your device',
                    'Move to an area with better signal (near windows, outdoors)',
                    'Check your device\'s location settings',
                    'Try again in a few moments'
                ];
                break;
                
            case error.TIMEOUT:
                errorInfo.type = 'TIMEOUT';
                errorInfo.userMessage = 'Location request timed out.';
                errorInfo.suggestions = [
                    'Try again with a longer timeout',
                    'Move to an area with better GPS signal',
                    'Ensure your device has a clear view of the sky'
                ];
                break;
        }
        
        return errorInfo;
    }
    
    /**
     * Check if location services are likely to work
     */
    async checkLocationAvailability() {
        const result = {
            supported: this.isSupported,
            permission: this.permissionState,
            https: location.protocol === 'https:' || location.hostname === 'localhost',
            recommendations: []
        };
        
        if (!result.supported) {
            result.recommendations.push('Use a modern browser that supports geolocation');
        }
        
        if (!result.https) {
            result.recommendations.push('Location services require HTTPS in production');
        }
        
        if (this.permissionState === 'denied') {
            result.recommendations.push('Location access is blocked - please enable it in browser settings');
        }
        
        return result;
    }
    
    /**
     * Request location with user-friendly UI feedback
     */
    async requestLocationWithUI(statusCallback, options = {}) {
        try {
            if (statusCallback) {
                statusCallback('Checking location availability...', 'info');
            }
            
            const availability = await this.checkLocationAvailability();
            
            if (!availability.supported) {
                throw new Error('GEOLOCATION_NOT_SUPPORTED');
            }
            
            if (availability.permission === 'denied') {
                throw new Error('PERMISSION_DENIED');
            }
            
            if (statusCallback) {
                statusCallback('Requesting your location...', 'info');
            }
            
            const position = await this.getCurrentLocation(options);
            
            if (statusCallback) {
                statusCallback(`Location obtained! Accuracy: ±${Math.round(position.coords.accuracy)}m`, 'success');
            }
            
            return position;
            
        } catch (error) {
            if (statusCallback) {
                const errorInfo = typeof error === 'object' && error.userMessage ? error : this.handleLocationError(error);
                statusCallback(errorInfo.userMessage, 'error', errorInfo);
            }
            throw error;
        }
    }
}

// Global instance
window.locationHandler = new LocationHandler();

/**
 * Utility functions for UI integration
 */
window.LocationUtils = {
    /**
     * Show location permission guide modal
     */
    showPermissionGuide() {
        const modal = document.getElementById('locationPermissionModal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            // Fallback alert
            alert(`To enable location access:

Chrome/Edge:
1. Click the 🔒 lock icon in the address bar
2. Set "Location" to "Allow"
3. Refresh the page

Firefox:
1. Click the 🛡️ shield icon in the address bar
2. Click "Allow Location Access"

Safari:
1. Go to Safari > Preferences > Websites
2. Select "Location Services"
3. Set this website to "Allow"

Mobile:
1. Go to your browser settings
2. Find site permissions or location settings
3. Allow location for this website

If still not working:
- Try refreshing the page
- Ensure you're not in incognito/private mode
- Move to an area with better GPS signal`);
        }
    },
    
    /**
     * Retry location access
     */
    async retryLocation(callback) {
        try {
            const position = await window.locationHandler.getCurrentLocation();
            if (callback) callback(null, position);
            return position;
        } catch (error) {
            if (callback) callback(error, null);
            throw error;
        }
    },
    
    /**
     * Calculate distance between two points
     */
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371000; // Earth's radius in meters
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    },
    
    /**
     * Format location for display
     */
    formatLocation(position) {
        return {
            latitude: position.coords.latitude.toFixed(6),
            longitude: position.coords.longitude.toFixed(6),
            accuracy: Math.round(position.coords.accuracy),
            timestamp: new Date(position.timestamp).toLocaleString()
        };
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Location handler initialized');
    
    // Add global error handler for unhandled location errors
    window.addEventListener('error', function(event) {
        if (event.error && event.error.message && event.error.message.includes('geolocation')) {
            console.error('Unhandled geolocation error:', event.error);
        }
    });
});
/**
 * Hybrid Location System
 * Combines multiple positioning methods for best accuracy (like Zomato/Uber)
 * 
 * Methods (in order):
 * 1. Browser GPS + WiFi positioning
 * 2. Google Geolocation API (WiFi/Cell tower database)
 * 3. Manual coordinate entry (fallback)
 */

class HybridLocationSystem {
    constructor(options = {}) {
        this.options = {
            googleApiKey: options.googleApiKey || null,
            targetAccuracy: options.targetAccuracy || 20, // meters
            gpsTimeout: options.gpsTimeout || 30000, // 30 seconds
            googleTimeout: options.googleTimeout || 10000, // 10 seconds
            maxAttempts: options.maxAttempts || 3,
            ...options
        };
        
        this.currentMethod = null;
        this.attempts = 0;
        this.callbacks = {
            onProgress: null,
            onSuccess: null,
            onError: null
        };
    }

    /**
     * Start location acquisition with hybrid approach
     */
    async getLocation(onSuccess, onError, onProgress) {
        this.callbacks.onSuccess = onSuccess;
        this.callbacks.onError = onError;
        this.callbacks.onProgress = onProgress;
        
        console.log('🎯 Starting hybrid location system...');
        
        // Method 1: Try browser GPS + WiFi
        this.updateProgress('method1', 'Trying GPS + WiFi positioning...');
        const gpsResult = await this.tryBrowserGeolocation();
        
        if (gpsResult && gpsResult.coords.accuracy <= this.options.targetAccuracy) {
            console.log('✅ GPS + WiFi successful:', gpsResult.coords.accuracy + 'm');
            this.handleSuccess(gpsResult, 'gps_wifi');
            return;
        }
        
        // Method 2: Try Google Geolocation API
        if (this.options.googleApiKey) {
            this.updateProgress('method2', 'Trying Google WiFi positioning...');
            const googleResult = await this.tryGoogleGeolocation();
            
            if (googleResult && googleResult.coords.accuracy <= 50) {
                console.log('✅ Google Geolocation successful:', googleResult.coords.accuracy + 'm');
                this.handleSuccess(googleResult, 'google_wifi');
                return;
            }
        }
        
        // Method 3: Use best available result or offer manual entry
        if (gpsResult) {
            console.log('⚠️ Using GPS result with reduced accuracy:', gpsResult.coords.accuracy + 'm');
            this.updateProgress('method3', 'Using available GPS (accuracy: ±' + Math.round(gpsResult.coords.accuracy) + 'm)');
            this.handleSuccess(gpsResult, 'gps_fallback', true);
        } else {
            console.log('❌ All automatic methods failed');
            this.updateProgress('manual', 'Automatic positioning failed. Please enter location manually.');
            this.handleError(new Error('All positioning methods failed'));
        }
    }

    /**
     * Method 1: Browser Geolocation (GPS + WiFi)
     */
    tryBrowserGeolocation() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                console.log('❌ Geolocation not supported');
                resolve(null);
                return;
            }

            let bestPosition = null;
            let attempts = 0;
            const maxAttempts = 3;

            const tryGetPosition = () => {
                attempts++;
                this.updateProgress('method1', `GPS attempt ${attempts}/${maxAttempts}...`);

                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        console.log(`📍 GPS reading ${attempts}: ±${Math.round(position.coords.accuracy)}m`);
                        
                        // Keep best reading
                        if (!bestPosition || position.coords.accuracy < bestPosition.coords.accuracy) {
                            bestPosition = position;
                        }

                        // If good enough, return immediately
                        if (position.coords.accuracy <= this.options.targetAccuracy) {
                            resolve(bestPosition);
                        } else if (attempts < maxAttempts) {
                            // Try again
                            setTimeout(tryGetPosition, 2000);
                        } else {
                            // Return best we got
                            resolve(bestPosition);
                        }
                    },
                    (error) => {
                        console.log(`⚠️ GPS attempt ${attempts} failed:`, error.message);
                        if (attempts < maxAttempts) {
                            setTimeout(tryGetPosition, 2000);
                        } else {
                            resolve(bestPosition);
                        }
                    },
                    {
                        enableHighAccuracy: true,  // Use GPS + WiFi + Cell
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            };

            tryGetPosition();

            // Timeout after gpsTimeout
            setTimeout(() => {
                resolve(bestPosition);
            }, this.options.gpsTimeout);
        });
    }

    /**
     * Method 2: Google Geolocation API (WiFi/Cell tower database)
     */
    async tryGoogleGeolocation() {
        if (!this.options.googleApiKey) {
            console.log('⚠️ Google API key not configured');
            return null;
        }

        try {
            // Scan WiFi networks (if available)
            const wifiData = await this.scanWiFiNetworks();
            
            // Call Google Geolocation API
            const response = await fetch(
                `https://www.googleapis.com/geolocation/v1/geolocate?key=${this.options.googleApiKey}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        considerIp: true,
                        wifiAccessPoints: wifiData
                    })
                }
            );

            if (!response.ok) {
                throw new Error('Google API request failed');
            }

            const data = await response.json();
            
            // Convert to standard position format
            return {
                coords: {
                    latitude: data.location.lat,
                    longitude: data.location.lng,
                    accuracy: data.accuracy,
                    altitude: null,
                    altitudeAccuracy: null,
                    heading: null,
                    speed: null
                },
                timestamp: Date.now(),
                method: 'google_geolocation'
            };
        } catch (error) {
            console.error('❌ Google Geolocation failed:', error);
            return null;
        }
    }

    /**
     * Scan WiFi networks (browser support is limited)
     */
    async scanWiFiNetworks() {
        // Note: Most browsers don't expose WiFi scanning for privacy
        // Google API can still work with just IP-based location
        return [];
    }

    /**
     * Handle successful location acquisition
     */
    handleSuccess(position, method, lowAccuracy = false) {
        this.currentMethod = method;
        
        const result = {
            ...position,
            method: method,
            lowAccuracy: lowAccuracy,
            timestamp: Date.now()
        };

        if (this.callbacks.onSuccess) {
            this.callbacks.onSuccess(result);
        }
    }

    /**
     * Handle location acquisition failure
     */
    handleError(error) {
        if (this.callbacks.onError) {
            this.callbacks.onError(error);
        }
    }

    /**
     * Update progress callback
     */
    updateProgress(stage, message) {
        if (this.callbacks.onProgress) {
            this.callbacks.onProgress({
                stage: stage,
                message: message,
                method: this.currentMethod
            });
        }
    }

    /**
     * Get location using IP geolocation (very rough, last resort)
     */
    async tryIPGeolocation() {
        try {
            const response = await fetch('https://ipapi.co/json/');
            const data = await response.json();
            
            return {
                coords: {
                    latitude: data.latitude,
                    longitude: data.longitude,
                    accuracy: 5000, // Very rough
                    altitude: null,
                    altitudeAccuracy: null,
                    heading: null,
                    speed: null
                },
                timestamp: Date.now(),
                method: 'ip_geolocation'
            };
        } catch (error) {
            console.error('❌ IP Geolocation failed:', error);
            return null;
        }
    }
}

/**
 * Manual Location Entry Helper
 */
class ManualLocationEntry {
    constructor(containerId, onLocationSelected) {
        this.containerId = containerId;
        this.onLocationSelected = onLocationSelected;
        this.map = null;
        this.marker = null;
    }

    /**
     * Show manual entry interface
     */
    show() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="manual-location-entry">
                <h5>📍 Manual Location Entry</h5>
                <p class="text-muted">Automatic positioning failed. Please enter location manually:</p>
                
                <div class="mb-3">
                    <label class="form-label">Search Address or Place</label>
                    <input type="text" class="form-control" id="locationSearch" 
                           placeholder="e.g., Computer Science Building, University Name">
                    <button class="btn btn-primary btn-sm mt-2" onclick="searchLocation()">
                        <i class="fas fa-search"></i> Search
                    </button>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Or Enter Coordinates</label>
                    <div class="row">
                        <div class="col-6">
                            <input type="number" class="form-control" id="manualLat" 
                                   placeholder="Latitude" step="0.000001">
                        </div>
                        <div class="col-6">
                            <input type="number" class="form-control" id="manualLng" 
                                   placeholder="Longitude" step="0.000001">
                        </div>
                    </div>
                    <button class="btn btn-success btn-sm mt-2" onclick="useManualCoordinates()">
                        <i class="fas fa-check"></i> Use These Coordinates
                    </button>
                </div>
                
                <div class="alert alert-info">
                    <strong>💡 Tip:</strong> You can find coordinates by:
                    <ul class="mb-0">
                        <li>Opening Google Maps</li>
                        <li>Right-clicking on your classroom location</li>
                        <li>Copying the coordinates</li>
                    </ul>
                </div>
            </div>
        `;

        container.style.display = 'block';
    }

    /**
     * Hide manual entry interface
     */
    hide() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.style.display = 'none';
        }
    }

    /**
     * Use manually entered coordinates
     */
    useCoordinates(lat, lng) {
        const position = {
            coords: {
                latitude: parseFloat(lat),
                longitude: parseFloat(lng),
                accuracy: 10, // Assume good accuracy for manual entry
                altitude: null,
                altitudeAccuracy: null,
                heading: null,
                speed: null
            },
            timestamp: Date.now(),
            method: 'manual_entry'
        };

        if (this.onLocationSelected) {
            this.onLocationSelected(position);
        }

        this.hide();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HybridLocationSystem, ManualLocationEntry };
}

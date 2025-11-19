/**
 * Enhanced GPS Accuracy Module
 * Implements multiple strategies to improve GPS accuracy:
 * 1. Multiple readings with averaging
 * 2. GPS warm-up period
 * 3. Accuracy filtering
 * 4. Kalman filtering for smoothing
 */

class EnhancedGPS {
    constructor(options = {}) {
        this.options = {
            warmupReadings: options.warmupReadings || 5,
            warmupTimeout: options.warmupTimeout || 30000, // 30 seconds
            minAccuracy: options.minAccuracy || 20, // meters
            maxAge: options.maxAge || 5000, // 5 seconds
            enableHighAccuracy: options.enableHighAccuracy !== false,
            averageReadings: options.averageReadings || 3,
            ...options
        };
        
        this.readings = [];
        this.isWarmedUp = false;
        this.watchId = null;
        this.callbacks = {
            onUpdate: null,
            onError: null,
            onWarmupComplete: null
        };
    }

    /**
     * Start GPS tracking with warm-up period
     */
    start(onUpdate, onError) {
        this.callbacks.onUpdate = onUpdate;
        this.callbacks.onError = onError;

        if (!navigator.geolocation) {
            if (onError) onError(new Error('Geolocation not supported'));
            return;
        }

        console.log('🛰️ Starting enhanced GPS tracking...');
        
        // Start warm-up phase
        this.warmUp().then(() => {
            console.log('✅ GPS warm-up complete, starting continuous tracking');
            this.startContinuousTracking();
        }).catch(error => {
            console.error('❌ GPS warm-up failed:', error);
            if (onError) onError(error);
        });
    }

    /**
     * Warm-up phase: collect multiple readings to stabilize GPS
     */
    warmUp() {
        return new Promise((resolve, reject) => {
            let readingCount = 0;
            const warmupReadings = [];
            const startTime = Date.now();

            console.log(`🔄 GPS warm-up: collecting ${this.options.warmupReadings} readings...`);

            const collectReading = () => {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        readingCount++;
                        warmupReadings.push(position);
                        
                        console.log(`📍 Warm-up reading ${readingCount}/${this.options.warmupReadings}: ` +
                                  `±${Math.round(position.coords.accuracy)}m`);

                        if (readingCount >= this.options.warmupReadings) {
                            // Warm-up complete
                            this.isWarmedUp = true;
                            
                            // Use best reading from warm-up
                            const bestReading = this.getBestReading(warmupReadings);
                            this.readings = [bestReading];
                            
                            if (this.callbacks.onWarmupComplete) {
                                this.callbacks.onWarmupComplete(bestReading);
                            }
                            
                            resolve(bestReading);
                        } else if (Date.now() - startTime < this.options.warmupTimeout) {
                            // Continue warm-up
                            setTimeout(collectReading, 1000);
                        } else {
                            // Timeout - use what we have
                            console.warn('⚠️ GPS warm-up timeout, using available readings');
                            this.isWarmedUp = true;
                            const bestReading = this.getBestReading(warmupReadings);
                            this.readings = [bestReading];
                            resolve(bestReading);
                        }
                    },
                    (error) => {
                        console.error('GPS warm-up error:', error);
                        if (Date.now() - startTime < this.options.warmupTimeout) {
                            setTimeout(collectReading, 2000);
                        } else {
                            reject(error);
                        }
                    },
                    {
                        enableHighAccuracy: this.options.enableHighAccuracy,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            };

            collectReading();
        });
    }

    /**
     * Start continuous GPS tracking with averaging
     */
    startContinuousTracking() {
        this.watchId = navigator.geolocation.watchPosition(
            (position) => {
                // Filter by accuracy
                if (position.coords.accuracy > this.options.minAccuracy * 2) {
                    console.warn(`⚠️ Poor GPS accuracy: ±${Math.round(position.coords.accuracy)}m (skipping)`);
                    return;
                }

                // Add to readings buffer
                this.readings.push(position);
                
                // Keep only recent readings
                if (this.readings.length > this.options.averageReadings) {
                    this.readings.shift();
                }

                // Calculate averaged position
                const averagedPosition = this.getAveragedPosition();
                
                // Notify callback
                if (this.callbacks.onUpdate) {
                    this.callbacks.onUpdate(averagedPosition);
                }
            },
            (error) => {
                console.error('GPS tracking error:', error);
                if (this.callbacks.onError) {
                    this.callbacks.onError(error);
                }
            },
            {
                enableHighAccuracy: this.options.enableHighAccuracy,
                timeout: 10000,
                maximumAge: this.options.maxAge
            }
        );
    }

    /**
     * Get best reading from a set (lowest accuracy value = best)
     */
    getBestReading(readings) {
        if (!readings || readings.length === 0) return null;
        
        return readings.reduce((best, current) => {
            return current.coords.accuracy < best.coords.accuracy ? current : best;
        });
    }

    /**
     * Calculate averaged position from recent readings
     */
    getAveragedPosition() {
        if (this.readings.length === 0) return null;
        
        if (this.readings.length === 1) {
            return this.readings[0];
        }

        // Calculate weighted average (better accuracy = higher weight)
        let totalWeight = 0;
        let weightedLat = 0;
        let weightedLon = 0;
        let bestAccuracy = Infinity;

        this.readings.forEach(reading => {
            const accuracy = reading.coords.accuracy;
            const weight = 1 / (accuracy * accuracy); // Inverse square weighting
            
            totalWeight += weight;
            weightedLat += reading.coords.latitude * weight;
            weightedLon += reading.coords.longitude * weight;
            
            if (accuracy < bestAccuracy) {
                bestAccuracy = accuracy;
            }
        });

        // Create averaged position object
        const avgPosition = {
            coords: {
                latitude: weightedLat / totalWeight,
                longitude: weightedLon / totalWeight,
                accuracy: bestAccuracy, // Use best accuracy from readings
                altitude: this.readings[this.readings.length - 1].coords.altitude,
                altitudeAccuracy: this.readings[this.readings.length - 1].coords.altitudeAccuracy,
                heading: this.readings[this.readings.length - 1].coords.heading,
                speed: this.readings[this.readings.length - 1].coords.speed
            },
            timestamp: Date.now(),
            averaged: true,
            readingCount: this.readings.length
        };

        return avgPosition;
    }

    /**
     * Get current best position
     */
    getCurrentPosition() {
        return this.getAveragedPosition();
    }

    /**
     * Stop GPS tracking
     */
    stop() {
        if (this.watchId !== null) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
            console.log('🛑 GPS tracking stopped');
        }
    }

    /**
     * Get GPS status information
     */
    getStatus() {
        const current = this.getCurrentPosition();
        return {
            isWarmedUp: this.isWarmedUp,
            readingCount: this.readings.length,
            currentAccuracy: current ? Math.round(current.coords.accuracy) : null,
            isTracking: this.watchId !== null,
            averagedReadings: this.readings.length
        };
    }
}

/**
 * Simple Kalman Filter for GPS smoothing
 */
class GPSKalmanFilter {
    constructor(processNoise = 0.001, measurementNoise = 10) {
        this.processNoise = processNoise;
        this.measurementNoise = measurementNoise;
        this.estimatedLat = null;
        this.estimatedLon = null;
        this.errorCovarianceLat = 1;
        this.errorCovarianceLon = 1;
    }

    filter(latitude, longitude, accuracy) {
        if (this.estimatedLat === null) {
            // First reading - initialize
            this.estimatedLat = latitude;
            this.estimatedLon = longitude;
            return { latitude, longitude };
        }

        // Prediction step
        const predictedErrorCovarianceLat = this.errorCovarianceLat + this.processNoise;
        const predictedErrorCovarianceLon = this.errorCovarianceLon + this.processNoise;

        // Update step
        const kalmanGainLat = predictedErrorCovarianceLat / (predictedErrorCovarianceLat + this.measurementNoise);
        const kalmanGainLon = predictedErrorCovarianceLon / (predictedErrorCovarianceLon + this.measurementNoise);

        this.estimatedLat = this.estimatedLat + kalmanGainLat * (latitude - this.estimatedLat);
        this.estimatedLon = this.estimatedLon + kalmanGainLon * (longitude - this.estimatedLon);

        this.errorCovarianceLat = (1 - kalmanGainLat) * predictedErrorCovarianceLat;
        this.errorCovarianceLon = (1 - kalmanGainLon) * predictedErrorCovarianceLon;

        return {
            latitude: this.estimatedLat,
            longitude: this.estimatedLon
        };
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EnhancedGPS, GPSKalmanFilter };
}

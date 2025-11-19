/**
 * Student Location Tracker
 * Real-time location tracking and boundary status checking for students
 */

class StudentLocationTracker {
    constructor(lectureId) {
        this.lectureId = lectureId;
        this.currentLocation = null;
        this.updateInterval = null;
        this.map = null;
        this.studentMarker = null;
        this.boundaryOverlay = null;
        this.isTracking = false;
        this.gpsAccuracy = 999;
    }
    
    startTracking() {
        if (this.isTracking) {
            return;
        }
        
        this.isTracking = true;
        
        // Request high-accuracy GPS
        if (navigator.geolocation) {
            // Get initial location
            this.updateLocation();
            
            // Update every 3 seconds
            this.updateInterval = setInterval(() => {
                this.updateLocation();
            }, 3000);
            
            this.showTrackingStatus('Tracking your location...');
        } else {
            this.showError('Geolocation is not supported by your browser');
        }
    }
    
    stopTracking() {
        this.isTracking = false;
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        this.showTrackingStatus('Location tracking stopped');
    }
    
    updateLocation() {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                this.currentLocation = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };
                
                this.gpsAccuracy = position.coords.accuracy;
                
                // Update map
                this.updateStudentMarker();
                
                // Check boundary status
                this.checkBoundaryStatus();
                
                // Update GPS accuracy indicator
                this.updateGPSAccuracyIndicator(position.coords.accuracy);
            },
            (error) => {
                this.showError('Error getting location: ' + error.message);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }
    
    checkBoundaryStatus() {
        if (!this.currentLocation) {
            return;
        }
        
        const url = `/student/api/lecture/${this.lectureId}/boundary-status?` +
                    `lat=${this.currentLocation.lat}&` +
                    `lon=${this.currentLocation.lon}&` +
                    `accuracy=${this.currentLocation.accuracy}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.displayBoundaryStatus(data);
                }
            })
            .catch(error => {
                console.error('Error checking boundary status:', error);
            });
    }
    
    displayBoundaryStatus(status) {
        const statusDiv = document.getElementById('boundary-status');
        if (!statusDiv) return;
        
        const inside = status.boundary_status.inside;
        const canCheckin = status.boundary_status.can_checkin;
        const gpsAcceptable = status.requirements.meets_requirements;
        
        let statusHTML = '';
        let statusClass = '';
        let statusIcon = '';
        
        if (canCheckin) {
            statusClass = 'alert-success';
            statusIcon = 'fa-check-circle';
            statusHTML = '<h5><i class="fas fa-check-circle"></i> Ready to Check In</h5>';
            statusHTML += '<p>You are inside the classroom boundary with good GPS signal.</p>';
            
            // Enable check-in button
            const checkinBtn = document.getElementById('checkin-button');
            if (checkinBtn) {
                checkinBtn.disabled = false;
                checkinBtn.classList.remove('btn-secondary');
                checkinBtn.classList.add('btn-success');
            }
        } else if (!inside) {
            statusClass = 'alert-danger';
            statusIcon = 'fa-times-circle';
            statusHTML = '<h5><i class="fas fa-times-circle"></i> Outside Classroom</h5>';
            
            if (status.geofence_type === 'rectangular') {
                const distance = status.boundary_status.distance_to_edge;
                statusHTML += `<p>You are ${distance}m away from the classroom boundary.</p>`;
                statusHTML += '<p><small>Move closer to the classroom to check in.</small></p>';
            } else {
                const distance = status.boundary_status.distance;
                const radius = status.boundary_status.radius;
                statusHTML += `<p>You are ${distance.toFixed(1)}m from the lecture location (required: within ${radius}m).</p>`;
            }
            
            // Disable check-in button
            const checkinBtn = document.getElementById('checkin-button');
            if (checkinBtn) {
                checkinBtn.disabled = true;
                checkinBtn.classList.remove('btn-success');
                checkinBtn.classList.add('btn-secondary');
            }
        } else if (!gpsAcceptable) {
            statusClass = 'alert-warning';
            statusIcon = 'fa-exclamation-triangle';
            statusHTML = '<h5><i class="fas fa-exclamation-triangle"></i> Poor GPS Signal</h5>';
            statusHTML += `<p>GPS accuracy: ${this.gpsAccuracy.toFixed(1)}m (required: ≤${status.requirements.gps_accuracy_threshold}m)</p>`;
            statusHTML += '<p><small>Move to an area with better GPS signal (outdoors or near windows).</small></p>';
            
            // Disable check-in button
            const checkinBtn = document.getElementById('checkin-button');
            if (checkinBtn) {
                checkinBtn.disabled = true;
                checkinBtn.classList.remove('btn-success');
                checkinBtn.classList.add('btn-secondary');
            }
        }
        
        statusDiv.innerHTML = `<div class="alert ${statusClass}">${statusHTML}</div>`;
        
        // Update boundary visualization
        this.updateBoundaryVisualization(status);
    }
    
    updateBoundaryVisualization(status) {
        // Initialize map if not already done
        if (!this.map) {
            this.initializeMap();
        }
        
        // Clear existing boundary
        if (this.boundaryOverlay) {
            this.map.removeLayer(this.boundaryOverlay);
        }
        
        const inside = status.boundary_status.inside;
        const color = inside ? '#28a745' : '#dc3545';
        
        if (status.geofence_type === 'rectangular') {
            // Draw rectangular boundary
            // Note: We'd need the actual corners from the API
            // For now, just show a marker
        } else {
            // Draw circular boundary
            const center = status.student_location; // This should be lecture location
            const radius = status.boundary_status.radius;
            
            this.boundaryOverlay = L.circle([center.lat, center.lon], {
                radius: radius,
                color: color,
                fillColor: color,
                fillOpacity: 0.1,
                weight: 2
            }).addTo(this.map);
        }
    }
    
    updateStudentMarker() {
        if (!this.map) {
            this.initializeMap();
        }
        
        if (!this.currentLocation) {
            return;
        }
        
        if (this.studentMarker) {
            this.studentMarker.setLatLng([this.currentLocation.lat, this.currentLocation.lon]);
        } else {
            this.studentMarker = L.marker([this.currentLocation.lat, this.currentLocation.lon], {
                icon: L.divIcon({
                    className: 'student-location-marker',
                    html: '<div class="student-marker-icon"><i class="fas fa-user"></i></div>'
                })
            }).addTo(this.map);
        }
        
        // Center map on student
        this.map.setView([this.currentLocation.lat, this.currentLocation.lon], 18);
    }
    
    updateGPSAccuracyIndicator(accuracy) {
        const indicatorDiv = document.getElementById('gps-accuracy-indicator');
        if (!indicatorDiv) return;
        
        let color = '';
        let label = '';
        
        if (accuracy <= 10) {
            color = 'success';
            label = 'Excellent';
        } else if (accuracy <= 20) {
            color = 'warning';
            label = 'Good';
        } else {
            color = 'danger';
            label = 'Poor';
        }
        
        indicatorDiv.innerHTML = `
            <div class="gps-accuracy-badge badge badge-${color}">
                <i class="fas fa-satellite-dish"></i>
                GPS: ${accuracy.toFixed(1)}m (${label})
            </div>
        `;
    }
    
    attemptCheckin() {
        if (!this.currentLocation) {
            alert('Location not available. Please wait for GPS signal.');
            return;
        }
        
        const data = {
            lecture_id: this.lectureId,
            latitude: this.currentLocation.lat,
            longitude: this.currentLocation.lon,
            metadata: {
                accuracy: this.currentLocation.accuracy,
                timestamp: new Date().toISOString()
            }
        };
        
        // Show loading
        const checkinBtn = document.getElementById('checkin-button');
        if (checkinBtn) {
            checkinBtn.disabled = true;
            checkinBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking in...';
        }
        
        fetch('/student/api/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showSuccess(result.message);
                this.stopTracking();
                
                // Redirect after 2 seconds
                setTimeout(() => {
                    window.location.href = '/student/active-lectures';
                }, 2000);
            } else {
                this.showError(result.message);
                
                // Re-enable button
                if (checkinBtn) {
                    checkinBtn.disabled = false;
                    checkinBtn.innerHTML = '<i class="fas fa-check"></i> Check In';
                }
            }
        })
        .catch(error => {
            this.showError('Error checking in: ' + error);
            
            // Re-enable button
            if (checkinBtn) {
                checkinBtn.disabled = false;
                checkinBtn.innerHTML = '<i class="fas fa-check"></i> Check In';
            }
        });
    }
    
    initializeMap() {
        const mapDiv = document.getElementById('student-location-map');
        if (!mapDiv) return;
        
        this.map = L.map('student-location-map').setView([40.7128, -74.0060], 17);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
    }
    
    showTrackingStatus(message) {
        const statusDiv = document.getElementById('tracking-status');
        if (statusDiv) {
            statusDiv.innerHTML = `<small class="text-muted"><i class="fas fa-info-circle"></i> ${message}</small>`;
        }
    }
    
    showSuccess(message) {
        const alertDiv = document.getElementById('checkin-alert');
        if (alertDiv) {
            alertDiv.innerHTML = `
                <div class="alert alert-success alert-dismissible fade show">
                    <i class="fas fa-check-circle"></i> ${message}
                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                </div>
            `;
        }
    }
    
    showError(message) {
        const alertDiv = document.getElementById('checkin-alert');
        if (alertDiv) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show">
                    <i class="fas fa-exclamation-circle"></i> ${message}
                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                </div>
            `;
        }
    }
}

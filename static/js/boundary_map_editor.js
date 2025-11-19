/**
 * Boundary Map Editor
 * Interactive map-based editor for rectangular classroom boundaries
 */

class BoundaryMapEditor {
    constructor(mapElementId, lectureId) {
        this.mapElementId = mapElementId;
        this.lectureId = lectureId;
        this.map = null;
        this.boundary = null;
        this.markers = {};
        this.rectangle = null;
        this.mode = 'view'; // 'view', 'edit', 'walk_perimeter'
        this.walkPerimeterStep = 0;
        this.walkPerimeterCorners = [];
        
        this.initializeMap();
    }
    
    initializeMap(center = [40.7128, -74.0060], zoom = 17) {
        // Initialize Leaflet map
        this.map = L.map(this.mapElementId).setView(center, zoom);
        
        // Add tile layers
        const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        });
        
        const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles © Esri',
            maxZoom: 19
        });
        
        // Add layers to map
        streetLayer.addTo(this.map);
        
        // Layer control
        const baseMaps = {
            "Street": streetLayer,
            "Satellite": satelliteLayer
        };
        
        L.control.layers(baseMaps).addTo(this.map);
        
        // Add scale
        L.control.scale().addTo(this.map);
    }
    
    enableEditMode() {
        this.mode = 'edit';
        
        if (!this.boundary) {
            // Create default boundary around current center
            const center = this.map.getCenter();
            const offset = 0.0005; // ~50 meters
            
            this.boundary = {
                ne: [center.lat + offset, center.lng + offset],
                nw: [center.lat + offset, center.lng - offset],
                se: [center.lat - offset, center.lng + offset],
                sw: [center.lat - offset, center.lng - offset]
            };
        }
        
        this.drawRectangularBoundary(this.boundary);
        this.addDraggableMarkers();
    }
    
    enableWalkPerimeterMode() {
        this.mode = 'walk_perimeter';
        this.walkPerimeterStep = 0;
        this.walkPerimeterCorners = [];
        
        // Clear existing boundary
        this.clearBoundary();
        
        // Show instructions
        this.showWalkPerimeterInstructions();
        
        // Get current location
        this.getCurrentLocation((lat, lon) => {
            this.map.setView([lat, lon], 19);
            this.showMarkCornerButton();
        });
    }
    
    showWalkPerimeterInstructions() {
        const cornerNames = ['Northeast', 'Northwest', 'Southwest', 'Southeast'];
        const currentCorner = cornerNames[this.walkPerimeterStep];
        
        const instructionDiv = document.getElementById('walk-perimeter-instructions');
        if (instructionDiv) {
            instructionDiv.innerHTML = `
                <div class="alert alert-info">
                    <h5>Step ${this.walkPerimeterStep + 1}/4: Mark ${currentCorner} Corner</h5>
                    <p>Walk to the ${currentCorner.toLowerCase()} corner of your classroom and tap "Mark Corner"</p>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${(this.walkPerimeterStep / 4) * 100}%"></div>
                    </div>
                </div>
            `;
        }
    }
    
    showMarkCornerButton() {
        const buttonDiv = document.getElementById('mark-corner-button');
        if (buttonDiv) {
            buttonDiv.innerHTML = `
                <button class="btn btn-primary btn-lg" onclick="boundaryEditor.markCorner()">
                    <i class="fas fa-map-marker-alt"></i> Mark Corner
                </button>
            `;
        }
    }
    
    markCorner() {
        this.getCurrentLocation((lat, lon) => {
            const cornerNames = ['ne', 'nw', 'sw', 'se'];
            const cornerName = cornerNames[this.walkPerimeterStep];
            
            this.walkPerimeterCorners.push({
                name: cornerName,
                coords: [lat, lon]
            });
            
            // Add marker
            const marker = L.marker([lat, lon], {
                icon: L.divIcon({
                    className: 'corner-marker',
                    html: `<div class="corner-label">${cornerName.toUpperCase()}</div>`
                })
            }).addTo(this.map);
            
            this.markers[cornerName] = marker;
            
            this.walkPerimeterStep++;
            
            if (this.walkPerimeterStep < 4) {
                this.showWalkPerimeterInstructions();
            } else {
                this.completeWalkPerimeter();
            }
        });
    }
    
    completeWalkPerimeter() {
        // Convert corners to boundary object
        this.boundary = {};
        this.walkPerimeterCorners.forEach(corner => {
            this.boundary[corner.name] = corner.coords;
        });
        
        // Validate and draw
        this.validateBoundary();
        this.drawRectangularBoundary(this.boundary);
        
        // Hide instructions
        const instructionDiv = document.getElementById('walk-perimeter-instructions');
        if (instructionDiv) {
            instructionDiv.innerHTML = `
                <div class="alert alert-success">
                    <h5>Boundary Captured!</h5>
                    <p>Review the boundary and click "Save Boundary" to finalize.</p>
                </div>
            `;
        }
        
        const buttonDiv = document.getElementById('mark-corner-button');
        if (buttonDiv) {
            buttonDiv.innerHTML = '';
        }
        
        this.mode = 'edit';
    }
    
    drawRectangularBoundary(corners) {
        // Clear existing rectangle
        if (this.rectangle) {
            this.map.removeLayer(this.rectangle);
        }
        
        // Create rectangle polygon
        const bounds = [
            corners.ne,
            corners.nw,
            corners.sw,
            corners.se,
            corners.ne // Close the polygon
        ];
        
        // Validate rectangle
        const isValid = this.isValidRectangle(corners);
        const color = isValid ? '#28a745' : '#dc3545';
        
        this.rectangle = L.polygon(bounds, {
            color: color,
            fillColor: color,
            fillOpacity: 0.2,
            weight: 2
        }).addTo(this.map);
        
        // Calculate and display measurements
        this.displayMeasurements(corners);
        
        // Fit map to boundary
        this.map.fitBounds(this.rectangle.getBounds(), { padding: [50, 50] });
    }
    
    addDraggableMarkers() {
        const cornerNames = ['ne', 'nw', 'se', 'sw'];
        const cornerLabels = {
            'ne': 'NE',
            'nw': 'NW',
            'se': 'SE',
            'sw': 'SW'
        };
        
        cornerNames.forEach(cornerName => {
            if (this.markers[cornerName]) {
                this.map.removeLayer(this.markers[cornerName]);
            }
            
            const marker = L.marker(this.boundary[cornerName], {
                draggable: true,
                icon: L.divIcon({
                    className: 'corner-marker-draggable',
                    html: `<div class="corner-handle">${cornerLabels[cornerName]}</div>`
                })
            }).addTo(this.map);
            
            marker.on('drag', () => {
                const pos = marker.getLatLng();
                this.boundary[cornerName] = [pos.lat, pos.lng];
                this.drawRectangularBoundary(this.boundary);
            });
            
            this.markers[cornerName] = marker;
        });
    }
    
    isValidRectangle(corners) {
        // Check if corners form a valid rectangle
        const northLatDiff = Math.abs(corners.ne[0] - corners.nw[0]);
        const southLatDiff = Math.abs(corners.se[0] - corners.sw[0]);
        const eastLonDiff = Math.abs(corners.ne[1] - corners.se[1]);
        const westLonDiff = Math.abs(corners.nw[1] - corners.sw[1]);
        
        const tolerance = 0.0003; // ~33 meters
        
        return (northLatDiff < tolerance && 
                southLatDiff < tolerance && 
                eastLonDiff < tolerance && 
                westLonDiff < tolerance);
    }
    
    displayMeasurements(corners) {
        // Calculate area and perimeter
        const area = this.calculateArea(corners);
        const perimeter = this.calculatePerimeter(corners);
        
        // Calculate side lengths
        const northSide = this.calculateDistance(corners.nw, corners.ne);
        const southSide = this.calculateDistance(corners.sw, corners.se);
        const eastSide = this.calculateDistance(corners.se, corners.ne);
        const westSide = this.calculateDistance(corners.sw, corners.nw);
        
        const measurementDiv = document.getElementById('boundary-measurements');
        if (measurementDiv) {
            measurementDiv.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h6>Boundary Measurements</h6>
                        <table class="table table-sm">
                            <tr>
                                <td>Area:</td>
                                <td><strong>${area.toFixed(1)} m²</strong></td>
                            </tr>
                            <tr>
                                <td>Perimeter:</td>
                                <td><strong>${perimeter.toFixed(1)} m</strong></td>
                            </tr>
                            <tr>
                                <td>North Side:</td>
                                <td>${northSide.toFixed(1)} m</td>
                            </tr>
                            <tr>
                                <td>South Side:</td>
                                <td>${southSide.toFixed(1)} m</td>
                            </tr>
                            <tr>
                                <td>East Side:</td>
                                <td>${eastSide.toFixed(1)} m</td>
                            </tr>
                            <tr>
                                <td>West Side:</td>
                                <td>${westSide.toFixed(1)} m</td>
                            </tr>
                        </table>
                    </div>
                </div>
            `;
        }
    }
    
    calculateDistance(point1, point2) {
        const R = 6371000; // Earth's radius in meters
        const lat1 = point1[0] * Math.PI / 180;
        const lat2 = point2[0] * Math.PI / 180;
        const deltaLat = (point2[0] - point1[0]) * Math.PI / 180;
        const deltaLon = (point2[1] - point1[1]) * Math.PI / 180;
        
        const a = Math.sin(deltaLat/2) * Math.sin(deltaLat/2) +
                  Math.cos(lat1) * Math.cos(lat2) *
                  Math.sin(deltaLon/2) * Math.sin(deltaLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        
        return R * c;
    }
    
    calculateArea(corners) {
        const width = (this.calculateDistance(corners.nw, corners.ne) + 
                      this.calculateDistance(corners.sw, corners.se)) / 2;
        const height = (this.calculateDistance(corners.sw, corners.nw) + 
                       this.calculateDistance(corners.se, corners.ne)) / 2;
        return width * height;
    }
    
    calculatePerimeter(corners) {
        return this.calculateDistance(corners.nw, corners.ne) +
               this.calculateDistance(corners.ne, corners.se) +
               this.calculateDistance(corners.se, corners.sw) +
               this.calculateDistance(corners.sw, corners.nw);
    }
    
    validateBoundary() {
        const isValid = this.isValidRectangle(this.boundary);
        
        const validationDiv = document.getElementById('boundary-validation');
        if (validationDiv) {
            if (isValid) {
                validationDiv.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle"></i> Valid rectangular boundary
                    </div>
                `;
            } else {
                validationDiv.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i> Boundary is not perfectly rectangular. 
                        Adjust corners to align with cardinal directions.
                    </div>
                `;
            }
        }
        
        return isValid;
    }
    
    saveBoundary() {
        if (!this.validateBoundary()) {
            alert('Please adjust the boundary to form a valid rectangle');
            return;
        }
        
        const gpsThreshold = document.getElementById('gps-threshold')?.value || 20;
        const tolerance = document.getElementById('boundary-tolerance')?.value || 2.0;
        
        const data = {
            geofence_type: 'rectangular',
            corners: {
                ne: { lat: this.boundary.ne[0], lon: this.boundary.ne[1] },
                nw: { lat: this.boundary.nw[0], lon: this.boundary.nw[1] },
                se: { lat: this.boundary.se[0], lon: this.boundary.se[1] },
                sw: { lat: this.boundary.sw[0], lon: this.boundary.sw[1] }
            },
            gps_accuracy_threshold: parseInt(gpsThreshold),
            tolerance_m: parseFloat(tolerance)
        };
        
        fetch(`/teacher/api/lecture/${this.lectureId}/set-rectangular-boundary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert('Boundary saved successfully!');
                location.reload();
            } else {
                alert('Error: ' + result.error);
            }
        })
        .catch(error => {
            alert('Error saving boundary: ' + error);
        });
    }
    
    getCurrentLocation(callback) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    callback(position.coords.latitude, position.coords.longitude);
                },
                (error) => {
                    alert('Error getting location: ' + error.message);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            alert('Geolocation is not supported by your browser');
        }
    }
    
    clearBoundary() {
        if (this.rectangle) {
            this.map.removeLayer(this.rectangle);
        }
        
        Object.values(this.markers).forEach(marker => {
            this.map.removeLayer(marker);
        });
        
        this.markers = {};
        this.boundary = null;
    }
    
    loadExistingBoundary(lectureId) {
        fetch(`/teacher/api/lecture/${lectureId}/boundary-preview`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.geofence_type === 'rectangular' && data.boundary) {
                    const corners = data.boundary.corners;
                    this.boundary = {
                        ne: corners.ne,
                        nw: corners.nw,
                        se: corners.se,
                        sw: corners.sw
                    };
                    
                    this.drawRectangularBoundary(this.boundary);
                    
                    if (data.visualization_data) {
                        const center = data.visualization_data.map_center;
                        this.map.setView([center.lat, center.lon], data.visualization_data.zoom_level);
                    }
                }
            })
            .catch(error => {
                console.error('Error loading boundary:', error);
            });
    }
}

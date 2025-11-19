/**
 * Boundary Converter
 * Convert circular geofences to rectangular boundaries
 */

class BoundaryConverter {
    constructor(mapElementId, lectureId) {
        this.mapElementId = mapElementId;
        this.lectureId = lectureId;
        this.map = null;
        this.circularOverlay = null;
        this.rectangularOverlay = null;
        this.suggestedBoundary = null;
        
        this.initializeMap();
    }
    
    initializeMap(center = [40.7128, -74.0060], zoom = 17) {
        this.map = L.map(this.mapElementId).setView(center, zoom);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
    }
    
    convertCircularToRectangular(centerLat, centerLon, radius) {
        // Calculate square with same area as circle
        // Area of circle = π * r²
        // Area of square = side²
        // side = r * sqrt(π)
        const sideLength = radius * Math.sqrt(Math.PI);
        const halfSide = sideLength / 2;
        
        // Convert meters to degrees
        const latOffset = halfSide / 111320;
        const lonOffset = halfSide / (111320 * Math.cos(centerLat * Math.PI / 180));
        
        return {
            ne: [centerLat + latOffset, centerLon + lonOffset],
            nw: [centerLat + latOffset, centerLon - lonOffset],
            se: [centerLat - latOffset, centerLon + lonOffset],
            sw: [centerLat - latOffset, centerLon - lonOffset]
        };
    }
    
    showConversionPreview(originalCircular, suggestedRectangular) {
        // Clear existing overlays
        if (this.circularOverlay) {
            this.map.removeLayer(this.circularOverlay);
        }
        if (this.rectangularOverlay) {
            this.map.removeLayer(this.rectangularOverlay);
        }
        
        // Draw circular geofence
        this.circularOverlay = L.circle(
            [originalCircular.center.lat, originalCircular.center.lon],
            {
                radius: originalCircular.radius,
                color: '#007bff',
                fillColor: '#007bff',
                fillOpacity: 0.1,
                weight: 2,
                dashArray: '5, 5'
            }
        ).addTo(this.map);
        
        // Draw rectangular boundary
        const corners = suggestedRectangular.corners;
        const bounds = [
            corners.ne,
            corners.nw,
            corners.sw,
            corners.se,
            corners.ne
        ];
        
        this.rectangularOverlay = L.polygon(bounds, {
            color: '#28a745',
            fillColor: '#28a745',
            fillOpacity: 0.2,
            weight: 2
        }).addTo(this.map);
        
        // Fit map to show both
        const group = L.featureGroup([this.circularOverlay, this.rectangularOverlay]);
        this.map.fitBounds(group.getBounds(), { padding: [50, 50] });
        
        // Show comparison
        this.displayComparison(originalCircular, suggestedRectangular);
    }
    
    displayComparison(circular, rectangular) {
        const comparisonDiv = document.getElementById('conversion-comparison');
        if (comparisonDiv) {
            const circularArea = Math.PI * Math.pow(circular.radius, 2);
            const rectArea = rectangular.metadata.area_sqm;
            
            comparisonDiv.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h6>Conversion Comparison</h6>
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th></th>
                                    <th>Circular (Original)</th>
                                    <th>Rectangular (Suggested)</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Type:</td>
                                    <td><span class="badge badge-primary">Circle</span></td>
                                    <td><span class="badge badge-success">Rectangle</span></td>
                                </tr>
                                <tr>
                                    <td>Area:</td>
                                    <td>${circularArea.toFixed(1)} m²</td>
                                    <td>${rectArea.toFixed(1)} m²</td>
                                </tr>
                                <tr>
                                    <td>Radius/Size:</td>
                                    <td>${circular.radius} m radius</td>
                                    <td>${rectangular.metadata.perimeter_m.toFixed(1)} m perimeter</td>
                                </tr>
                            </tbody>
                        </table>
                        <div class="alert alert-info mt-3">
                            <small>
                                <i class="fas fa-info-circle"></i>
                                The rectangular boundary approximates the same area as your circular geofence.
                                You can adjust the corners after accepting the conversion.
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    loadAndConvert(lectureId) {
        fetch(`/teacher/api/lecture/${lectureId}/convert-to-rectangular`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                conversion_method: 'square_approximation'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.suggestedBoundary = data.suggested_boundary;
                this.showConversionPreview(data.original_circular, data.suggested_boundary);
                
                // Center map
                const center = data.original_circular.center;
                this.map.setView([center[0], center[1]], 17);
                
                // Show accept button
                this.showAcceptButton();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            alert('Error converting boundary: ' + error);
        });
    }
    
    showAcceptButton() {
        const buttonDiv = document.getElementById('conversion-actions');
        if (buttonDiv) {
            buttonDiv.innerHTML = `
                <button class="btn btn-success btn-lg" onclick="converter.acceptConversion()">
                    <i class="fas fa-check"></i> Accept Rectangular Boundary
                </button>
                <button class="btn btn-secondary btn-lg ml-2" onclick="converter.customizeConversion()">
                    <i class="fas fa-edit"></i> Customize First
                </button>
            `;
        }
    }
    
    acceptConversion() {
        if (!this.suggestedBoundary) {
            alert('No conversion available');
            return;
        }
        
        const corners = this.suggestedBoundary.corners;
        const data = {
            geofence_type: 'rectangular',
            corners: {
                ne: { lat: corners.ne[0], lon: corners.ne[1] },
                nw: { lat: corners.nw[0], lon: corners.nw[1] },
                se: { lat: corners.se[0], lon: corners.se[1] },
                sw: { lat: corners.sw[0], lon: corners.sw[1] }
            },
            gps_accuracy_threshold: 20,
            tolerance_m: 2.0
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
                alert('Conversion successful! Rectangular boundary has been set.');
                location.reload();
            } else {
                alert('Error: ' + result.error);
            }
        })
        .catch(error => {
            alert('Error saving boundary: ' + error);
        });
    }
    
    customizeConversion() {
        // Redirect to boundary editor with suggested boundary
        if (this.suggestedBoundary) {
            sessionStorage.setItem('suggestedBoundary', JSON.stringify(this.suggestedBoundary));
            window.location.href = `/teacher/lecture/${this.lectureId}/edit-boundary`;
        }
    }
}

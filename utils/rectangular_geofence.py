"""
Rectangular Geofence Utilities
Provides classes and functions for rectangular boundary validation
"""
import math
import json
from typing import Tuple, Dict, Optional, List
from utils.geolocation import calculate_distance, calculate_distance_vincenty


class RectangularBoundary:
    """
    Represents a rectangular geofence boundary defined by four corner coordinates
    """
    
    def __init__(self, ne_corner: Tuple[float, float], nw_corner: Tuple[float, float], 
                 se_corner: Tuple[float, float], sw_corner: Tuple[float, float]):
        """
        Initialize rectangular boundary with four corner coordinates
        
        Args:
            ne_corner: (lat, lon) tuple for northeast corner
            nw_corner: (lat, lon) tuple for northwest corner
            se_corner: (lat, lon) tuple for southeast corner
            sw_corner: (lat, lon) tuple for southwest corner
        """
        self.ne = tuple(ne_corner)
        self.nw = tuple(nw_corner)
        self.se = tuple(se_corner)
        self.sw = tuple(sw_corner)
        
        # Validate the rectangle
        is_valid, error = self.validate_rectangle()
        if not is_valid:
            raise ValueError(f"Invalid rectangle: {error}")
    
    def validate_rectangle(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that corners form a proper rectangle
        
        Checks:
        - North edge is roughly horizontal (within 15° tolerance)
        - South edge is roughly horizontal
        - East edge is roughly vertical
        - West edge is roughly vertical
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check that north latitudes are similar (within tolerance)
            north_lat_diff = abs(self.ne[0] - self.nw[0])
            south_lat_diff = abs(self.se[0] - self.sw[0])
            
            # Check that east longitudes are similar
            east_lon_diff = abs(self.ne[1] - self.se[1])
            west_lon_diff = abs(self.nw[1] - self.sw[1])
            
            # Calculate tolerance based on rectangle size (15° tolerance ≈ 0.26 radians)
            # For a 100m x 100m rectangle, allow ~26m deviation
            lat_tolerance = 0.0003  # ~33 meters at equator
            lon_tolerance = 0.0003
            
            if north_lat_diff > lat_tolerance:
                return False, f"North edge not horizontal (lat diff: {north_lat_diff:.6f})"
            
            if south_lat_diff > lat_tolerance:
                return False, f"South edge not horizontal (lat diff: {south_lat_diff:.6f})"
            
            if east_lon_diff > lon_tolerance:
                return False, f"East edge not vertical (lon diff: {east_lon_diff:.6f})"
            
            if west_lon_diff > lon_tolerance:
                return False, f"West edge not vertical (lon diff: {west_lon_diff:.6f})"
            
            # Check that NE is actually northeast of SW
            if self.ne[0] <= self.sw[0]:
                return False, "Northeast corner must be north of southwest corner"
            
            if self.ne[1] <= self.sw[1]:
                return False, "Northeast corner must be east of southwest corner"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def calculate_area(self) -> float:
        """
        Calculate area in square meters using geodesic calculations
        
        Returns:
            Area in square meters
        """
        try:
            # Calculate width (east-west distance) at north edge
            north_width = calculate_distance_vincenty(
                self.nw[0], self.nw[1],
                self.ne[0], self.ne[1]
            )
            
            # Calculate width at south edge
            south_width = calculate_distance_vincenty(
                self.sw[0], self.sw[1],
                self.se[0], self.se[1]
            )
            
            # Average width
            avg_width = (north_width + south_width) / 2
            
            # Calculate height (north-south distance) at west edge
            west_height = calculate_distance_vincenty(
                self.sw[0], self.sw[1],
                self.nw[0], self.nw[1]
            )
            
            # Calculate height at east edge
            east_height = calculate_distance_vincenty(
                self.se[0], self.se[1],
                self.ne[0], self.ne[1]
            )
            
            # Average height
            avg_height = (west_height + east_height) / 2
            
            # Area = width × height
            area = avg_width * avg_height
            
            return area
            
        except Exception as e:
            # Fallback to simpler calculation
            width = calculate_distance(self.nw[0], self.nw[1], self.ne[0], self.ne[1])
            height = calculate_distance(self.sw[0], self.sw[1], self.nw[0], self.nw[1])
            return width * height
    
    def calculate_perimeter(self) -> float:
        """
        Calculate perimeter in meters
        
        Returns:
            Perimeter in meters
        """
        try:
            north_edge = calculate_distance_vincenty(
                self.nw[0], self.nw[1],
                self.ne[0], self.ne[1]
            )
            
            south_edge = calculate_distance_vincenty(
                self.sw[0], self.sw[1],
                self.se[0], self.se[1]
            )
            
            east_edge = calculate_distance_vincenty(
                self.se[0], self.se[1],
                self.ne[0], self.ne[1]
            )
            
            west_edge = calculate_distance_vincenty(
                self.sw[0], self.sw[1],
                self.nw[0], self.nw[1]
            )
            
            return north_edge + south_edge + east_edge + west_edge
            
        except Exception as e:
            # Fallback
            north = calculate_distance(self.nw[0], self.nw[1], self.ne[0], self.ne[1])
            south = calculate_distance(self.sw[0], self.sw[1], self.se[0], self.se[1])
            east = calculate_distance(self.se[0], self.se[1], self.ne[0], self.ne[1])
            west = calculate_distance(self.sw[0], self.sw[1], self.nw[0], self.nw[1])
            return north + south + east + west
    
    def get_center(self) -> Tuple[float, float]:
        """
        Calculate geometric center of rectangle
        
        Returns:
            (lat, lon) tuple of center point
        """
        center_lat = (self.ne[0] + self.nw[0] + self.se[0] + self.sw[0]) / 4
        center_lon = (self.ne[1] + self.nw[1] + self.se[1] + self.sw[1]) / 4
        return (center_lat, center_lon)
    
    def to_dict(self) -> Dict:
        """
        Convert to dictionary for JSON storage
        
        Returns:
            Dictionary representation
        """
        return {
            "type": "rectangular",
            "version": "1.0",
            "corners": {
                "ne": list(self.ne),
                "nw": list(self.nw),
                "se": list(self.se),
                "sw": list(self.sw)
            },
            "metadata": {
                "area_sqm": round(self.calculate_area(), 2),
                "perimeter_m": round(self.calculate_perimeter(), 2),
                "center": list(self.get_center())
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RectangularBoundary':
        """
        Create from dictionary
        
        Args:
            data: Dictionary with corners data
            
        Returns:
            RectangularBoundary instance
        """
        corners = data.get("corners", data)  # Support both formats
        return cls(
            tuple(corners["ne"]),
            tuple(corners["nw"]),
            tuple(corners["se"]),
            tuple(corners["sw"])
        )
    
    @classmethod
    def from_circular(cls, center_lat: float, center_lon: float, radius_m: float) -> 'RectangularBoundary':
        """
        Convert circular geofence to rectangular approximation
        Creates a square with same center and approximately same area
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_m: Radius in meters
            
        Returns:
            RectangularBoundary instance
        """
        # Calculate side length for square with same area as circle
        # Area of circle = π * r²
        # Area of square = side²
        # side = sqrt(π * r²) = r * sqrt(π)
        side_length = radius_m * math.sqrt(math.pi)
        half_side = side_length / 2
        
        # Convert meters to degrees (approximate)
        # 1 degree latitude ≈ 111,320 meters
        # 1 degree longitude ≈ 111,320 * cos(latitude) meters
        lat_offset = half_side / 111320
        lon_offset = half_side / (111320 * math.cos(math.radians(center_lat)))
        
        # Calculate corners
        ne = (center_lat + lat_offset, center_lon + lon_offset)
        nw = (center_lat + lat_offset, center_lon - lon_offset)
        se = (center_lat - lat_offset, center_lon + lon_offset)
        sw = (center_lat - lat_offset, center_lon - lon_offset)
        
        return cls(ne, nw, se, sw)
    
    @classmethod
    def from_center_and_dimensions(cls, center_lat: float, center_lon: float, 
                                   width_m: float, height_m: float) -> 'RectangularBoundary':
        """
        Create rectangular boundary from center point and dimensions
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            width_m: Width in meters (East-West dimension)
            height_m: Height in meters (North-South dimension)
            
        Returns:
            RectangularBoundary instance
        """
        # Calculate half dimensions
        half_width = width_m / 2
        half_height = height_m / 2
        
        # Convert meters to degrees
        # 1 degree latitude ≈ 111,320 meters
        # 1 degree longitude ≈ 111,320 * cos(latitude) meters
        lat_offset = half_height / 111320
        lon_offset = half_width / (111320 * math.cos(math.radians(center_lat)))
        
        # Calculate corners
        ne = (center_lat + lat_offset, center_lon + lon_offset)
        nw = (center_lat + lat_offset, center_lon - lon_offset)
        se = (center_lat - lat_offset, center_lon + lon_offset)
        sw = (center_lat - lat_offset, center_lon - lon_offset)
        
        return cls(ne, nw, se, sw)
    
    def get_bounding_box(self) -> Dict[str, float]:
        """
        Get bounding box coordinates for quick pre-checks
        
        Returns:
            Dictionary with min/max lat/lon
        """
        all_lats = [self.ne[0], self.nw[0], self.se[0], self.sw[0]]
        all_lons = [self.ne[1], self.nw[1], self.se[1], self.sw[1]]
        
        return {
            'min_lat': min(all_lats),
            'max_lat': max(all_lats),
            'min_lon': min(all_lons),
            'max_lon': max(all_lons)
        }
    
    def __repr__(self) -> str:
        return f"<RectangularBoundary NE={self.ne} NW={self.nw} SE={self.se} SW={self.sw}>"



def point_in_rectangular_boundary(point_lat: float, point_lon: float, 
                                  boundary: RectangularBoundary, 
                                  tolerance_m: float = 0) -> Dict:
    """
    Determine if a point is inside a rectangular boundary using ray casting algorithm
    
    Args:
        point_lat: Latitude of point to test
        point_lon: Longitude of point to test
        boundary: RectangularBoundary object
        tolerance_m: Edge tolerance in meters (default 0)
    
    Returns:
        dict: {
            'inside': bool,
            'distance_to_edge': float (meters),
            'nearest_edge': str ('north', 'south', 'east', 'west'),
            'method': str
        }
    """
    try:
        # Quick bounding box check first (optimization)
        bbox = boundary.get_bounding_box()
        
        # If point is clearly outside bounding box (with tolerance), reject quickly
        if tolerance_m == 0:
            if (point_lat < bbox['min_lat'] or point_lat > bbox['max_lat'] or
                point_lon < bbox['min_lon'] or point_lon > bbox['max_lon']):
                # Calculate distance to nearest edge
                dist_result = calculate_distance_to_boundary_edge(point_lat, point_lon, boundary)
                return {
                    'inside': False,
                    'distance_to_edge': dist_result['distance'],
                    'nearest_edge': dist_result['nearest_edge'],
                    'method': 'bounding_box_reject'
                }
        
        # Ray casting algorithm for point-in-polygon
        # Cast a ray from the point to infinity (to the right) and count intersections
        # Odd number of intersections = inside, even = outside
        
        # Define the four edges of the rectangle
        edges = [
            (boundary.nw, boundary.ne),  # North edge
            (boundary.ne, boundary.se),  # East edge
            (boundary.se, boundary.sw),  # South edge
            (boundary.sw, boundary.nw)   # West edge
        ]
        
        intersections = 0
        
        for edge_start, edge_end in edges:
            # Check if ray intersects this edge
            # Ray goes from (point_lat, point_lon) to (point_lat, +infinity)
            
            # Edge is from (y1, x1) to (y2, x2) where y=lat, x=lon
            y1, x1 = edge_start
            y2, x2 = edge_end
            
            # Check if edge crosses the horizontal line at point_lat
            if (y1 <= point_lat < y2) or (y2 <= point_lat < y1):
                # Calculate x-coordinate where edge crosses the horizontal line
                # Using linear interpolation
                if y2 != y1:  # Avoid division by zero
                    x_intersect = x1 + (point_lat - y1) * (x2 - x1) / (y2 - y1)
                    
                    # If intersection is to the right of the point, count it
                    if x_intersect > point_lon:
                        intersections += 1
        
        # Odd number of intersections = inside
        is_inside = (intersections % 2) == 1
        
        # Calculate distance to nearest edge
        dist_result = calculate_distance_to_boundary_edge(point_lat, point_lon, boundary)
        distance_to_edge = dist_result['distance']
        nearest_edge = dist_result['nearest_edge']
        
        # Apply tolerance if specified
        if tolerance_m > 0 and not is_inside:
            # If point is within tolerance of boundary, consider it inside
            if distance_to_edge <= tolerance_m:
                return {
                    'inside': True,
                    'distance_to_edge': distance_to_edge,
                    'nearest_edge': nearest_edge,
                    'method': 'tolerance_buffer_accepted'
                }
        
        return {
            'inside': is_inside,
            'distance_to_edge': distance_to_edge,
            'nearest_edge': nearest_edge,
            'method': 'ray_casting'
        }
        
    except Exception as e:
        # Fallback: use simple bounding box check
        bbox = boundary.get_bounding_box()
        is_inside = (bbox['min_lat'] <= point_lat <= bbox['max_lat'] and
                    bbox['min_lon'] <= point_lon <= bbox['max_lon'])
        
        return {
            'inside': is_inside,
            'distance_to_edge': 0,
            'nearest_edge': 'unknown',
            'method': f'fallback_bounding_box (error: {str(e)})'
        }



def calculate_distance_to_boundary_edge(point_lat: float, point_lon: float, 
                                        boundary: RectangularBoundary) -> Dict:
    """
    Calculate shortest distance from point to any boundary edge
    
    Args:
        point_lat: Point latitude
        point_lon: Point longitude
        boundary: RectangularBoundary object
    
    Returns:
        dict: {
            'distance': float (meters),
            'nearest_edge': str,
            'nearest_point_on_edge': (lat, lon)
        }
    """
    try:
        # Calculate distance to each edge
        edges = {
            'north': (boundary.nw, boundary.ne),
            'east': (boundary.ne, boundary.se),
            'south': (boundary.se, boundary.sw),
            'west': (boundary.sw, boundary.nw)
        }
        
        min_distance = float('inf')
        nearest_edge = None
        nearest_point = None
        
        for edge_name, (start, end) in edges.items():
            # Calculate perpendicular distance from point to line segment
            dist, closest_point = _distance_to_line_segment(
                point_lat, point_lon,
                start[0], start[1],
                end[0], end[1]
            )
            
            if dist < min_distance:
                min_distance = dist
                nearest_edge = edge_name
                nearest_point = closest_point
        
        return {
            'distance': min_distance,
            'nearest_edge': nearest_edge,
            'nearest_point_on_edge': nearest_point
        }
        
    except Exception as e:
        # Fallback: distance to center
        center = boundary.get_center()
        distance = calculate_distance(point_lat, point_lon, center[0], center[1])
        return {
            'distance': distance,
            'nearest_edge': 'unknown',
            'nearest_point_on_edge': center
        }


def _distance_to_line_segment(px: float, py: float, 
                              x1: float, y1: float, 
                              x2: float, y2: float) -> Tuple[float, Tuple[float, float]]:
    """
    Calculate distance from point (px, py) to line segment (x1,y1)-(x2,y2)
    
    Args:
        px, py: Point coordinates (lat, lon)
        x1, y1: Line segment start (lat, lon)
        x2, y2: Line segment end (lat, lon)
    
    Returns:
        Tuple of (distance in meters, closest point on segment)
    """
    # Calculate the parameter t that represents the closest point on the line segment
    # t = 0 means closest to start, t = 1 means closest to end
    
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        # Line segment is actually a point
        distance = calculate_distance(px, py, x1, y1)
        return distance, (x1, y1)
    
    # Calculate t
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    
    # Clamp t to [0, 1] to stay on the line segment
    t = max(0, min(1, t))
    
    # Calculate closest point on segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    # Calculate distance
    distance = calculate_distance(px, py, closest_x, closest_y)
    
    return distance, (closest_x, closest_y)


def apply_tolerance_buffer(point_lat: float, point_lon: float, 
                           boundary: RectangularBoundary, 
                           tolerance_m: float, 
                           gps_accuracy: float) -> Dict:
    """
    Apply tolerance buffer for edge cases
    
    Logic:
    - If point is within tolerance_m of boundary edge
    - AND GPS accuracy is <= 10m
    - Then accept the check-in
    
    Args:
        point_lat: Point latitude
        point_lon: Point longitude
        boundary: RectangularBoundary object
        tolerance_m: Tolerance in meters
        gps_accuracy: GPS accuracy in meters
    
    Returns:
        dict: {
            'accepted': bool,
            'reason': str,
            'applied_tolerance': bool
        }
    """
    try:
        # Check if point is inside boundary
        result = point_in_rectangular_boundary(point_lat, point_lon, boundary, tolerance_m=0)
        
        if result['inside']:
            return {
                'accepted': True,
                'reason': 'inside_boundary',
                'applied_tolerance': False,
                'distance_to_edge': result['distance_to_edge']
            }
        
        # Point is outside - check if within tolerance
        distance_to_edge = result['distance_to_edge']
        
        if distance_to_edge <= tolerance_m:
            # Within tolerance distance
            if gps_accuracy <= 10:
                # GPS is good enough to trust tolerance
                return {
                    'accepted': True,
                    'reason': 'within_tolerance_with_good_gps',
                    'applied_tolerance': True,
                    'distance_to_edge': distance_to_edge,
                    'gps_accuracy': gps_accuracy
                }
            else:
                # GPS not accurate enough for tolerance
                return {
                    'accepted': False,
                    'reason': 'within_tolerance_but_poor_gps',
                    'applied_tolerance': False,
                    'distance_to_edge': distance_to_edge,
                    'gps_accuracy': gps_accuracy
                }
        else:
            # Outside tolerance
            return {
                'accepted': False,
                'reason': 'outside_tolerance',
                'applied_tolerance': False,
                'distance_to_edge': distance_to_edge
            }
            
    except Exception as e:
        return {
            'accepted': False,
            'reason': f'error: {str(e)}',
            'applied_tolerance': False
        }



def validate_gps_accuracy(gps_accuracy: float, threshold: float, 
                         point_lat: float, point_lon: float, 
                         boundary: RectangularBoundary) -> Dict:
    """
    Validate if GPS accuracy is acceptable for boundary check
    
    Args:
        gps_accuracy: GPS accuracy in meters
        threshold: Maximum acceptable accuracy
        point_lat, point_lon: Point coordinates
        boundary: RectangularBoundary object
    
    Returns:
        dict: {
            'acceptable': bool,
            'reason': str,
            'uncertainty_intersects_boundary': bool
        }
    """
    try:
        # Check if GPS accuracy meets threshold
        if gps_accuracy > threshold:
            return {
                'acceptable': False,
                'reason': f'gps_accuracy_exceeds_threshold ({gps_accuracy}m > {threshold}m)',
                'gps_accuracy': gps_accuracy,
                'threshold': threshold,
                'uncertainty_intersects_boundary': False
            }
        
        # Check if GPS uncertainty circle intersects with boundary
        # This is important for edge cases
        result = point_in_rectangular_boundary(point_lat, point_lon, boundary)
        
        if result['inside']:
            # Point is inside - check if uncertainty extends outside
            distance_to_edge = result['distance_to_edge']
            
            if gps_accuracy > distance_to_edge:
                # Uncertainty circle extends outside boundary
                return {
                    'acceptable': True,
                    'reason': 'inside_but_uncertainty_extends_outside',
                    'gps_accuracy': gps_accuracy,
                    'threshold': threshold,
                    'distance_to_edge': distance_to_edge,
                    'uncertainty_intersects_boundary': True
                }
            else:
                # Fully inside with good margin
                return {
                    'acceptable': True,
                    'reason': 'inside_with_good_margin',
                    'gps_accuracy': gps_accuracy,
                    'threshold': threshold,
                    'distance_to_edge': distance_to_edge,
                    'uncertainty_intersects_boundary': False
                }
        else:
            # Point is outside
            distance_to_edge = result['distance_to_edge']
            
            if gps_accuracy >= distance_to_edge:
                # Uncertainty circle intersects boundary
                return {
                    'acceptable': False,
                    'reason': 'outside_but_uncertainty_intersects_boundary',
                    'gps_accuracy': gps_accuracy,
                    'threshold': threshold,
                    'distance_to_edge': distance_to_edge,
                    'uncertainty_intersects_boundary': True
                }
            else:
                # Clearly outside
                return {
                    'acceptable': False,
                    'reason': 'outside_boundary',
                    'gps_accuracy': gps_accuracy,
                    'threshold': threshold,
                    'distance_to_edge': distance_to_edge,
                    'uncertainty_intersects_boundary': False
                }
                
    except Exception as e:
        return {
            'acceptable': False,
            'reason': f'validation_error: {str(e)}',
            'gps_accuracy': gps_accuracy,
            'threshold': threshold,
            'uncertainty_intersects_boundary': False
        }

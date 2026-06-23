"""
Tests for Safe Cycle GPX validation.
 
Test structure:
1. Utility function tests (haversine, de-duplication)
2. Validation logic tests (speed anomalies, intersections)
3. Data parsing tests (GPX extraction)
"""
 
import pytest
from safe_cycle import (
    haversine_dist,
    nonduplicate_intersections,
    check_speed_anomalies,
    check_self_intersections,
    calculate_segment_data
)
from shapely.geometry import LineString

class TestHaversineDist:
    """Test distances between two points"""

    def test_haversine_zero(self):
        pass

    def test_known_distance(self):
        pass
"""
Branch Coverage Test Suite for car_rental_rate.py
Covers all decision branches, compound boolean conditions, loops, and edge cases.
"""

import pytest
from car_rental_rate import process_rental_fleet, check_fleet_telematics


# ============================================================================
# Branch Coverage Tests for process_rental_fleet
# ============================================================================

def test_branch_invalid_rentals_type():
    """Branch: if not isinstance(rentals, list) -> True (raises ValueError)"""
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet("not-a-list", 10.0)


def test_branch_negative_admin_fee():
    """Branch: if base_admin_fee < 0 -> True (raises ValueError)"""
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet([], -1.0)


def test_branch_empty_rentals_list():
    """Branch: for rental in rentals -> loop doesn't execute (empty list)
       Branch: if total_revenue == 0.0 -> True (returns EMPTY_BATCH)
    """
    result = process_rental_fleet([], 10.0)
    assert result == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}


def test_branch_unconfirmed_rental():
    """Branch: if not rental.get('is_confirmed', False) -> True (continue loop)"""
    rentals = [
        {"is_confirmed": False, "vehicle_type": "economy", "days": 2}
    ]
    result = process_rental_fleet(rentals, 10.0)
    assert result["status"] == "EMPTY_BATCH"


def test_branch_non_positive_days():
    """Branch: if days <= 0 -> True (increments risk_flags and continue)"""
    rentals = [
        {"is_confirmed": True, "vehicle_type": "economy", "days": 0}
    ]
    result = process_rental_fleet(rentals, 10.0)
    assert result["status"] == "EMPTY_BATCH"


def test_branch_vehicle_economy_and_driver_age_ge_25():
    """Branch: vehicle_type == 'economy' (else branch of rate check)
       Branch: trip_segments empty loop
       Branch: if driver_age < 25 -> False (no surcharge)
       Branch: if risk_flags > 4 -> False
       Branch: if total_revenue == 0.0 -> False
       Status: STANDARD
    """
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 25,
            "days": 2,
            "trip_segments": []
        }
    ]
    # daily: 40 * 2 + 10 = 90.0
    result = process_rental_fleet(rentals, 10.0)
    assert result["total_revenue"] == 90.0
    assert result["status"] == "STANDARD"


def test_branch_vehicle_luxury_under_21_long_trip():
    """Branch: vehicle_type == 'luxury' (daily_rate = 120.0)
       Branch: miles > 300 -> True (risk_flags += 1)
       Branch: if driver_age < 21 -> True (contract_total += 250.0, break)
       Branch: if driver_age < 25 -> True, ternary luxury (50.0 * days)
    """
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "luxury",
            "driver_age": 20,
            "days": 1,
            "trip_segments": [350, 50]  # second segment skipped due to break
        }
    ]
    # daily: 120 * 1 + 10 = 130
    # segment 350: + 250 -> 380, break
    # surcharge: + 50 * 1 -> 430.0
    result = process_rental_fleet(rentals, 10.0)
    assert result["total_revenue"] == 430.0
    assert result["status"] == "STANDARD"


def test_branch_vehicle_suv_age_21_to_24_long_trip():
    """Branch: vehicle_type == 'suv' (daily_rate = 70.0)
       Branch: miles > 300 -> True (risk_flags += 1)
       Branch: if driver_age < 21 -> False (contract_total += miles * 0.40)
       Branch: if driver_age < 25 -> True, ternary non-luxury (20.0 * days)
    """
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "suv",
            "driver_age": 22,
            "days": 2,
            "trip_segments": [400]
        }
    ]
    # daily: 70 * 2 + 20 = 160
    # miles: 400 * 0.40 = 160 -> 320
    # surcharge: + 20 * 2 = 40 -> 360.0
    result = process_rental_fleet(rentals, 20.0)
    assert result["total_revenue"] == 360.0
    assert result["status"] == "STANDARD"


def test_branch_trip_segments_negative_and_normal():
    """Branch: miles < 0 -> True (increments risk_flags, continue)
       Branch: miles <= 300 -> True (miles * 0.20)
    """
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 30,
            "days": 1,
            "trip_segments": [-50, 150]
        }
    ]
    # daily: 40 * 1 + 5 = 45
    # miles: -50 skipped (risk_flag=1), 150 * 0.20 = 30 -> 75.0
    result = process_rental_fleet(rentals, 5.0)
    assert result["total_revenue"] == 75.0
    assert result["status"] == "STANDARD"


def test_branch_high_risk_audit():
    """Branch: if risk_flags > 4 -> True (status = HIGH_RISK_AUDIT)"""
    rentals = [
        {"is_confirmed": True, "vehicle_type": "economy", "days": -1},  # flag 1
        {"is_confirmed": True, "vehicle_type": "economy", "days": -2},  # flag 2
        {"is_confirmed": True, "vehicle_type": "economy", "days": -3},  # flag 3
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 28,
            "days": 1,
            "trip_segments": [-10, 500]  # flag 4, flag 5
        }
    ]
    result = process_rental_fleet(rentals, 10.0)
    assert result["status"] == "HIGH_RISK_AUDIT"


# ============================================================================
# Branch Coverage Tests for check_fleet_telematics
# ============================================================================

def test_branch_telematics_empty():
    """Branch: if not telematics_matrix -> True (NO_DATA)"""
    assert check_fleet_telematics([]) == "NO_DATA"
    assert check_fleet_telematics(None) == "NO_DATA"


def test_branch_telematics_ground_vehicle():
    """Branch: speed > 100 -> True
       Branch: speeding_streak >= 2 -> True (GROUND_VEHICLE)
    """
    matrix = [
        [70, 105, 115, 80]
    ]
    assert check_fleet_telematics(matrix) == "GROUND_VEHICLE"


def test_branch_telematics_safe_reset_streak():
    """Branch: speed > 100 -> False (speeding_streak = 0)
       Branch: loops complete without streak >= 2 -> returns SAFE
    """
    matrix = [
        [],  # empty vehicle log (for loop doesn't execute)
        [90, 105, 85, 105, 75]  # non-consecutive speeding
    ]
    assert check_fleet_telematics(matrix) == "SAFE"

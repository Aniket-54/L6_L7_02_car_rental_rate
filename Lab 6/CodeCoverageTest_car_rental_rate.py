import pytest
from car_rental_rate import process_rental_fleet, check_fleet_telematics

def test_invalid_rentals_input():
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet("invalid_rentals_type", 10.0)

def test_invalid_admin_fee():
    with pytest.raises(ValueError, match="Invalid rental list or admin fee"):
        process_rental_fleet([], -5.0)

def test_single_economy_rental():
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 30,
            "days": 2,
            "trip_segments": [100]
        }
    ]
    result = process_rental_fleet(rentals, 10.0)
    assert result["total_revenue"] == 110.0
    assert result["status"] == "STANDARD"

def test_unconfirmed_and_invalid_days():
    rentals = [
        {"is_confirmed": False, "vehicle_type": "suv", "days": 3},
        {"is_confirmed": True, "vehicle_type": "suv", "days": 0}
    ]
    result = process_rental_fleet(rentals, 15.0)
    assert result["total_revenue"] == 0.0
    assert result["status"] == "EMPTY_BATCH"

def test_luxury_young_driver_break_on_long_trip():
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "luxury",
            "driver_age": 20,
            "days": 2,
            "trip_segments": [350, 100]
        }
    ]
    # base = 120 * 2 + 20 = 260
    # miles 350 > 300, driver_age < 21 -> contract_total += 250 (510), break
    # driver_age < 25 & luxury -> + 50 * 2 = 100 -> 610.0
    result = process_rental_fleet(rentals, 20.0)
    assert result["total_revenue"] == 610.0
    assert result["status"] == "STANDARD"

def test_suv_under_25_miles_over_300():
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "suv",
            "driver_age": 23,
            "days": 1,
            "trip_segments": [400]
        }
    ]
    # daily: 70 * 1 + 10 = 80
    # miles: 400 * 0.40 = 160 -> 240
    # driver_age < 25 (suv): 20 * 1 = 20 -> 260.0
    result = process_rental_fleet(rentals, 10.0)
    assert result["total_revenue"] == 260.0
    assert result["status"] == "STANDARD"

def test_negative_miles_and_high_risk_audit():
    rentals = [
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 22,
            "days": 0  # flag 1
        },
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 22,
            "days": 0  # flag 2
        },
        {
            "is_confirmed": True,
            "vehicle_type": "economy",
            "driver_age": 22,
            "days": 1,
            "trip_segments": [-10, -20, 350]  # flags 3, 4, 5
        }
    ]
    result = process_rental_fleet(rentals, 10.0)
    assert result["status"] == "HIGH_RISK_AUDIT"

def test_telematics_no_data():
    assert check_fleet_telematics([]) == "NO_DATA"

def test_telematics_ground_vehicle():
    matrix = [[80, 110, 120]]
    assert check_fleet_telematics(matrix) == "GROUND_VEHICLE"

def test_telematics_safe():
    matrix = [
        [50, 60, 70],
        [105, 90, 105]  # streak resets
    ]
    assert check_fleet_telematics(matrix) == "SAFE"

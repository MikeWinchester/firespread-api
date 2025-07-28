def calculate_spread_rate(
    wind_speed: float,
    wind_direction: float,
    humidity: float,
    slope: float,
    vegetation_type: str
) -> float:
    vegetation_factors = {
        "forest": 0.7,
        "grassland": 0.3,
        "shrubland": 0.5,
        "agricultural": 0.4,
        "urban": 0.1
    }
    
    base_rate = vegetation_factors.get(vegetation_type, 0.5)
    wind_factor = 1 + (wind_speed / 20) * 0.5
    humidity_factor = max(0, 1 - (humidity / 100))
    slope_factor = 1 + (slope / 45) * 0.3
    
    spread_rate = base_rate * wind_factor * humidity_factor * slope_factor
    return min(max(spread_rate, 0), 0.9)
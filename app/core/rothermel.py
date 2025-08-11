"""
Rothermel Fire Spread Model Implementation
Based on the mathematical model for fire spread prediction
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict
import logging

from app.models.simulation import VegetationType, SimulationParameters

logger = logging.getLogger(__name__)


@dataclass
class FuelProperties:
    """Physical and chemical properties of different fuel types"""
    
    # Fuel load (kg/m²) - amount of combustible material
    fuel_load: float
    
    # Surface area to volume ratio (1/cm) - affects burning rate
    surface_area_volume: float
    
    # Fuel bed depth (m) - height of fuel layer
    fuel_depth: float
    
    # Moisture content of extinction (%) - moisture level that prevents combustion
    moisture_extinction: float
    
    # Heat content (kJ/kg) - energy released during combustion
    heat_content: float
    
    # Fuel particle density (kg/m³)
    fuel_density: float
    
    # Fuel bed bulk density (kg/m³)
    bulk_density: float
    
    # Mineral content (fraction)
    mineral_content: float = 0.0555  # Default 5.55%


class RothermelModel:
    """
    Implementation of Rothermel's surface fire spread model
    
    The model calculates fire spread rate based on:
    - Fuel properties (load, moisture, structure)
    - Weather conditions (wind, humidity)
    - Topography (slope)
    
    Reference: Rothermel, R.C. 1972. A mathematical model for predicting fire spread
    """
    
    # Fuel model properties for different vegetation types
    # Based on standard fuel models (Rothermel 1972, Anderson 1982)
    FUEL_PROPERTIES: Dict[VegetationType, FuelProperties] = {
        
        VegetationType.FOREST: FuelProperties(
            fuel_load=0.45,          # Dense forest fuel
            surface_area_volume=3500, # Moderate surface area
            fuel_depth=0.30,         # Tall fuel bed
            moisture_extinction=25.0, # Forest retains moisture
            heat_content=18622,      # Standard wood heat content
            fuel_density=512,        # Wood density
            bulk_density=0.20        # Compact fuel bed
        ),
        
        VegetationType.GRASSLAND: FuelProperties(
            fuel_load=0.15,          # Light grass fuel
            surface_area_volume=11000, # High surface area (fine fuels)
            fuel_depth=0.10,         # Low fuel bed
            moisture_extinction=15.0, # Grass dries quickly
            heat_content=18622,      # Grass heat content
            fuel_density=200,        # Light grass density
            bulk_density=0.40        # Loose fuel bed
        ),
        
        VegetationType.SHRUBLAND: FuelProperties(
            fuel_load=0.35,          # Medium shrub fuel
            surface_area_volume=6000, # Medium surface area
            fuel_depth=0.20,         # Medium fuel bed
            moisture_extinction=20.0, # Moderate moisture retention
            heat_content=18622,      # Standard shrub heat content
            fuel_density=350,        # Shrub wood density
            bulk_density=0.30        # Medium fuel bed density
        ),
        
        VegetationType.AGRICULTURAL: FuelProperties(
            fuel_load=0.08,          # Light crop residue
            surface_area_volume=8000, # Fine agricultural residue
            fuel_depth=0.05,         # Very low fuel bed
            moisture_extinction=12.0, # Dry crop residue
            heat_content=18622,      # Crop residue heat content
            fuel_density=150,        # Light agricultural density
            bulk_density=0.50        # Sparse fuel bed
        ),
        
        VegetationType.URBAN: FuelProperties(
            fuel_load=0.02,          # Limited urban vegetation
            surface_area_volume=5000, # Mixed urban fuels
            fuel_depth=0.02,         # Minimal fuel bed
            moisture_extinction=10.0, # Urban areas dry quickly
            heat_content=20000,      # Mixed materials (higher)
            fuel_density=100,        # Light urban fuel density
            bulk_density=0.10        # Very sparse fuel bed
        )
    }
    
    @staticmethod
    def calculate_moisture_damping_coefficient(moisture_content: float, fuel_props: FuelProperties) -> float:
        """
        Calculate moisture damping coefficient (η_M)
        
        Args:
            moisture_content: Fuel moisture content (%)
            fuel_props: Fuel properties
            
        Returns:
            Moisture damping coefficient (0-1)
        """
        # Moisture ratio
        moisture_ratio = moisture_content / fuel_props.moisture_extinction
        
        # Rothermel moisture damping equation
        if moisture_ratio < 1.0:
            eta_M = 1.0 - 2.59 * moisture_ratio + 5.11 * (moisture_ratio ** 2) - 3.52 * (moisture_ratio ** 3)
            eta_M = max(0.0, min(1.0, eta_M))
        else:
            eta_M = 0.0  # No burning possible above extinction moisture
        
        return eta_M
    
    @staticmethod
    def calculate_mineral_damping_coefficient(fuel_props: FuelProperties) -> float:
        """
        Calculate mineral damping coefficient (η_s)
        
        Args:
            fuel_props: Fuel properties
            
        Returns:
            Mineral damping coefficient (0-1)
        """
        # Rothermel mineral damping equation
        eta_s = 0.174 * (fuel_props.mineral_content ** -0.19)
        return min(1.0, eta_s)
    
    @staticmethod
    def calculate_reaction_intensity(fuel_props: FuelProperties, eta_M: float, eta_s: float) -> float:
        """
        Calculate reaction intensity (I_R) - rate of heat release per unit area
        
        Args:
            fuel_props: Fuel properties
            eta_M: Moisture damping coefficient
            eta_s: Mineral damping coefficient
            
        Returns:
            Reaction intensity (kW/m²)
        """
        # Packing ratio (β) - fraction of fuel bed volume occupied by fuel
        beta = fuel_props.bulk_density / fuel_props.fuel_density
        
        # Optimum packing ratio (β_op)
        beta_op = 3.348 * (fuel_props.surface_area_volume ** -0.8189)
        
        # Maximum reaction velocity (γ_max)
        gamma_max = fuel_props.surface_area_volume ** 1.5 / (495.0 + 0.0594 * (fuel_props.surface_area_volume ** 1.5))
        
        # Reaction velocity (γ)
        if beta > 0 and beta_op > 0:
            A = 133.0 * (fuel_props.surface_area_volume ** -0.7913)
            gamma = gamma_max * ((beta / beta_op) ** A) * math.exp(A * (1.0 - beta / beta_op))
        else:
            gamma = 0.0
        
        # Reaction intensity
        I_R = gamma * fuel_props.heat_content * eta_M * eta_s
        
        return max(0.0, I_R)
    
    @staticmethod
    def calculate_propagating_flux_ratio(fuel_props: FuelProperties) -> float:
        """
        Calculate propagating flux ratio (ξ) - fraction of reaction intensity 
        that contributes to fire spread
        
        Args:
            fuel_props: Fuel properties
            
        Returns:
            Propagating flux ratio (dimensionless)
        """
        # Packing ratio
        beta = fuel_props.bulk_density / fuel_props.fuel_density
        
        # Propagating flux ratio equation
        exp_term = (0.792 + 0.681 * math.sqrt(fuel_props.surface_area_volume)) * (beta + 0.1)
        denominator = 192.0 + 0.2595 * fuel_props.surface_area_volume
        
        xi = math.exp(exp_term) / denominator
        
        return xi
    
    @staticmethod
    def calculate_heat_of_preignition(moisture_content: float) -> float:
        """
        Calculate heat of preignition (Q_ig) - heat required to ignite fuel
        
        Args:
            moisture_content: Fuel moisture content (%)
            
        Returns:
            Heat of preignition (kJ/kg)
        """
        # Rothermel heat of preignition equation
        Q_ig = 250.0 + 1116.0 * (moisture_content / 100.0)
        
        return Q_ig
    
    @staticmethod
    def calculate_base_spread_rate(parameters: SimulationParameters, moisture_content: float = None) -> float:
        """
        Calculate base fire spread rate (no wind, no slope) using Rothermel model
        
        Args:
            parameters: Simulation parameters
            moisture_content: Fuel moisture content (%), defaults to humidity-derived value
            
        Returns:
            Base rate of spread (m/min)
        """
        fuel_props = RothermelModel.FUEL_PROPERTIES[parameters.vegetationType]
        
        # Calculate moisture content from humidity if not provided
        if moisture_content is None:
            # Inverse relationship: high humidity = high fuel moisture
            moisture_content = parameters.humidity * 0.5  # Simplified relationship
        
        # Ensure moisture content is within reasonable bounds
        moisture_content = max(1.0, min(moisture_content, fuel_props.moisture_extinction - 1.0))
        
        # Calculate damping coefficients
        eta_M = RothermelModel.calculate_moisture_damping_coefficient(moisture_content, fuel_props)
        eta_s = RothermelModel.calculate_mineral_damping_coefficient(fuel_props)
        
        # Calculate reaction intensity
        I_R = RothermelModel.calculate_reaction_intensity(fuel_props, eta_M, eta_s)
        
        if I_R <= 0:
            return 0.0
        
        # Calculate propagating flux ratio
        xi = RothermelModel.calculate_propagating_flux_ratio(fuel_props)
        
        # Calculate heat of preignition
        Q_ig = RothermelModel.calculate_heat_of_preignition(moisture_content)
        
        # Base rate of spread (Rothermel equation)
        R_0 = (I_R * xi) / (fuel_props.bulk_density * Q_ig)
        
        return max(0.0, R_0)
    
    @staticmethod
    def calculate_wind_coefficient(parameters: SimulationParameters) -> float:
        """
        Calculate wind coefficient (φ_w) - dimensionless wind factor
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            Wind coefficient (≥ 1.0)
        """
        fuel_props = RothermelModel.FUEL_PROPERTIES[parameters.vegetationType]
        
        if parameters.windSpeed <= 0:
            return 1.0
        
        # Convert wind speed to ft/min (Rothermel units)
        wind_ft_per_min = parameters.windSpeed * 3.28084 * 60  # m/s to ft/min
        
        # Packing ratio
        beta = fuel_props.bulk_density / fuel_props.fuel_density
        
        # Wind coefficient calculation
        # B and C are empirical coefficients
        B = 0.02526 * (fuel_props.surface_area_volume ** 0.54)
        C = 7.47 * math.exp(-0.133 * (fuel_props.surface_area_volume ** 0.55))
        E = 0.715 * math.exp(-3.59e-4 * fuel_props.surface_area_volume)
        
        phi_w = C * (wind_ft_per_min ** B) * ((beta / 0.0189) ** (-E))
        
        return max(1.0, phi_w)
    
    @staticmethod
    def calculate_slope_coefficient(parameters: SimulationParameters) -> float:
        """
        Calculate slope coefficient (φ_s) - dimensionless slope factor
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            Slope coefficient (≥ 1.0)
        """
        if parameters.slope <= 0:
            return 1.0
        
        # Convert slope to radians
        slope_radians = math.radians(parameters.slope)
        
        # Slope coefficient (Rothermel equation)
        phi_s = 5.275 * (slope_radians ** 2)
        
        return max(1.0, phi_s)
    
    @staticmethod
    def calculate_spread_rate(parameters: SimulationParameters, moisture_content: float = None) -> float:
        """
        Calculate total fire spread rate including wind and slope effects
        
        Args:
            parameters: Simulation parameters
            moisture_content: Fuel moisture content (%), optional
            
        Returns:
            Rate of spread (m/min)
        """
        try:
            # Calculate base spread rate
            R_0 = RothermelModel.calculate_base_spread_rate(parameters, moisture_content)
            
            if R_0 <= 0:
                return 0.0
            
            # Calculate wind and slope coefficients
            phi_w = RothermelModel.calculate_wind_coefficient(parameters)
            phi_s = RothermelModel.calculate_slope_coefficient(parameters)
            
            # Total rate of spread
            R = R_0 * (1.0 + phi_w + phi_s)
            
            logger.debug(f"Spread rate calculation: R_0={R_0:.4f}, φ_w={phi_w:.4f}, φ_s={phi_s:.4f}, R={R:.4f}")
            
            return max(0.0, R)
            
        except Exception as e:
            logger.error(f"Error calculating spread rate: {e}")
            return 0.0
    
    @staticmethod
    def calculate_directional_spread_rate(parameters: SimulationParameters, direction_degrees: float, 
                                        moisture_content: float = None) -> float:
        """
        Calculate spread rate in a specific direction considering wind direction
        
        Args:
            parameters: Simulation parameters
            direction_degrees: Direction of spread (0=North, 90=East, etc.)
            moisture_content: Fuel moisture content (%), optional
            
        Returns:
            Directional rate of spread (m/min)
        """
        # Base spread rate
        R_0 = RothermelModel.calculate_base_spread_rate(parameters, moisture_content)
        
        if R_0 <= 0:
            return 0.0
        
        # Slope coefficient (assumed uniform in all directions for simplicity)
        phi_s = RothermelModel.calculate_slope_coefficient(parameters)
        
        # Wind coefficient varies by direction
        phi_w_max = RothermelModel.calculate_wind_coefficient(parameters)
        
        # Calculate wind effect based on direction
        wind_angle_diff = abs(direction_degrees - parameters.windDirection)
        if wind_angle_diff > 180:
            wind_angle_diff = 360 - wind_angle_diff
        
        # Cosine law for wind effect (maximum in wind direction, minimum opposite)
        wind_factor = math.cos(math.radians(wind_angle_diff))
        phi_w_directional = 1.0 + (phi_w_max - 1.0) * max(0, wind_factor)
        
        # Total directional spread rate
        R_directional = R_0 * (1.0 + phi_w_directional + phi_s)
        
        return max(0.0, R_directional)
    
    @staticmethod
    def calculate_flame_length(intensity: float) -> float:
        """
        Calculate flame length from fireline intensity (Byram's equation)
        
        Args:
            intensity: Fireline intensity (kW/m)
            
        Returns:
            Flame length (m)
        """
        if intensity <= 0:
            return 0.0
        
        # Byram's flame length equation: L = 0.0775 * I^0.46
        flame_length = 0.0775 * (intensity ** 0.46)
        
        return max(0.0, flame_length)
    
    @staticmethod
    def calculate_fireline_intensity(spread_rate: float, fuel_props: FuelProperties, 
                                   reaction_intensity: float) -> float:
        """
        Calculate fireline intensity (I) - heat release rate per unit length of fire front
        
        Args:
            spread_rate: Rate of spread (m/min)
            fuel_props: Fuel properties
            reaction_intensity: Reaction intensity (kW/m²)
            
        Returns:
            Fireline intensity (kW/m)
        """
        if spread_rate <= 0 or reaction_intensity <= 0:
            return 0.0
        
        # Convert spread rate to m/s
        spread_rate_ms = spread_rate / 60.0
        
        # Fireline intensity = heat per unit area × spread rate × fuel bed depth
        I = reaction_intensity * spread_rate_ms * fuel_props.fuel_depth
        
        return max(0.0, I)
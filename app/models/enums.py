from enum import Enum

class VegetationType(str, Enum):
    forest = "forest"
    grassland = "grassland"
    shrubland = "shrubland"
    agricultural = "agricultural"
    urban = "urban"

class FireState(str, Enum):
    unburned = "unburned"
    burning = "burning"
    burned = "burned"
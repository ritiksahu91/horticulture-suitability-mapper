
slope_rules = [
    (0, 5, 7),
    (5, 10, 2),
    (10, 90, 1)
]

# Soil Type (string match, exact categories handled separately)
soil_rules = {
    1: 6,
    5: 6,
    8: 6,
    12: 6,
    11: 3,
    3: 3,
    10: 3,
    2: 1,
    7: 1,
    9: 1,
    4: 1,
    6: 1,
    13: 1
}



# Soil Organic Carbon (t/ha)
soc_rules = [
    (15, float('inf'), 5),
    (8, 15, 3),
    (0, 8, 2)
]

# Rainfall (mm/year)
rainfall_rules = [
    (800, 1200, 6),
    (1200, float('inf'), 3),
    (0, 800, 1)
]

# Mean Temperature (°C)
temp_rules = [
    (25, 32, 6),
    (20, 25, 3),
    (32, 35, 3),
    (-50, 20, 1),  # edge case for lower temp
    (35, 60, 1)    # edge case for higher temp
]

# Water Body Distance (m)
water_rules = [
    (0, 500, 7),
    (500, 1000, 2),
    (1000, float('inf'), 1)
]

# Road Distance (m)
road_rules = [
    (0, 1000, 5),
    (1000, 3000, 3),
    (3000, float('inf'), 2)
]

# Weights for each factor
weights = {
    'slope': 0.38,
    'soil': 0.28,
    'soc': 0.15,
    'rainfall': 0.09,
    'temperature': 0.05,
    'water': 0.03,
    'road': 0.02
}
reclass1_rules = {
    'slope': slope_rules,
    'soil': soil_rules,
    'soc': soc_rules,
    'rainfall': rainfall_rules,
    'temperature': temp_rules,
    'water': water_rules,
    'road': road_rules
}

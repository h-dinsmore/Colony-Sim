import pygame as pg

RES = (1284, 720)
FPS = 60

KEY_BINDINGS = {
    '-x': pg.K_a,
    '+x': pg.K_d,
    '-y': pg.K_w,
    '+y': pg.K_s,
    'drop item': pg.K_BACKSPACE,
    'reset zoom': pg.K_z,
    'elevation view': pg.K_RALT
}

TILE_SIZE = 16
MAP_TILE_SIZE = (128, 256, 16)
MAP_PX_SIZE = (MAP_TILE_SIZE[0] * TILE_SIZE, MAP_TILE_SIZE[1] * TILE_SIZE, MAP_TILE_SIZE[2] * TILE_SIZE)
SEA_LVL = MAP_TILE_SIZE[2] // 3
Z_DIF_ICONS = {
    (1, 3): 'foothills',
    (3, 8): 'hills',
    (8, 13): 'mountains',
    (13, 16): 'mountain peak',
    (-1, -8): 'shallow valley',
    (-8, -16): 'deep valley'
}

WORLD_GEN_NOISE = {
    'elev': {'scale': 96, 'octaves': 5, 'persistence': 0.7, 'lacunarity': 2.0},
    'max z': {'scale': 88, 'octaves': 3, 'persistence': 0.7, 'lacunarity': 2.0},
    'temp': {'scale': 192, 'octaves': 3, 'persistence': 0.4, 'lacunarity': 2.0},
    'precip': {'scale': 160, 'octaves': 3, 'persistence': 0.5, 'lacunarity': 2.0},
    'veg': {'scale': 80, 'octaves': 4, 'persistence': 0.6, 'lacunarity': 2.0},
    #'cont': {},
    #'erosion': {},
    #'rand': {},
    #'fossils': {}
}

BIOMES = {
    'tundra': {
        'geo noise': {'elev': (0.0, 0.15), 'temp': (0.0, 0.1), 'precip': (0.0, 0.1), 'veg': (0.0, 0.15)},

        'surface noise': {'scale': 300, 'octaves': 3, 'persistence': 1.2, 'lacunarity': 1.5},

        'surface terrain': {'snow': (0.0, 0.3), 'grass': (0.3, 0.4), 'small rock': (0.4, 0.5), 'large rock': (0.5, 0.55), 'plant': (0.55, 0.6), 'small mushroom': (0.6, 0.65)},

        'cave noise': {'scale': 70.0, 'octaves': 2, 'persistence': 0.6, 'lacunarity': 1.8, 'threshold': 0.35},

        'z layers': {
            0.2: {'stone': (0.0, 0.3), 'ice': (0.3, 0.5), 'fossil': (0.5, 0.65), 'iron': (0.65, 0.8), 'silver': (0.8, 0.95), 'sapphire': (0.95, 1.0)},

            0.4: {'stone': (0.0, 0.35), 'obsidian': (0.35, 0.55), 'iron': (0.55, 0.75), 'coal': (0.75, 0.88), 'silver': (0.88, 0.97), 'sapphire': (0.97, 1.0)},
           
            0.6: {'stone': (0.0, 0.4), 'ice': (0.4, 0.6), 'coal': (0.6, 0.8), 'fossil': (0.8, 0.93), 'silver': (0.93, 1.0)},

            0.8: {'ice': (0.0, 0.5), 'dirt': (0.5, 0.75), 'stone': (0.75, 0.95), 'fossil': (0.95, 1.0)},
            
            1.0: {'ice': (0.0, 0.65), 'dirt': (0.65, 0.9), 'stone': (0.9, 1.0)},
        },
    },

    'taiga': {
        'geo noise': {'elev': (0.6, 0.75), 'temp': (0.15, 0.3), 'precip': (0.3, 0.5), 'veg': (0.45, 0.6)},

        'surface noise': {'scale': 150, 'octaves': 4, 'persistence': 1.3, 'lacunarity': 1.6},

        'surface terrain': {'tree': (0.0, 0.4), 'grass': (0.4, 0.65), 'plant': (0.65, 0.8), 'small mushroom': (0.8, 0.95), 'large mushroom': (0.95, 1.0)},
        
        'tree variants': {'fir': (0.0, 0.3), 'evergreen': (0.3, 0.4)},

        'cave noise': {'scale': 40.0, 'octaves': 4, 'persistence': 1.6, 'lacunarity': 1.9, 'threshold': 0.4},

        'z layers': {
            0.2: {'stone': (0.0, 0.35), 'coal': (0.35, 0.55), 'amber': (0.55, 0.7), 'fossil': (0.7, 0.82), 'iron': (0.82, 0.92), 'silver': (0.92, 0.98), 'emerald': (0.98, 1.0)},
            
            0.4: {'stone': (0.0, 0.35), 'coal': (0.35, 0.6), 'amber': (0.6, 0.75), 'iron': (0.75, 0.9), 'silver': (0.9, 0.98), 'emerald': (0.98, 1.0)},
            
            0.6: {'stone': (0.0, 0.4), 'coal': (0.4, 0.65), 'amber': (0.65, 0.8), 'iron': (0.8, 0.95), 'fossil': (0.95, 1.0)},
            
            0.8: {'dirt': (0.0, 0.4), 'stone': (0.4, 0.75), 'ice': (0.75, 0.9), 'amber': (0.9, 1.0)},

            1.0: {'dirt': (0.0, 0.6), 'stone': (0.6, 0.9), 'ice': (0.9, 1.0)},
        }
    },

    'forest': {
        'geo noise': {'elev': (0.4, 0.6), 'temp': (0.3, 0.5), 'precip': (0.5, 0.65), 'veg': (0.6, 0.75)},

        'surface noise': {'scale': 200, 'octaves': 3, 'persistence': 1.5, 'lacunarity': 2.0},
        
        'surface terrain': {'tree': (0.0, 0.5), 'plant': (0.5, 0.7), 'grass': (0.7, 0.85), 'small mushroom': (0.85, 0.95), 'large mushroom': (0.95, 1.0)},
        
        'tree variants': {'oak': (0.0, 0.2), 'maple': (0.2, 0.35), 'poplar': (0.35, 0.45), 'fruit': (0.45, 0.5)},

        'cave noise': {'scale': 30.0, 'octaves': 4, 'persistence': 1.6, 'lacunarity': 1.3, 'threshold': 0.55},

        'z layers': {
            0.2: {'stone': (0.0, 0.45), 'coal': (0.45, 0.65), 'amber': (0.65, 0.8), 'iron': (0.8, 0.92), 'emerald': (0.92, 1.0)},
            
            0.4: {'stone': (0.0, 0.45), 'coal': (0.45, 0.65), 'iron': (0.65, 0.85), 'amber': (0.85, 0.95), 'emerald': (0.95, 1.0)},
           
            0.6: {'stone': (0.0, 0.45), 'coal': (0.45, 0.7), 'clay': (0.7, 0.85), 'iron': (0.85, 0.97), 'amber': (0.97, 1.0)},

            0.8: {'dirt': (0.0, 0.45), 'stone': (0.45, 0.75), 'clay': (0.75, 0.9), 'amber': (0.9, 1.0)},

            1.0: {'dirt': (0.0, 0.55), 'stone': (0.55, 0.8), 'clay': (0.8, 1.0)},
        }
    },

    'plains': {
        'geo noise': {'elev': (0.15, 0.25), 'temp': (0.4, 0.6), 'precip': (0.25, 0.4), 'veg': (0.25, 0.4)},

        'surface noise': {'scale': 300, 'octaves': 3, 'persistence': 1.2, 'lacunarity': 1.5},
        
        'surface terrain': {'grass': (0.0, 0.4), 'plant': (0.4, 0.75), 'tree': (0.75, 0.85), 'small mushroom': (0.85, 0.95), 'large mushroom': (0.95, 1.0)},
        
        'tree variants': {'oak': (0.75, 0.8), 'fruit': (0.8, 0.85)},

        'cave noise': {'scale': 60.0, 'octaves': 3, 'persistence': 0.7, 'lacunarity': 0.9, 'threshold': 0.6},

        'z layers': {       
            0.2: {'stone': (0.0, 0.45), 'clay': (0.45, 0.65), 'fossil': (0.65, 0.82), 'iron': (0.82, 0.94), 'silver': (0.94, 1.0)},

            0.4: {'stone': (0.0, 0.5), 'fossil': (0.5, 0.68), 'iron': (0.68, 0.88), 'coal': (0.88, 0.97), 'silver': (0.97, 1.0)},

            0.6: {'stone': (0.0, 0.45), 'clay': (0.45, 0.65), 'fossil': (0.65, 0.82), 'iron': (0.82, 1.0)},

            0.8: {'dirt': (0.0, 0.55), 'stone': (0.55, 0.8), 'clay': (0.8, 0.95), 'fossil': (0.95, 1.0)},

            1.0: {'dirt': (0.0, 0.7), 'clay': (0.7, 0.9), 'stone': (0.9, 1.0)},
        }
    },

    'desert': {
        'geo noise': {'elev': (0.35, 0.5), 'temp': (0.85, 1.0), 'precip': (0.0, 0.1), 'veg': (0.0, 0.1)},

        'surface noise': {'scale': 275, 'octaves': 4, 'persistence': 0.9, 'lacunarity': 1.4},
        
        'surface terrain': {'cactus': (0.0, 0.15), 'plant': (0.15, 0.25), 'small rock': (0.25, 0.35), 'large rock': (0.35, 0.4)},

        'cave noise': {'scale': 60.0, 'octaves': 3, 'persistence': 0.7, 'lacunarity': 0.9, 'threshold': 0.6},

        'z layers': {     
            0.2: {'stone': (0.0, 0.25), 'copper': (0.25, 0.5), 'fossil': (0.5, 0.65), 'gold': (0.65, 0.82), 'topaz': (0.82, 0.94), 'ruby': (0.94, 1.0)},

            0.4: {'stone': (0.0, 0.35), 'copper': (0.35, 0.6), 'gold': (0.6, 0.82), 'topaz': (0.82, 0.95), 'ruby': (0.95, 1.0)},

            0.6: {'sandstone': (0.0, 0.4), 'stone': (0.4, 0.65), 'copper': (0.65, 0.85), 'fossil': (0.85, 1.0)},            

            0.8: {'sandstone': (0.0, 0.45), 'sand': (0.45, 0.65), 'clay': (0.65, 0.8), 'copper': (0.8, 1.0)},

            1.0: {'sand': (0.0, 0.65), 'sandstone': (0.65, 0.9), 'clay': (0.9, 1.0)},
        }
    },

    'jungle': {
        'geo noise': {'elev': (0.65, 0.8), 'temp': (0.7, 0.85), 'precip': (0.8, 1.0), 'veg': (0.8, 1.0)},

        'surface noise': {'scale': 175, 'octaves': 3, 'persistence': 1.6, 'lacunarity': 1.6},

        'surface terrain': {'tree': (0.0, 0.5), 'plant': (0.5, 0.75), 'grass': (0.75, 0.9), 'small mushroom': (0.9, 0.97), 'large mushroom': (0.97, 1.0)},
        
        'tree variants': {'willow': (0.0, 0.3), 'palm': (0.3, 0.5)},

        'cave noise': {'scale': 60.0, 'octaves': 3, 'persistence': 0.7, 'lacunarity': 0.9, 'threshold': 0.6},
        
        'z layers': {
            0.2: {'stone': (0.0, 0.3), 'copper': (0.3, 0.5), 'gold': (0.5, 0.68), 'emerald': (0.68, 0.82), 'amethyst': (0.82, 0.92), 'ruby': (0.92, 1.0)},

            0.4: {'stone': (0.0, 0.4), 'coal': (0.4, 0.6), 'copper': (0.6, 0.8), 'emerald': (0.8, 0.94), 'amethyst': (0.94, 1.0)},

            0.6: {'stone': (0.0, 0.4), 'coal': (0.4, 0.6), 'clay': (0.6, 0.75), 'copper': (0.75, 0.92), 'gold': (0.92, 1.0)},
 
            0.8: {'dirt': (0.0, 0.45), 'clay': (0.45, 0.7), 'stone': (0.7, 0.9), 'coal': (0.9, 1.0)},

            1.0: {'dirt': (0.0, 0.55), 'clay': (0.55, 0.8), 'stone': (0.8, 0.9), 'sand': (0.9, 1.0)}, 
        }
    },
}

SOLID_TILES = {
    'amber': {'hardness': 500, 'minimap rgb': ()},

    'amethyst': {'hardness': 100, 'minimap rgb': ()},

    'clay': {'hardness': 150, 'minimap rgb': (255, 138, 101)},

    'coal': {'hardness': 450, 'minimap rgb': (66, 66, 66)},

    'copper': {'hardness': 550, 'minimap rgb': (245, 127, 23)},

    'diamond': {'hardness': 1500, 'minimap rgb': ()},

    'dirt': {'hardness': 100, 'minimap rgb': (93, 64, 55)},

    'emerald': {'hardness': 500, 'minimap rgb': ()},

    'fossil': {'hardness': 400, 'minimap rgb': (243, 174, 113)},

    'gold': {'hardness': 400, 'minimap rgb': (251, 192, 45)},

    'ice': {'hardness': 200, 'minimap rgb': (179, 229, 252)},

    'iron': {'hardness': 750, 'minimap rgb': (251, 233, 231)},

    'obsidian': {'hardness': 1000, 'minimap rgb': (32, 23, 43)},

    'ruby': {'hardness': 500, 'minimap rgb': ()},

    'sand': {'hardness': 100, 'minimap rgb': (255, 224, 178)},

    'sandstone': {'hardness': 500, 'minimap rgb': (255, 112, 67)},

    'sapphire': {'hardness': 500, 'minimap rgb': ()},

    'silver': {'hardness': 500, 'minimap rgb': (224, 224, 224)},

    'stone': {'hardness': 300, 'minimap rgb': (117, 117, 117)},

    'topaz': {'hardness': 500, 'minimap rgb': ()}
}

ELEVATIONS = {'foothills', 'hills', 'mountains', 'mountain peak', 'volcano', 'shallow valley', 'deep valley'}

TREES = {'oak', 'evergreen', 'bare', 'stump', 'fir 0', 'fir 1', 'fruit', 'maple 0', 'maple 1', 'poplar', 'willow', 'palm 0', 'palm 1'}

SURFACE_TERRAIN = {'small rock', 'large rock', 'small mushroom', 'large mushroom', 'lilypad', 'cactus', 'snow'}
for b in BIOMES:
    SURFACE_TERRAIN.add(f'{b} plant')
    SURFACE_TERRAIN.add(f'{b} grass')

MISC_TERRAIN = {'large rock', 'small rock', 'snow'}

LIQUIDS = {'water', 'lava', 'oil'}

MONTHS_DAYS = {
    'January': 31, 'February': 28, 'March': 31, 'April': 30, 'May': 31, 'June': 30, 'July': 31, 'August': 31, 
    'September': 30, 'October': 31, 'November': 30, 'December': 31
}
MONTH_IDXS = {i: month for i, month in enumerate(MONTHS_DAYS)}

MOON_PHASES = ('New', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous', 'Full', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent')
MOON_PHASE_IDXS = {i: phase for i, phase in enumerate(MOON_PHASES)}
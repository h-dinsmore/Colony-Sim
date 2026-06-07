import pygame as pg

RES = (1284, 720)
FPS = 60

KEY_BINDINGS = {
    '-x': pg.K_a,
    '+x': pg.K_d,
    '-y': pg.K_w,
    '+y': pg.K_s,
    '+z': pg.K_UP,
    '-z': pg.K_DOWN,
    'drop item': pg.K_BACKSPACE
}

MAP_SIZE = (400, 400, 5)
TILE_SIZE = 16
SEA_LVL = 0

BIOMES = {
    'tundra': {
        'noise max': {'elev': 0.25, 'temp': 0.1, 'precip': 0.25, 'plants': 0.2},
        'z lvl slices': {
            0.2: {'snow': 0.40, 'ice': 0.30, 'dirt': 0.20, 'stone': 0.10},
            0.5: {'ice': 0.40, 'dirt': 0.25, 'stone': 0.20, 'snow': 0.15},
            0.7: {'stone': 0.40, 'ice': 0.30, 'dirt': 0.30},
            1.0: {'stone': 0.50, 'dirt': 0.50}
        }
    },

    'taiga': {
        'noise max': {'elev': 1.0, 'temp': 0.25, 'precip': 0.4, 'plants': 0.6},
        'z lvl slices': {
            0.2: {'stone': 0.35, 'ice': 0.30, 'snow': 0.20, 'dirt': 0.15},
            0.5: {'dirt': 0.40, 'stone': 0.25, 'ice': 0.20, 'snow': 0.15},
            0.7: {'stone': 0.45, 'dirt': 0.35, 'coal': 0.15, 'ice': 0.05},
            1.0: {'stone': 0.55, 'coal': 0.20, 'iron': 0.15, 'dirt': 0.10}
        }
    },

    'forest': {
        'noise max': {'elev': 0.5, 'temp': 0.4, 'precip': 0.6, 'plants': 0.7},
        'z lvl slices': {
            0.2: {'dirt': 0.60, 'stone': 0.25, 'clay': 0.15},
            0.5: {'dirt': 0.45, 'stone': 0.35, 'clay': 0.10, 'coal': 0.10},
            0.7: {'stone': 0.50, 'dirt': 0.20, 'coal': 0.15, 'iron': 0.15},
            1.0: {'stone': 0.55, 'coal': 0.20, 'iron': 0.15, 'copper': 0.10}
        }
    },

    'plains': {
        'noise max': {'elev': 0.2, 'temp': 0.5, 'precip': 0.2, 'plants': 0.3},
        'z lvl slices': {
            0.2: {'dirt': 0.70, 'clay': 0.20, 'stone': 0.10},
            0.5: {'dirt': 0.50, 'stone': 0.30, 'clay': 0.10, 'coal': 0.10},
            0.7: {'stone': 0.55, 'coal': 0.15, 'iron': 0.15, 'dirt': 0.15},
            1.0: {'stone': 0.60, 'iron': 0.20, 'coal': 0.10, 'copper': 0.10}
        }
    },

    'desert': {
        'noise max': {'elev': 0.4, 'temp': 1.0, 'precip': 0.1, 'plants': 0.15},
        'z lvl slices': {
            0.2: {'sand': 0.60, 'sandstone': 0.25, 'clay': 0.15},
            0.5: {'sandstone': 0.40, 'sand': 0.25, 'clay': 0.15, 'copper': 0.20},
            0.7: {'sandstone': 0.45, 'stone': 0.25, 'copper': 0.20, 'fossil': 0.10},
            1.0: {'stone': 0.45, 'copper': 0.25, 'gold': 0.20, 'obsidian': 0.10}
        }
    },

    'jungle': {
        'noise max': {'elev': 0.6, 'temp': 0.75, 'precip': 1.0, 'plants': 1.0},
        'z lvl slices': {
            0.2: {'dirt': 0.55, 'clay': 0.25, 'stone': 0.20},
            0.5: {'dirt': 0.40, 'clay': 0.20, 'stone': 0.25, 'coal': 0.15},
            0.7: {'stone': 0.45, 'coal': 0.20, 'iron': 0.15, 'gold': 0.20},
            1.0: {'stone': 0.45, 'gold': 0.20, 'iron': 0.15, 'diamond': 0.10, 'obsidian': 0.10}
        }
    }
}

SURFACES = {
    'dirt': {'hardness': 100, 'minimap rgb': (93, 64, 55)},
    'stone': {'hardness': 300, 'minimap rgb': (117, 117, 117)},
    'ice': {'hardness': 200, 'minimap rgb': (179, 229, 252)},
    'snow': {'hardness': 125, 'minimap rgb': (255, 255, 255)},
    'sand': {'hardness': 100, 'minimap rgb': (255, 224, 178)},
    'sandstone': {'hardness': 500, 'minimap rgb': (255, 112, 67)},
    'clay': {'hardness': 150, 'minimap rgb': (255, 138, 101)},
    'fossil': {'hardness': 400, 'minimap rgb': (243, 174, 113)},
    'coal': {'hardness': 450, 'minimap rgb': (66, 66, 66)},
    'silver': {'hardness': 500, 'minimap rgb': (224, 224, 224)},
    'copper': {'hardness': 550, 'minimap rgb': (245, 127, 23)},
    'gold': {'hardness': 400, 'minimap rgb': (251, 192, 45)},
    'iron': {'hardness': 750, 'minimap rgb': (251, 233, 231)},
    'obsidian': {'hardness': 1000, 'minimap rgb': (32, 23, 43)},
    'diamond': {'hardness': 1500, 'minimap rgb': ()},
}

ELEVATIONS = {'foothills', 'hills', 'mountains', 'mountain peak', 'volcano'}

TREES = {'oak', 'evergreen', 'bare', 'stump', 'forest'}

LIQUIDS = {'water', 'lava', 'oil'}
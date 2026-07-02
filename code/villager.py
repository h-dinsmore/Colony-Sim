import pygame as pg
from random import randint, choice

from settings import MONTHS_DAYS, TILE_SIZE

class Villager(pg.sprite.Sprite):
    def __init__(self, image, xyz, spr_groups, screen, proc_gen):
        super().__init__(*spr_groups)
        self.image = image
        self.image.set_colorkey((0, 0, 0))
        self.x, self.y, self.z = xyz
        self.rect = self.image.get_rect(topleft=(pg.Vector2(self.x, self.y) * TILE_SIZE) + pg.Vector2(TILE_SIZE) / 2)
        self.screen = screen
        self.proc_gen = proc_gen
        
        self.action = 'idle'
        self.facing_dir = 'left'
        self.visible = True

        self.inv = {}
        self.max_inv_items = 64

        self.hunger = 100 
        self.thirst = 100
        self.sleep = 100
        self.mood = 100
        self.health = 100
        self.living = True

        self.relations = {
            'family': {},
            'friends': {},
            'enemies': {},
            'partner': None
        }
        self.age = randint(18, 36)
        birth_month = choice(list(MONTHS_DAYS.keys()))
        self.birthday = f'{birth_month} {randint(0, MONTHS_DAYS[birth_month])}'
        self.strengths = {}
        self.weaknesses = {}
        self.hobbies = {}
        self.memories = {}
        self.fears = {}

    def update_visibility(self, player):
        px, py = player.rect.center
        x, y = self.rect.center
        z_map = self.proc_gen.z_map
        self.visible = abs(px - x) < RES[0] // 2 and abs(py - y) < RES[1] // 2 and z_map[x, y] <= z_map[px, py]

    def update(self):
        pass
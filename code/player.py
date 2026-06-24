import pygame as pg

from villager import Villager

class Player(Villager):
    def __init__(self, image, xyz, spr_groups, screen, keyboard):
        super().__init__(image, xyz, spr_groups, screen)
        self.keyboard = keyboard

    def move(self):
        pass
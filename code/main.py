import pygame as pg
import sys

from settings import RES, FPS, MAP_PX_SIZE, TILE_SIZE
from assets import Assets
from camera import Camera
from input import Keyboard, Mouse
from proc_gen import ProcGen
from chunk_renderer import ChunkRenderer
from weather import Weather
from village import Village
from ui import UI

class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption('colony sim')
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode(RES)
        self.running = True
        
        self.keyboard = Keyboard()
        
        self.cam = Camera(pg.Vector2(RES) / 2, self.keyboard)
        self.zoom_scale = None

        self.mouse = Mouse(self.cam)

        self.world_surf = pg.Surface(pg.Vector2(MAP_PX_SIZE[:2]) / self.cam.min_zoom_scale, pg.SRCALPHA)
        self.visible_surf = None
        
        self.proc_gen = ProcGen()
        
        self.assets = Assets(self.proc_gen)
        
        self.chunk_renderer = ChunkRenderer(self.world_surf, self.proc_gen, self.assets, self.cam, self.keyboard)
        
        self.village = Village(
            self.proc_gen, self.assets, self.keyboard, self.mouse, self.world_surf, self.chunk_renderer
        )
        self.chunk_renderer.player = self.village.player
        
        self.weather = Weather(self.world_surf, self.cam, self.proc_gen, self.village.village_sprs)

        self.ui = UI(
            self.cam, self.proc_gen, self.village.player, self.keyboard, self.mouse, self.chunk_renderer, 
            self.weather, self.assets, self.clock, self.village
        )

    def update_visible_surf(self): 
        scaled_res = pg.Vector2(RES) / self.cam.zoom_scale
        max_x, max_y = pg.Vector2(self.world_surf.size) - scaled_res
        cam_x, cam_y = self.cam.offset
        return pg.transform.scale(
            self.world_surf.subsurface((max(0, min(cam_x, max_x)), max(0, min(cam_y, max_y))), scaled_res), RES
        )
       
    def update(self):
        self.clock.tick(FPS) 
        
        self.weather.update()
        self.keyboard.update()
        self.mouse.update()
        self.cam.update(pg.Vector2(self.village.player.rect.center))
        self.chunk_renderer.update()
        self.village.update()

        self.visible_surf = self.update_visible_surf()
        self.ui.update(self.visible_surf) # not blitting it on the world surface to keep it the same size when the camera zooms
        self.screen.blit(self.visible_surf, self.visible_surf.get_rect(topleft=(0, 0)))
        pg.display.flip()

    def run(self):
        while self.running:
            for event in pg.event.get():
                self.running = self.village.player.living and not (event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE))
                if event.type == pg.MOUSEWHEEL:
                    self.cam.update_zoom(event)
                    
            self.update()

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()
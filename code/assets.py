import pygame as pg
from os import walk
from os.path import join
from pathlib import Path
from dataclasses import dataclass, field

from settings import TILE_SIZE, ELEVATIONS, SOLID_TILES

@dataclass
class FolderDir:
    files: dict[str, pg.Surface | None] = field(default_factory=dict)
    subfolders: dict[str, 'FolderDir'] = field(default_factory=dict)
    loaded: bool = False

class Assets:
    def __init__(self, proc_gen):
        self.proc_gen = proc_gen
        
        self.img_cache, self.img_dir_cache = {}, {}
        self.graphics_load_runtime = {'entities', 'terrain'} 
        self.graphics_dir_root = Path('..') / 'graphics'
        self.graphics = {
            folder.name: self.load_subfolders(folder, folder.name in self.graphics_load_runtime) 
            for folder in self.graphics_dir_root.iterdir() if folder.is_dir()
        }
        
        self.colors = {
            'transparent': (0,0,0,0)
        }
        
        self.font_sizes = {'default': 16}
        self.fonts = self.load_fonts(join('..', 'graphics', 'fonts'))

    @staticmethod
    def load_img(dir_path):
        img = pg.transform.scale(pg.image.load(dir_path).convert_alpha(), (TILE_SIZE, TILE_SIZE))
        if 'elevations' in dir_path:
            img.set_alpha(175 if 'valley' in dir_path else 200)
        return img.copy()
    
    def load_folder(self, dir_path):
        imgs = {}
        for path, _, files in walk(dir_path):    
            for file_name in files:
                key = file_name.split('.')[0] # not reassigning 'name' because it needs the file extension when passed to load_img()
                img = self.load_img(join(path, file_name))
                imgs[key] = img
                self.img_cache[key] = img
        return imgs
    
    def load_frames(self, dir_path):
        frames = []
        for path, _, files in walk(dir_path):   
            for file in sorted(files, key=lambda file_name: int(file_name.split('.')[0])): 
                frames.append(self.load_img(join(path, file)))
        return frames

    def load_subfolders(self, dir_path, load_files=False):
        folder_dir = FolderDir(loaded=load_files)
        if load_files:
            folder_dir.files = self.load_folder(dir_path) 

        self.cache_img_dirs(dir_path)

        for folder in (f for f in dir_path.iterdir() if f.is_dir()):
            folder_dir.subfolders[folder.name] = self.load_subfolders(folder, load_files)
        return folder_dir

    def cache_img_dirs(self, dir_path):
        for path, _, files in walk(dir_path):    
            for file_name in files:
                self.img_dir_cache[file_name.split('.')[0]] = join(dir_path, file_name)
    
    def load_fonts(self, dir_path):
        fonts = {}
        for path, _, files in walk(dir_path):    
            for name in files:
                name_split = name.split('.')[0]
                fonts[name_split] = pg.font.Font(join(path, name), self.font_sizes[name_split])
        return fonts

    def get_img(self, file_name):
        if file_name in self.img_cache:
            return self.img_cache[file_name]
        return self.load_img(self.img_dir_cache[file_name])
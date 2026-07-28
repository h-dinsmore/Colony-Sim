import pygame as pg
from os import walk
from os.path import join
from pathlib import Path
from dataclasses import dataclass, field

from settings import TILE_SIZE, ELEVATIONS, SOLID_TILES, Z_DIF_ICONS

@dataclass
class FolderDir:
    files: dict[str, pg.Surface | None] = field(default_factory=dict)
    subfolders: dict[str, 'FolderDir'] = field(default_factory=dict)

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
        for i, (_, file_name) in enumerate(sorted(Z_DIF_ICONS.items(), key=lambda items: items[0][1], reverse=True), start=1):
            self.graphics['terrain'].subfolders['elevations'].files[file_name].set_alpha(255 - (i * 16))
        
        self.colors = {
            'transparent': (0,0,0,0)
        }
        
        self.font_sizes = {'default': 16, 'inv item amounts': 20, 'inv item names': 18}
        self.font_variants = {'default': ('inv item amounts', 'inv item names')} # uses a loaded font but at a different size
        self.fonts = self.load_fonts(join('..', 'graphics', 'fonts'))
        self.font_text_cache = {k: {} for k in self.fonts}

    @staticmethod
    def load_img(dir_path):
        return pg.transform.scale(pg.image.load(dir_path).convert_alpha(), (TILE_SIZE, TILE_SIZE))
    
    def load_folder(self, dir_path):
        imgs = {}
        for file_dir in (f for f in dir_path.iterdir() if f.is_file()):    
            dir_parts = Path(file_dir).parts
            img = self.load_img(join(*dir_parts)) 
            file_name = dir_parts[-1].split('.')[0]
            imgs[file_name] = img
            self.img_cache[file_name] = img
        return imgs
    
    def load_frames(self, dir_path):
        frames = []
        for path, _, files in walk(dir_path):   
            for file in sorted(files, key=lambda file_name: int(file_name.split('.')[0])): 
                frames.append(self.load_img(join(path, file)))
        return frames

    def load_subfolders(self, dir_path, load_files=False):
        folder_dir = FolderDir()
        if load_files:
            file_dict = self.load_folder(dir_path) 
            folder_dir.files = file_dict
            for (file_name, img) in file_dict.items():
                self.img_cache[file_name] = img
        else:
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
                font_key = name.split('.')[0]
                fonts[font_key] = pg.font.Font(join(path, name), self.font_sizes[font_key])

                if font_key in self.font_variants:
                    for font_var in self.font_variants[font_key]:
                        fonts[font_var] = pg.font.Font(join(path, name), self.font_sizes[font_var])
        return fonts

    def get_img(self, file_name):
        if file_name in self.img_cache:
            return self.img_cache[file_name]
        return self.load_img(self.img_dir_cache[file_name])
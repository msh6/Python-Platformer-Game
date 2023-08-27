import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

'''Initializing Pygame for our program.'''
pygame.init()

'''Sets the title of the window.'''
pygame.display.set_caption("Ninja Frog")

'''Setting the size of window, locking in the FPS and player velocity.'''
WIDTH, HEIGHT = 1000, 700
FPS = 60
PLAYER_VEL = 8 

'''Initialization variable with our determined inputs.'''
window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_spite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]
    
    all_sprites = {}
    
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))
            
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
            
    return all_sprites
        
        
def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    # convert_alpha() is for transparent background
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)
        

'''Player Class'''
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 5
    SPRITES = load_spite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 1
    
    def __init__(self, x, y, width, height):
        super().__init__()
        # Rect is just a tuple storing four values
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left" 
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        
    def jump(self):
        self.y_vel = -self.GRAVITY * 3
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0
        
    # dx, dy is displacement in both velocities for player movement
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy
        
    def make_hit(self):
        self.hit = True
        self.hit_count = 0
        
    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0
        
    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0
            
    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)
        
        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 1 :
            self.hit = False
            self.hit_count = 0
                        
        self.fall_count += 1
        self.update_sprite()
        self.update()
        
    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
    
    def hit_head(self):
        self.fall_count = 0
        self.y_vel *= -1
        
    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"
            
        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        # mask is a mapping of all of the pixels that exists in a sprite
        # it helps us achieve the pixel perfect collision
        self.mask = pygame.mask.from_surface(self.sprite)
    
    def draw(self, win, offset_x):
        #pygame.draw.rect(win, self.COLOR, self.rect)
        #self.sprite = self.SPRITES["idle_" + self.direction][0]
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))
        
        
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        # srcalpha transports/supports transparent images 
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
        
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))
        
        
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)
        
        
class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_spite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0
    
'''Function loads bg_image and its size proportions.'''
def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    
    """below the two for loops loop through the range(widthofwindow//widthofimage same for height)
    to get exact positions as tuple stored in a list as tiles to know how bg_image blocks are
    needed to fill the whole window

    Returns:
        _type_: list and pygame.image
    """    
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)
            
    return tiles, image

'''Function draws our image all across the window'''
def draw(window, background, bg_image, player, objects, offset_x):
    # loops through background(tiles) and drawing bg_image on the res. cordinates.
    for tile in background:
        window.blit(bg_image, tile)
        
    for obj in objects:
        obj.draw(window, offset_x)
        
    player.draw(window, offset_x)
    
    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    # dy = displacement y cord
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
        
            collided_objects.append(obj)
        
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collide_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collide_object = obj
            break
        
    player.move(-dx, 0)
    player.update()
    return collide_object 


'''Func for handling player movement.'''
def handle_move(player, objects):
    keys = pygame.key.get_pressed()
    
    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL*2)
    collide_right = collide(player, objects, PLAYER_VEL*2)

    
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)
        
    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check =  [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

'''main function constitues of all the events happening'''
def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")
    
    block_size = 96
    
    player = Player(100,100,50,50)
    fire = Fire(100, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    floor = []
    for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size):
        x = i * block_size
        y = HEIGHT - block_size
        block = Block(x, y, block_size)
        floor.append(block)
    #blocks = [Block(0, HEIGHT - block_size, block_size)]
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size), fire]
    
    offset_x = 0
    scroll_area_width = 600
    
    run = True
    while run:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
            
        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)
            
        draw(window, background, bg_image, player, objects, offset_x)
        
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel
            
    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pygame
import os
from time import sleep, time
from math import sqrt, acos, degrees, radians, sin, cos
from random import randint


file_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_path)
clock = pygame.time.Clock()


WINDOW_WIDTH = 500
WINDOW_HEIGHT = 500


def rotate_image(image, angle):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image


def sign(a, magic=1): # if a // magic == 0, then a == 0
    if a // magic > 0:
        return 1
    elif a // magic == 0:
        return 0
    else:
        return -1


class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x * other.x, self.y * other.y)
        else:
            return Vector(self.x * other, self.y * other)

    def __div__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x / other.x, self.y / other.y)
        else:
            return Vector(self.x / other, self.y / other)

    def len(self):
        return sqrt(self.x * self.x + self.y * self.y)

    def distance(self, other):
        return (self - other).len()

    def normalized(self):
        l = self.len()
        return Vector(self.x / l, self.y / l)

    def rotated(self, angle, origin=None):
        x = self.x
        y = self.y
        angle = radians(angle)
        if origin:
            ox = origin.x
            oy = origin.y
            qx = ox + cos(angle) * (x - ox) - sin(angle) * (y - oy)
            qy = oy + sin(angle) * (x - ox) + cos(angle) * (y - oy)
        else:
            qx = -x * cos(angle) + y * sin(angle)
            qy =x * sin(angle) + y * cos(angle)
        return Vector(qx, qy)

    def dot_product(self, other):
        return self.x * other.x + self.y * other.y

    def angle(self, other):
        return acos(self.dot_product(other) / (self.len() * other.len()))

    def __repr__(self):
        return '({}, {})'.format(self.x, self.y)


class World:
    def __init__(self, name, width, height):
        self.window = pygame.display.set_mode((width, height))
        pygame.display.set_caption('Game')
        self.screen = pygame.Surface((width, height))
        #pygame.key.set_repeat(50, 1)
        pygame.init()

        self.width = width
        self.height = height

        self.objects = []

    def render(self):
        screen = self.screen
        screen.fill((80, 80, 80))
        
        pl = self.objects[0]
        pygame.draw.circle(screen, (255, 255, 255), (int(pl.pos.x), int(pl.pos.y)), pl.width)

        for obj in self.objects:
            if obj.is_drawable and obj.is_alive:
                screen.blit(rotate_image(obj.texture, obj.angle), (obj.pos.x - obj.width // 2, obj.pos.y - obj.height // 2))

        self.window.blit(screen, (0, 0))
        pygame.display.flip()

    def tick(self):
        events = pygame.event.get()
        pl = self.objects[0]
        dt = clock.tick(60)
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                pl.pos.center = Vector(pos[0], pos[1])
                pl.goal_targeting_mode = True
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            pl.cur_spd.y = -pl.spd
        if keys[pygame.K_a]:
            pl.cur_spd.x = -pl.spd
        if keys[pygame.K_s]:
            pl.cur_spd.y = +pl.spd
        if keys[pygame.K_d]:
            pl.cur_spd.x = +pl.spd
        if keys[pygame.K_SPACE]:
            pl.goal_targeting_mode = False
            pl.attack()

        if pl.cur_spd.x and pl.cur_spd.y:
            pl.cur_spd = pl.cur_spd.normalized() * pl.spd

        for obj in self.objects:
            obj.tick()
        self.render()


class Weapon:
    def __init__(self, world, owner, dmg, bullet_spd, reload_time, shift_x=0, shift_y=0, shift_angle=0):
        self.world = world
        self.owner = owner

        self.dmg = dmg
        self.bullet_spd = bullet_spd
        self.reload_time = reload_time
        self.shift_x = shift_x
        self.shift_y = shift_y
        self.shift_angle = shift_angle

        self.last_shot_time = 0

    def fire(self):
        if time() - self.last_shot_time < self.reload_time:
            return
        self.last_shot_time = time()
        
        pos = self.owner.pos
        angle = self.owner.angle
        spawn_pos = pos + (Vector(self.shift_x, self.shift_y).rotated(90+angle))
        x = spawn_pos.x
        y = spawn_pos.y
        # im super cool

        bullet = Projectile(self.world, 'bullet', x, y, 10, 10, angle + self.shift_angle, self.dmg, self.bullet_spd*3, './textures/bullet.png', owner=self.owner)
        self.world.objects.append(bullet)


class Unit:
    def __init__(self, world, name, x, y, width, height, angle, hp, spd, texture, goal_targeting_mode=False, is_player=False, is_drawable=True):
        self.world = world
        self.name = name
        self.width = width
        self.height = height
        self.angle = angle
        self.texture = pygame.transform.scale(pygame.image.load(texture), (width, height))

        self.hp = hp
        self.spd = spd
        self.cur_spd = Vector(0, 0)

        self.pos = Vector(x, y)
        self.pos.center = Vector(x, y)
        if is_player:
            magic = 0
        else:
            magic = 1
        self.pos.radius = (self.width + self.height) // 2 * magic + self.spd + 1
        self.pos.random_goal = None

        self.goal_targeting_mode = goal_targeting_mode
        self.is_alive = True
        self.is_player = is_player
        self.is_drawable = is_drawable

        self.weapons = [Weapon(world, self, self.hp//5, self.spd*2, 2),
                        Weapon(world, self, self.hp//5, self.spd*2, 2, 10, +10, -10),
                        Weapon(world, self, self.hp//5, self.spd*2, 2, 10, -10, +10)]

    def move_tick(self, to_cancel_cur_spd=False):
        self.pos += self.cur_spd
        self.pos.x = self.pos.x
        self.pos.y = self.pos.y

        self.angle = degrees(self.cur_spd.angle(Vector(0, -1)))
        if self.cur_spd.x > 0:
            self.angle *= -1

        if to_cancel_cur_spd:
            self.move_cancel_cur_spd()
        
    def move_cancel_cur_spd(self):
        self.cur_spd.x = 0
        self.cur_spd.y = 0

    def collides(self, other):
        r1 = Vector(self.width, self.height).len() / 4
        r2 = Vector(other.width, other.height).len() / 4
        if r1 + r2 >= (self.pos - other.pos).len():
            return True
        else:
            return False

    def tick(self):
        if not self.is_alive:
            self.die()
            return

        cur_spd = self.cur_spd

        if cur_spd.x or cur_spd.y:
            self.move_tick(to_cancel_cur_spd=True)
        elif self.goal_targeting_mode:
            pos = self.pos
            if pos.distance(pos.center) > pos.radius:
                need_spd = (pos.center - pos).normalized()  * self.spd
                self.cur_spd = need_spd
                self.move_tick()
            elif self.is_player:
                self.goal_targeting_mode = False
            elif not self.is_player and self.pos.radius:
                if pos.random_goal is None:
                    rg_x = randint(pos.center.x - pos.radius, pos.center.x + pos.radius)
                    rg_y = randint(pos.center.y - pos.radius, pos.center.y + pos.radius)
                    pos.random_goal = Vector(rg_x, rg_y)
                else:
                    if (pos.center - pos.random_goal).len() > pos.radius:
                        pos.random_goal = None
                    else:
                        if pos.distance(pos.random_goal) > self.spd + 1:
                            need_spd = (pos.random_goal - pos).normalized() * self.spd
                            self.cur_spd = need_spd
                            self.move_tick()
                        else:
                            pos.random_goal = None

    def attack(self):
        for weapon in self.weapons:
            weapon.fire()

    def apply_dmg(self, dmg, to_check_death=True):
        self.hp -= dmg
        if to_check_death:
            if self.hp <= 0:
                self.die()

    def die(self):
        if self.is_alive:
            self.is_alive = False
        else:
            del self.world.objects[self.world.objects.index(self)]


class Projectile(Unit):
    def __init__(self, world, name, x, y, width, height, angle, hp, spd, texture, goal_targeting_mode=False, is_player=False, is_drawable=True, owner=None):
        super(Projectile, self).__init__(world, name, x, y, width, height, angle, hp, spd, texture, goal_targeting_mode, is_player, is_drawable)
        self.cur_spd = Vector(0, -1).rotated(angle) * spd
        self.owner = owner

    def tick(self):
        if not self.is_alive:
            self.die()
            return

        self.move_tick()
        if self.pos.x > self.world.width or self.pos.x < 0 or self.pos.y > self.world.height or self.pos.y < 0:
            self.die()

        for obj in self.world.objects:
            if self.collides(obj):
                if obj is self or obj is self.owner:
                    pass
                else:
                    obj.apply_dmg(self.hp)
                    self.die()
                    print(self.is_alive)

def main():
    w = World('GameWorld', WINDOW_WIDTH, WINDOW_HEIGHT)
    u = Unit(w, 'kawak', WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, 32, 32, 0, 10, 2, './textures/kawak_green.png', is_player=True)
    w.objects.append(u)
    u = Unit(w, 'kawak', WINDOW_WIDTH // 4, WINDOW_HEIGHT // 4, 128, 128, 0, 10, 2, './textures/plurt_red.png')
    w.objects.append(u)
    cnt = 0
    while True:
        cnt += 1
        w.tick()

if __name__ == '__main__':
    main()
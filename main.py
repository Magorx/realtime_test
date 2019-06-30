#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pygame
import os
from time import sleep
from math import sqrt, acos, degrees
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


class World:
    def __init__(self, name, width, height):
        self.window = pygame.display.set_mode((width, height))
        pygame.display.set_caption('Game')
        self.screen = pygame.Surface((width, height))
        #pygame.key.set_repeat(50, 1)
        pygame.init()

        self.objects = []

    def render(self):
        screen = self.screen
        screen.fill((80, 80, 80))
        
        pl = self.objects[0]
        pygame.draw.circle(screen, (255, 255, 255), (pl.pos.x, pl.pos.y), pl.width)

        for obj in self.objects:
            if obj.is_drawable:
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
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            pl.cur_spd.y = -pl.speed
        if keys[pygame.K_a]:
            pl.cur_spd.x = -pl.speed
        if keys[pygame.K_s]:
            pl.cur_spd.y = +pl.speed
        if keys[pygame.K_d]:
            pl.cur_spd.x = +pl.speed

        for obj in self.objects:
            obj.tick()
        self.render()


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
        return Vector(self.x * other.x, self.y * other.y)

    def len(self):
        return sqrt(self.x * self.x + self.y * self.y)

    def distance(self, other):
        return (self - other).len()

    def normalized(self):
        l = self.len()
        return Vector(self.x / l, self.y / l)

    def dot_product(self, other):
        return self.x * other.x + self.y * other.y

    def angle(self, other):
        return acos(self.dot_product(other) / (self.len() * other.len()))


class Unit:
    def __init__(self, name, x, y, width, height, angle, texture, is_player=False, is_drawable=True):
        self.name = name
        self.width = width
        self.height = height
        self.angle = angle
        self.texture = pygame.transform.scale(pygame.image.load(texture), (width, height))

        self.speed = 2
        self.v_speed = Vector(2, 2)
        self.cur_spd = Vector(0, 0)

        self.pos = Vector(x, y)
        self.pos.center = Vector(x, y)
        magic = 1
        self.pos.radius = (self.width + self.height) // 2 * magic
        self.pos.random_goal = None

        self.is_player = is_player
        self.is_drawable = is_drawable

    def move_tick(self):
        self.pos += self.cur_spd
        self.pos.x = int(self.pos.x)
        self.pos.y = int(self.pos.y)

        self.angle = degrees(self.cur_spd.angle(Vector(0, -1)))
        if self.cur_spd.x > 0:
            self.angle *= -1
        
        self.cur_spd.x = 0
        self.cur_spd.y = 0

    def tick(self):
        cur_spd = self.cur_spd

        if cur_spd.x or cur_spd.y:
            self.move_tick()
        else:
            pos = self.pos
            if pos.distance(pos.center) > pos.radius:
                need_spd = (pos.center - pos).normalized() * self.v_speed
                self.cur_spd = need_spd
                self.move_tick()
            elif not self.is_player:
                if pos.random_goal is None:
                    print('lel')
                    rg_x = randint(pos.center.x - pos.radius, pos.center.x + pos.radius)
                    rg_y = randint(pos.center.y - pos.radius, pos.center.y + pos.radius)
                    pos.random_goal = Vector(rg_x, rg_y)
                else:
                    if (pos.center - pos.random_goal).len() > pos.radius:
                        pos.random_goal = None
                        print('pup')
                    else:
                        if pos.distance(pos.random_goal) > 1:
                            need_spd = (pos.random_goal - pos).normalized() * self.v_speed
                            self.cur_spd = need_spd
                            self.move_tick()
                        else:
                            pos.random_goal = None

def main():
    w = World('GameWorld', WINDOW_WIDTH, WINDOW_HEIGHT)
    u = Unit('kawak', WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, 32, 32, 0, 'kawak_green.png', is_player=True)
    w.objects.append(u)
    cnt = 0
    while True:
        cnt += 1
        w.tick()

if __name__ == '__main__':
    main()
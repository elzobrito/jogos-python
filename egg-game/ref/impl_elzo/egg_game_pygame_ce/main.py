"""EGG GAME — Protótipo de parallax vertical em Pygame-CE.

Execute: python main.py
Dependência: pip install pygame-ce

Conceitos demonstrados:
* camadas de parallax independentes (céu, montanhas, vila);
* tronco infinito composto por textura repetível + módulos decorativos;
* geração determinística de cestas e descarte das que saem da tela;
* colisão unidirecional por cruzamento da superfície;
* salto automático, pausa e recorde local;
* simulação fixa 120 Hz, renderização a até 60 FPS.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

import pygame as pg

BASE = Path(__file__).resolve().parent
ASSETS = BASE / 'assets'
SAVE = BASE / 'recorde.json'
W, H = 960, 720
FPS = 60
FIXED_DT = 1.0 / 120
GRAVITY = 1650.0
JUMP_VY = -810.0
RUN_SPEED = 405.0
EGG_HALF_HEIGHT = 36.0
SEED = 2026

# Rendering e física não usam a mesma coordenada: os mundos y negativos ficam ACIMA.


def font(size: int, bold: bool = False) -> pg.font.Font:
    return pg.font.SysFont('dejavusans', size, bold=bold)


def load_scaled(path: Path, size: tuple[int, int] | None = None) -> pg.Surface:
    src = pg.image.load(str(path)).convert_alpha()
    return pg.transform.smoothscale(src, size) if size else src


@dataclass
class Platform:
    x: float                 # centro horizontal
    y: float                 # plano de aterrissagem (coordenada de mundo)
    kind: str = 'fixed'
    width: float = 138.0
    amplitude: float = 0.0
    phase: float = 0.0
    lifetime: int = 0        # 1 = plataforma frágil já tocada

    def center_at(self, t: float) -> float:
        return self.x + math.sin(t * 1.45 + self.phase) * self.amplitude


class EggGame:
    def __init__(self) -> None:
        pg.init()
        pg.display.set_caption('EGG GAME — De Volta ao Ninho | Demo Pygame-CE')
        self.window = pg.display.set_mode((W, H), pg.RESIZABLE)
        self.frame = pg.Surface((W, H)).convert()
        self.clock = pg.time.Clock()
        self.font_small = font(19)
        self.font_body = font(24, True)
        self.font_title = font(59, True)
        self.font_num = font(34, True)

        self.sky = load_scaled(ASSETS / 'background' / 'sky.jpg')
        self.mountains = load_scaled(ASSETS / 'background' / 'mountains.png')
        self.village = load_scaled(ASSETS / 'background' / 'village.png')
        self.trunk = load_scaled(ASSETS / 'tree' / 'trunk_repeat.png')
        self.tree_parts = [load_scaled(ASSETS / 'tree' / f'trunk_{c}.png') for c in 'ABCDEFG']
        self.baskets = {
            'fixed': load_scaled(ASSETS / 'nests' / 'fixa_01.png', (170, 85)),
            'moving': load_scaled(ASSETS / 'nests' / 'movel_01.png', (180, 83)),
            'small': load_scaled(ASSETS / 'nests' / 'pequena_01.png', (135, 77)),
            'fragile': load_scaled(ASSETS / 'nests' / 'fragil_01.png', (155, 80)),
        }
        self.egg_frames = {
            state: [load_scaled(p, (76, 88)) for p in sorted((ASSETS / 'egg').glob(pattern))]
            for state, pattern in {
                'idle': 'idle_*.png', 'jump': 'jump_*.png',
                'fall': 'fall_*.png', 'death': 'death_*.png',
            }.items()
        }
        if any(not arr for arr in self.egg_frames.values()):
            raise FileNotFoundError('Faltam quadros do personagem em assets/egg/')

        self.records = self.load_records()
        self.best = self.records.get('record', 0)
        self.show_parts = [True, True, True, True]  # céu, montanhas, vila, árvore
        self.show_debug = False
        self.show_hitboxes = False
        self.mode = 'menu'
        self.reset()

    @staticmethod
    def load_records() -> dict:
        try:
            d = json.loads(SAVE.read_text(encoding='utf8'))
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_record(self) -> None:
        try:
            SAVE.write_text(json.dumps({'record': self.best}, indent=2), encoding='utf8')
        except OSError:
            pass  # salvamento não deve derrubar a partida

    def reset(self) -> None:
        self.random = random.Random(SEED)
        self.time = 0.0
        self.player_x = 580.0
        self.player_y = 4.0
        self.velocity_y = 0.0
        self.camera_y = -H * 0.62
        self.initial_camera_y = self.camera_y
        self.max_height = 0.0
        self.on_floor = True
        self.egg_state = 'idle'
        self.platforms = [Platform(x=580, y=40, kind='fixed', width=145)]
        self.last_spawn_x = 580.0
        self.highest_y = 40.0
        self.generate_until(self.camera_y - 300)
        self.death_elapsed = 0.0

    def generate_until(self, y_goal: float) -> None:
        while self.highest_y > y_goal:
            i = int((40 - self.highest_y) // 116)
            height = self.random.randint(106, 145)
            next_y = self.highest_y - height
            next_x = min(838, max(245, self.last_spawn_x + self.random.uniform(-142, 142)))
            if i < 3:
                kind = 'fixed'
            else:
                kind = self.random.choices(
                    ['fixed', 'moving', 'small', 'fragile'], [0.65, 0.20, 0.10, 0.05]
                )[0]
            self.platforms.append(Platform(
                x=next_x, y=next_y, kind=kind,
                width={'fixed': 145, 'moving': 160, 'small': 100, 'fragile': 133}[kind],
                amplitude=42 if kind == 'moving' else 0,
                phase=self.random.uniform(0, math.tau),
            ))
            self.last_spawn_x = next_x
            self.highest_y = next_y

    def start(self) -> None:
        self.reset()
        self.velocity_y = JUMP_VY
        self.on_floor = False
        self.mode = 'playing'

    def update_fixed(self, dt: float) -> None:
        if self.mode == 'dying':
            self.death_elapsed += dt
            if self.death_elapsed > 0.68:
                self.mode = 'over'
            return
        if self.mode != 'playing':
            return

        self.time += dt
        keys = pg.key.get_pressed()
        left = keys[pg.K_LEFT] or keys[pg.K_a]
        right = keys[pg.K_RIGHT] or keys[pg.K_d]
        input_x = int(bool(right)) - int(bool(left))
        self.player_x = min(W - 35, max(35, self.player_x + input_x * RUN_SPEED * dt))

        old_feet = self.player_y + EGG_HALF_HEIGHT
        self.velocity_y += GRAVITY * dt
        self.player_y += self.velocity_y * dt
        new_feet = self.player_y + EGG_HALF_HEIGHT
        self.egg_state = 'jump' if self.velocity_y < 0 else 'fall'

        # Na descida, atravessar a altura do topo de uma cesta gera um novo salto.
        if self.velocity_y > 0:
            for platform in self.platforms:
                if platform.lifetime:
                    continue
                p_x = platform.center_at(self.time)
                if (old_feet <= platform.y <= new_feet and
                    abs(self.player_x - p_x) < (platform.width / 2 + 17)):
                    self.player_y = platform.y - EGG_HALF_HEIGHT
                    self.velocity_y = JUMP_VY
                    self.egg_state = 'jump'
                    if platform.kind == 'fragile':
                        platform.lifetime = 1
                    break

        self.max_height = max(self.max_height, max(0, -self.player_y))
        # Subida: a câmera acompanha; descida: não desce atrás do ovo.
        target = self.player_y - H * 0.44
        if target < self.camera_y:
            self.camera_y = target

        self.generate_until(self.camera_y - 250)
        self.platforms = [p for p in self.platforms if p.y < self.camera_y + H + 160]
        if self.player_y - self.camera_y > H + 65:
            self.mode = 'dying'
            self.death_elapsed = 0.0
            score = int(self.max_height / 10)
            if score > self.best:
                self.best = score
                self.save_record()

    def draw_background(self) -> None:
        ascent = max(0.0, self.initial_camera_y - self.camera_y)
        self.frame.fill((96, 185, 247))
        if self.show_parts[0]:
            # O céu contém apenas nuvens e tonalidades azuis; não possui objetos de primeiro plano.
            x = -int(ascent * 0.015) % 240
            self.frame.blit(self.sky, (-x, 0))
            if x > 0:
                self.frame.blit(self.sky, (1200 - x, 0))
        if self.show_parts[1]:
            # Montanhas deslocam 16% do avanço vertical da câmera.
            y = 205 + ascent * .16
            if y < H:
                self.frame.blit(self.mountains, (-100, int(y)))
        if self.show_parts[2]:
            # Vilarejo desloca 38% do avanço e desaparece conforme o ovo ganha altura.
            y = 455 + ascent * .38
            if y < H:
                self.frame.blit(self.village, (-95, int(y)))

    def draw_tree(self) -> None:
        if not self.show_parts[3]:
            return
        # Núcleo sem costura vertical, módulo de textura 300x420.
        size_y = self.trunk.get_height()
        first = math.floor((self.camera_y - size_y) / size_y)
        last = math.ceil((self.camera_y + H + size_y) / size_y)
        for i in range(first, last):
            self.frame.blit(self.trunk, (24, round(i * size_y - self.camera_y)))
        # Galhos e folhas independentes do núcleo, em ordem determinística.
        # A borda das peças decorativas é suavizada para esconder transições.
        spacing = 300
        first = math.floor((self.camera_y - spacing) / spacing)
        last = math.ceil((self.camera_y + H + spacing) / spacing)
        for i in range(first, last):
            part = self.tree_parts[i % len(self.tree_parts)]
            x = 172 - part.get_width() // 2 + ((i * 23) % 19 - 9)
            self.frame.blit(part, (x, round(i * spacing - self.camera_y)))

    def draw_world(self) -> None:
        for p in self.platforms:
            py = p.y - self.camera_y
            if py < -100 or py > H + 130 or p.lifetime:
                continue
            surf = self.baskets[p.kind]
            x = p.center_at(self.time)
            # O aro da cesta fica acima da plataforma física; não é uma parede sólida.
            px = x - surf.get_width() // 2
            self.frame.blit(surf, (int(px), int(py) - 29))
            if self.show_hitboxes:
                pg.draw.line(self.frame, (255, 80, 80), (x - p.width / 2, py), (x + p.width / 2, py), 3)

        state = self.egg_state if self.mode != 'dying' else 'death'
        frames = self.egg_frames[state]
        index = int((self.death_elapsed if state == 'death' else self.time) * (9 if state == 'death' else 6))
        sprite = frames[min(len(frames) - 1, index) if state == 'death' else index % len(frames)]
        px = self.player_x - sprite.get_width() / 2
        py = self.player_y - self.camera_y - sprite.get_height() / 2
        if -110 < py < H + 100:
            self.frame.blit(sprite, (int(px), int(py)))
            if self.show_hitboxes and state != 'death':
                pg.draw.rect(self.frame, (255, 75, 70), pg.Rect(int(self.player_x - 27), int(self.player_y - self.camera_y - EGG_HALF_HEIGHT), 54, 72), 2)

    def text(self, value: str, x: int, y: int, color=(35, 31, 24), *, style: str = 'body', center=False) -> None:
        f = {'small': self.font_small, 'body': self.font_body, 'title': self.font_title, 'num': self.font_num}[style]
        surface = f.render(value, True, color)
        if center:
            x -= surface.get_width() // 2
        self.frame.blit(surface, (x, y))

    def panel(self, rect: pg.Rect, alpha=224) -> None:
        shadow = pg.Surface((rect.w, rect.h), pg.SRCALPHA)
        pg.draw.rect(shadow, (35, 29, 21, 150), shadow.get_rect(), border_radius=19)
        self.frame.blit(shadow, rect.move(5, 6).topleft)
        tile = pg.Surface((rect.w, rect.h), pg.SRCALPHA)
        pg.draw.rect(tile, (255, 239, 203, alpha), tile.get_rect(), border_radius=19)
        pg.draw.rect(tile, (116, 70, 37, 255), tile.get_rect(), 3, border_radius=19)
        self.frame.blit(tile, rect.topleft)

    def draw_hud(self) -> None:
        self.panel(pg.Rect(20, 16, 205, 108), 232)
        self.text('ALTURA', 36, 22, style='small')
        self.text(f'{int(self.max_height / 10):04} m', 34, 49, style='num')
        self.text(f'RECORDE: {self.best:04} m', 36, 91, style='small')
        self.panel(pg.Rect(875, 16, 63, 55), 235)
        self.text('II', 897, 22, style='num')
        if self.show_debug:
            info = f'camera {self.camera_y:.0f} | chunks {len(self.platforms)} | FPS {self.clock.get_fps():.0f}'
            self.text(info, 18, H - 28, (255, 250, 240), style='small')

    def overlay(self, alpha=148) -> None:
        mask = pg.Surface((W, H), pg.SRCALPHA)
        mask.fill((16, 29, 31, alpha))
        self.frame.blit(mask, (0, 0))

    def draw_menu(self) -> None:
        self.overlay(75)
        self.panel(pg.Rect(272, 132, 416, 436), 245)
        self.text('EGG GAME', W // 2, 156, (114, 72, 39), style='title', center=True)
        self.text('DE VOLTA AO NINHO', W // 2, 236, center=True)
        self.text('Um ovo. Uma arvore. Muitas cestas.', W // 2, 309, style='small', center=True)
        self.text('ENTER / ESPACO — JOGAR', W // 2, 373, center=True)
        self.text('A / D ou SETAS — MOVER', W // 2, 425, style='small', center=True)
        self.text('O salto e automatico', W // 2, 455, style='small', center=True)
        self.text('ESC — SAIR', W // 2, 507, style='small', center=True)

    def draw_pause(self) -> None:
        self.overlay()
        self.panel(pg.Rect(290, 210, 380, 270))
        self.text('PAUSADO', W // 2, 236, style='title', center=True)
        self.text('P / ESPACO — CONTINUAR', W // 2, 349, center=True)
        self.text('R — REINICIAR    ESC — MENU', W // 2, 410, style='small', center=True)

    def draw_over(self) -> None:
        self.overlay(172)
        self.panel(pg.Rect(273, 150, 414, 427), 246)
        death = self.egg_frames['death'][-1]
        death = pg.transform.smoothscale(death, (128, 148))
        self.frame.blit(death, (416, 165))
        self.text('GAME OVER', W // 2, 313, (146, 56, 39), style='num', center=True)
        self.text(f'ALTURA: {int(self.max_height / 10):04} m', W // 2, 377, center=True)
        self.text(f'RECORDE: {self.best:04} m', W // 2, 418, center=True)
        self.text('ENTER — TENTAR DE NOVO', W // 2, 477, style='small', center=True)
        self.text('ESC — MENU', W // 2, 521, style='small', center=True)

    def draw(self) -> None:
        self.draw_background()
        self.draw_tree()
        self.draw_world()
        if self.mode == 'menu':
            self.draw_menu()
        else:
            self.draw_hud()
            if self.mode == 'paused':
                self.draw_pause()
            elif self.mode == 'over':
                self.draw_over()
        if self.window.get_size() == (W, H):
            self.window.blit(self.frame, (0, 0))
        else:
            pg.transform.smoothscale(self.frame, self.window.get_size(), self.window)
        pg.display.flip()

    def run(self) -> None:
        running = True
        accumulator = 0.0
        while running:
            dt_real = min(0.05, self.clock.tick(FPS) / 1000.0)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.VIDEORESIZE:
                    pass  # janela RESIZABLE, desenho reescalado sem alterar a física
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_F1:
                        self.show_debug = not self.show_debug
                    elif event.key == pg.K_h:
                        self.show_hitboxes = not self.show_hitboxes
                    elif event.key in [pg.K_1, pg.K_2, pg.K_3, pg.K_4]:
                        idx = event.key - pg.K_1
                        self.show_parts[idx] = not self.show_parts[idx]
                    elif event.key == pg.K_F12:
                        pg.image.save(self.frame, str(BASE / 'captura.png'))
                    elif self.mode == 'menu':
                        if event.key in [pg.K_RETURN, pg.K_SPACE]:
                            self.start()
                        elif event.key == pg.K_ESCAPE:
                            running = False
                    elif self.mode == 'over':
                        if event.key in [pg.K_RETURN, pg.K_SPACE, pg.K_r]:
                            self.start()
                        elif event.key == pg.K_ESCAPE:
                            self.mode = 'menu'
                    elif self.mode in ['playing', 'paused']:
                        if event.key in [pg.K_p, pg.K_SPACE]:
                            self.mode = 'paused' if self.mode == 'playing' else 'playing'
                        elif event.key == pg.K_r:
                            self.start()
                        elif event.key == pg.K_ESCAPE:
                            self.mode = 'menu'
            accumulator = min(.10, accumulator + dt_real)
            while accumulator >= FIXED_DT:
                self.update_fixed(FIXED_DT)
                accumulator -= FIXED_DT
            self.draw()
        pg.quit()


if __name__ == '__main__':
    EggGame().run()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pac-Man — clone didático em Pygame
==================================
Labirinto azul, bolinhas, power pellets, Pac-Man amarelo e 4 fantasmas
com modos chase / scatter / frightened. Feito para as aulas do Elzo.

Controles:
  Setas   — mover
  R       — reiniciar
  ESC     — sair

Rodar:
  python3 main.py
  python3 main.py --demo   # auto-piloto + prints/
"""

from __future__ import annotations

import argparse
import os
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# Labirinto: # parede  . bolinha  o power  - porta  ' ' vazio  = túnel
# ---------------------------------------------------------------------------
MAPA_TXT = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "     #.##### ## #####.#     ",
    "     #.##          ##.#     ",
    "     #.## ###--### ##.#     ",
    "######.## #      # ##.######",
    "      .   #      #   .      ",
    "######.## #      # ##.######",
    "     #.## ######## ##.#     ",
    "     #.##          ##.#     ",
    "     #.## ######## ##.#     ",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o..##................##..o#",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
]

COLS = len(MAPA_TXT[0])
ROWS = len(MAPA_TXT)
TILE = 24
LARGURA = COLS * TILE
ALTURA = ROWS * TILE + 60
FPS = 60

PRETO = (0, 0, 0)
AZUL = (33, 33, 255)
AZUL_CLARO = (60, 60, 255)
BRANCO = (255, 255, 255)
AMARELO = (255, 255, 0)
VERMELHO = (255, 0, 0)
ROSA = (255, 184, 255)
CIANO = (0, 255, 255)
LARANJA = (255, 184, 82)
AZUL_FRIGHT = (33, 33, 222)
PORTA = (255, 255, 255)

Dir = Tuple[int, int]
DIRS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
OPOSTO = {(0, -1): (0, 1), (0, 1): (0, -1), (-1, 0): (1, 0), (1, 0): (-1, 0)}


def parse_mapa() -> Tuple[List[List[str]], List[Tuple[int, int]], List[Tuple[int, int]]]:
    grid = [list(row) for row in MAPA_TXT]
    dots, powers = [], []
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == ".":
                dots.append((x, y))
            elif ch == "o":
                powers.append((x, y))
    return grid, dots, powers


def andavel(grid, x: int, y: int, porta_ok: bool = False) -> bool:
    # túneis laterais
    if y < 0 or y >= ROWS:
        return False
    if x < 0 or x >= COLS:
        return True  # wrap
    ch = grid[y][x]
    if ch == "#":
        return False
    if ch == "-" and not porta_ok:
        return False
    return True


@dataclass
class Entidade:
    x: float
    y: float
    dx: int = 0
    dy: int = 0
    prox_dx: int = 0
    prox_dy: int = 0
    velocidade: float = 4.0

    @property
    def tx(self) -> int:
        return int(self.x)

    @property
    def ty(self) -> int:
        return int(self.y)

    def centro_pixel(self) -> Tuple[int, int]:
        return int(self.x * TILE + TILE / 2), int(self.y * TILE + TILE / 2)


class Fantasma(Entidade):
    def __init__(self, x, y, cor, nome, scatter_alvo):
        super().__init__(x, y, velocidade=3.2)
        self.cor = cor
        self.nome = nome
        self.scatter_alvo = scatter_alvo
        self.modo = "scatter"  # scatter | chase | frightened | eyes
        self.casa = True
        self.timer_saida = 0.0


class Jogo:
    def __init__(self, demo: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("Pac-Man — didático")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("dejavusansmono", 22)
        self.fonte_p = pygame.font.SysFont("dejavusans", 16)
        self.demo = demo
        self.grid, _, _ = parse_mapa()
        self.reiniciar(completo=True)
        self.pedir_print: List[str] = []
        self.prints_feitos: set = set()
        self.demo_timer = 0.0
        self.modo_timer = 0.0
        self.frightened_timer = 0.0
        self.fase_scatter = True

    def reiniciar(self, completo: bool = False) -> None:
        self.grid, self.dots, self.powers = parse_mapa()
        # Pac-Man nasce abaixo da casa
        self.pac = Entidade(13.0, 20.0, -1, 0, velocidade=4.0)
        self.pac.prox_dx, self.pac.prox_dy = -1, 0
        self.fantasmas = [
            Fantasma(13.0, 11.0, VERMELHO, "blinky", (COLS - 2, 0)),
            Fantasma(11.5, 14.0, ROSA, "pinky", (1, 0)),
            Fantasma(13.0, 14.0, CIANO, "inky", (COLS - 2, ROWS - 1)),
            Fantasma(14.5, 14.0, LARANJA, "clyde", (1, ROWS - 1)),
        ]
        for i, g in enumerate(self.fantasmas):
            g.timer_saida = i * 2.5
            g.casa = True
            g.dx, g.dy = 0, -1
        self.score = 0 if completo else getattr(self, "score", 0)
        self.vidas = 3 if completo else self.vidas
        self.vivo = True
        self.vitoria = False
        self.game_over = False
        self.frightened = False
        self.modo_timer = 0.0
        self.mouth = 0.0

    def tile_centro(self, ent: Entidade) -> bool:
        px = ent.x * TILE + TILE / 2
        py = ent.y * TILE + TILE / 2
        cx = ent.tx * TILE + TILE / 2
        cy = ent.ty * TILE + TILE / 2
        return abs(px - cx) < ent.velocidade and abs(py - cy) < ent.velocidade

    def wrap(self, ent: Entidade) -> None:
        if ent.x < -0.5:
            ent.x = COLS - 0.5
        elif ent.x > COLS - 0.5:
            ent.x = -0.5

    def mover_pac(self) -> None:
        p = self.pac
        # tenta mudar direção no centro do tile
        if self.tile_centro(p):
            p.x, p.y = float(p.tx), float(p.ty)
            nx, ny = p.tx + p.prox_dx, p.ty + p.prox_dy
            if andavel(self.grid, nx, ny):
                p.dx, p.dy = p.prox_dx, p.prox_dy
            # se direção atual bloqueada, para
            nx2, ny2 = p.tx + p.dx, p.ty + p.dy
            if not andavel(self.grid, nx2, ny2):
                p.dx = p.dy = 0
        p.x += p.dx * p.velocidade / TILE
        p.y += p.dy * p.velocidade / TILE
        self.wrap(p)
        # come bolinhas
        tx, ty = p.tx, p.ty
        if 0 <= tx < COLS and 0 <= ty < ROWS:
            if (tx, ty) in self.dots:
                self.dots.remove((tx, ty))
                self.score += 10
                self.grid[ty][tx] = " "
            if (tx, ty) in self.powers:
                self.powers.remove((tx, ty))
                self.score += 50
                self.grid[ty][tx] = " "
                self.frightened = True
                self.frightened_timer = 6.0
                for g in self.fantasmas:
                    if g.modo != "eyes":
                        g.modo = "frightened"
                        g.dx, g.dy = OPOSTO.get((g.dx, g.dy), (g.dx, g.dy))
        if not self.dots and not self.powers:
            self.vitoria = True

    def alvos_fantasma(self, g: Fantasma) -> Tuple[int, int]:
        if g.modo == "eyes":
            return 13, 11
        if g.modo == "frightened":
            return random.randint(0, COLS - 1), random.randint(0, ROWS - 1)
        if g.modo == "scatter":
            return g.scatter_alvo
        # chase
        px, py = self.pac.tx, self.pac.ty
        if g.nome == "blinky":
            return px, py
        if g.nome == "pinky":
            return px + self.pac.dx * 4, py + self.pac.dy * 4
        if g.nome == "inky":
            return px + (px - self.fantasmas[0].tx), py + (py - self.fantasmas[0].ty)
        # clyde: chase se longe, senão scatter
        dist2 = (g.tx - px) ** 2 + (g.ty - py) ** 2
        if dist2 > 64:
            return px, py
        return g.scatter_alvo

    def mover_fantasma(self, g: Fantasma, dt: float) -> None:
        if g.casa:
            g.timer_saida -= dt
            # oscila na casa
            g.y += g.dy * 0.03
            if g.y < 13.3 or g.y > 14.7:
                g.dy *= -1
            if g.timer_saida <= 0:
                g.casa = False
                g.x, g.y = 13.0, 11.0
                g.dx, g.dy = random.choice([(-1, 0), (1, 0)])
                g.modo = "scatter" if self.fase_scatter else "chase"
            return
        if self.tile_centro(g):
            g.x, g.y = float(g.tx), float(g.ty)
            alvo = self.alvos_fantasma(g)
            opcoes = []
            for d in DIRS.values():
                if d == OPOSTO.get((g.dx, g.dy)) and g.modo != "frightened":
                    # fantasmas não revertem (exceto frightened já forçou)
                    if any(andavel(self.grid, g.tx + dd[0], g.ty + dd[1], porta_ok=(g.modo == "eyes"))
                           for dd in DIRS.values() if dd != d):
                        # só evita reverso se houver outra opção
                        nx, ny = g.tx + d[0], g.ty + d[1]
                        if andavel(self.grid, nx, ny, porta_ok=(g.modo == "eyes")):
                            # marca mas com peso baixo — na prática pulamos
                            continue
                nx, ny = g.tx + d[0], g.ty + d[1]
                if andavel(self.grid, nx, ny, porta_ok=(g.modo == "eyes")):
                    dist = (nx - alvo[0]) ** 2 + (ny - alvo[1]) ** 2
                    opcoes.append((dist, d))
            if not opcoes:
                # só reverso
                rev = OPOSTO.get((g.dx, g.dy), (0, 0))
                if andavel(self.grid, g.tx + rev[0], g.ty + rev[1], porta_ok=True):
                    opcoes.append((0, rev))
            if opcoes:
                if g.modo == "frightened":
                    _, d = random.choice(opcoes)
                else:
                    opcoes.sort(key=lambda t: t[0])
                    _, d = opcoes[0]
                g.dx, g.dy = d
        vel = 2.2 if g.modo == "frightened" else (5.0 if g.modo == "eyes" else g.velocidade)
        g.x += g.dx * vel / TILE
        g.y += g.dy * vel / TILE
        self.wrap(g)
        if g.modo == "eyes" and abs(g.x - 13) < 0.4 and abs(g.y - 11) < 0.4:
            g.modo = "chase" if not self.fase_scatter else "scatter"
            g.casa = True
            g.timer_saida = 1.5
            g.x, g.y = 13.0, 14.0

    def colisoes(self) -> None:
        px, py = self.pac.centro_pixel()
        for g in self.fantasmas:
            if g.casa or g.modo == "eyes":
                continue
            gx, gy = g.centro_pixel()
            if abs(px - gx) < TILE * 0.6 and abs(py - gy) < TILE * 0.6:
                if g.modo == "frightened":
                    g.modo = "eyes"
                    self.score += 200
                else:
                    self.vidas -= 1
                    if self.vidas <= 0:
                        self.game_over = True
                    else:
                        # respawn
                        self.pac = Entidade(13.0, 20.0, -1, 0, velocidade=4.0)
                        self.pac.prox_dx, self.pac.prox_dy = -1, 0
                        for i, gh in enumerate(self.fantasmas):
                            gh.casa = True
                            gh.x, gh.y = 13.0, 14.0
                            gh.timer_saida = i * 1.5
                            gh.modo = "scatter"

    def auto_piloto(self) -> None:
        """Demo: escolhe direção que aponta a bolinha mais próxima / foge de fantasmas."""
        p = self.pac
        if not self.tile_centro(p) and (p.dx or p.dy):
            return
        alvos = self.dots + self.powers
        if not alvos:
            return
        # foge se fantasma perto e não frightened
        perigo = None
        for g in self.fantasmas:
            if g.casa or g.modo in ("frightened", "eyes"):
                continue
            if (g.tx - p.tx) ** 2 + (g.ty - p.ty) ** 2 < 25:
                perigo = g
                break
        melhor = None
        melhor_score = -1e9
        for nome, d in DIRS.items():
            nx, ny = p.tx + d[0], p.ty + d[1]
            if not andavel(self.grid, nx, ny):
                continue
            # score: proximidade a bolinha - perigo
            dist_dot = min((nx - ax) ** 2 + (ny - ay) ** 2 for ax, ay in alvos)
            sc = -dist_dot
            if perigo:
                dist_g = (nx - perigo.tx) ** 2 + (ny - perigo.ty) ** 2
                sc += dist_g * 3
            # power se frightened acabando? preferir power
            if (nx, ny) in self.powers:
                sc += 50
            if (nx, ny) in self.dots:
                sc += 5
            if sc > melhor_score:
                melhor_score = sc
                melhor = d
        if melhor:
            p.prox_dx, p.prox_dy = melhor

    def atualizar(self, dt: float) -> None:
        if self.game_over or self.vitoria:
            return
        self.mouth += dt * 10
        self.modo_timer += dt
        # alterna scatter/chase a cada ~7s / 20s simplificado
        ciclo = 7.0 if self.fase_scatter else 20.0
        if self.modo_timer > ciclo and not self.frightened:
            self.modo_timer = 0.0
            self.fase_scatter = not self.fase_scatter
            novo = "scatter" if self.fase_scatter else "chase"
            for g in self.fantasmas:
                if g.modo in ("scatter", "chase"):
                    g.modo = novo
                    g.dx, g.dy = OPOSTO.get((g.dx, g.dy), (g.dx, g.dy))
        if self.frightened:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0:
                self.frightened = False
                for g in self.fantasmas:
                    if g.modo == "frightened":
                        g.modo = "chase" if not self.fase_scatter else "scatter"
        if self.demo:
            self.auto_piloto()
        self.mover_pac()
        for g in self.fantasmas:
            self.mover_fantasma(g, dt)
        self.colisoes()

    def desenhar_labirinto(self) -> None:
        self.tela.fill(PRETO)
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                px, py = x * TILE, y * TILE
                if ch == "#":
                    pygame.draw.rect(self.tela, AZUL, (px + 1, py + 1, TILE - 2, TILE - 2), border_radius=4)
                elif ch == "-":
                    pygame.draw.rect(self.tela, PORTA, (px + 2, py + TILE // 2 - 2, TILE - 4, 4))
        for x, y in self.dots:
            pygame.draw.circle(self.tela, BRANCO, (x * TILE + TILE // 2, y * TILE + TILE // 2), 3)
        for x, y in self.powers:
            pygame.draw.circle(self.tela, BRANCO, (x * TILE + TILE // 2, y * TILE + TILE // 2), 7)

    def desenhar_pac(self) -> None:
        cx, cy = self.pac.centro_pixel()
        abertura = abs(int(8 + 25 * abs(__import__("math").sin(self.mouth))))
        # direção da boca
        if self.pac.dx > 0:
            start, end = abertura, 360 - abertura
        elif self.pac.dx < 0:
            start, end = 180 + abertura, 180 - abertura + 360
        elif self.pac.dy < 0:
            start, end = 90 + abertura, 90 - abertura + 360
        elif self.pac.dy > 0:
            start, end = 270 + abertura, 270 - abertura + 360
        else:
            start, end = 30, 330
        rect = pygame.Rect(0, 0, TILE - 4, TILE - 4)
        rect.center = (cx, cy)
        pygame.draw.circle(self.tela, AMARELO, (cx, cy), TILE // 2 - 2)
        # "bocada" preta via polígono
        import math
        ang0 = math.radians(start)
        ang1 = math.radians(end if end > start else end + 360)
        # simplifica: desenha fatia preta
        if self.pac.dx or self.pac.dy:
            pts = [(cx, cy)]
            # boca aberta na direção
            if self.pac.dx > 0:
                a0, a1 = -abertura, abertura
            elif self.pac.dx < 0:
                a0, a1 = 180 - abertura, 180 + abertura
            elif self.pac.dy < 0:
                a0, a1 = 90 - abertura, 90 + abertura
            else:
                a0, a1 = 270 - abertura, 270 + abertura
            for a in range(int(a0), int(a1) + 1, 3):
                rad = math.radians(a)
                pts.append((cx + int((TILE // 2 - 1) * math.cos(rad)),
                            cy - int((TILE // 2 - 1) * math.sin(rad))))
            if len(pts) > 2:
                pygame.draw.polygon(self.tela, PRETO, pts)

    def desenhar_fantasma(self, g: Fantasma) -> None:
        cx, cy = g.centro_pixel()
        if g.modo == "eyes":
            cor = None
        elif g.modo == "frightened":
            cor = AZUL_FRIGHT if int(self.frightened_timer * 4) % 2 == 0 or self.frightened_timer > 2 else BRANCO
        else:
            cor = g.cor
        r = TILE // 2 - 2
        if cor:
            pygame.draw.circle(self.tela, cor, (cx, cy - 2), r)
            pygame.draw.rect(self.tela, cor, (cx - r, cy - 2, 2 * r, r + 4))
            # ondulação inferior
            for i in range(3):
                pygame.draw.circle(self.tela, cor, (cx - r + 4 + i * 8, cy + r - 2), 5)
        # olhos
        olho_c = BRANCO
        pupila = (33, 33, 222) if g.modo != "frightened" else BRANCO
        for ox in (-6, 6):
            pygame.draw.circle(self.tela, olho_c, (cx + ox, cy - 4), 5)
            pygame.draw.circle(self.tela, pupila, (cx + ox + g.dx * 2, cy - 4 + g.dy * 2), 2)

    def desenhar(self) -> None:
        self.desenhar_labirinto()
        self.desenhar_pac()
        for g in self.fantasmas:
            self.desenhar_fantasma(g)
        # HUD
        pygame.draw.rect(self.tela, PRETO, (0, ROWS * TILE, LARGURA, 60))
        txt = self.fonte.render(f"Score: {self.score}", True, BRANCO)
        self.tela.blit(txt, (16, ROWS * TILE + 8))
        vidas = self.fonte_p.render(f"Vidas: {self.vidas}", True, AMARELO)
        self.tela.blit(vidas, (16, ROWS * TILE + 34))
        if self.game_over:
            t = self.fonte.render("GAME OVER — R reinicia", True, VERMELHO)
            self.tela.blit(t, t.get_rect(center=(LARGURA // 2, ROWS * TILE // 2)))
        if self.vitoria:
            t = self.fonte.render("VOCÊ VENCEU!", True, AMARELO)
            self.tela.blit(t, t.get_rect(center=(LARGURA // 2, ROWS * TILE // 2)))
        pygame.display.flip()
        self._salvar_prints()

    def _salvar_prints(self) -> None:
        if not self.pedir_print:
            return
        pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prints")
        os.makedirs(pasta, exist_ok=True)
        for nome in self.pedir_print:
            pygame.image.save(self.tela, os.path.join(pasta, nome))
        self.pedir_print.clear()

    def _demo_prints(self) -> None:
        if "inicio.png" not in self.prints_feitos and self.demo_timer > 0.4:
            self.pedir_print.append("inicio.png")
            self.prints_feitos.add("inicio.png")
        if "meio.png" not in self.prints_feitos and self.score >= 50:
            self.pedir_print.append("meio.png")
            self.prints_feitos.add("meio.png")
        if "fim.png" not in self.prints_feitos and (self.demo_timer > 6.5 or self.game_over or self.vitoria):
            self.pedir_print.append("fim.png")
            self.prints_feitos.add("fim.png")

    def tratar(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return False
                if ev.key == pygame.K_r:
                    self.reiniciar(completo=True)
                if not self.demo:
                    if ev.key == pygame.K_LEFT:
                        self.pac.prox_dx, self.pac.prox_dy = -1, 0
                    if ev.key == pygame.K_RIGHT:
                        self.pac.prox_dx, self.pac.prox_dy = 1, 0
                    if ev.key == pygame.K_UP:
                        self.pac.prox_dx, self.pac.prox_dy = 0, -1
                    if ev.key == pygame.K_DOWN:
                        self.pac.prox_dx, self.pac.prox_dy = 0, 1
        return True

    def rodar(self) -> None:
        rodando = True
        while rodando:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            rodando = self.tratar()
            self.atualizar(dt)
            if self.demo:
                self.demo_timer += dt
                self._demo_prints()
            self.desenhar()
            if self.demo and self.demo_timer > 7.5:
                if "fim.png" not in self.prints_feitos:
                    self.pedir_print.append("fim.png")
                    self.prints_feitos.add("fim.png")
                    self.desenhar()
                rodando = False
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pac-Man didático (Pygame)")
    parser.add_argument("--demo", action="store_true", help="Auto-piloto + prints/")
    args = parser.parse_args()
    if args.demo and not os.environ.get("DISPLAY") and not os.environ.get("SDL_VIDEODRIVER"):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    Jogo(demo=args.demo).rodar()


if __name__ == "__main__":
    main()

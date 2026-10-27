#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flappy Bird — clone didático em Pygame
======================================
Pássaro amarelo, canos verdes, chão rolante, flap com espaço/clique.
Feito para as aulas do Elzo.

Controles:
  Espaço / clique — flap (bater asas)
  R               — reiniciar após game over
  ESC             — sair

Rodar:
  python3 main.py
  python3 main.py --demo   # auto-flap + prints/
"""

from __future__ import annotations

import argparse
import os
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
LARGURA = 400
ALTURA = 600
FPS = 60

CEU = (112, 197, 206)
VERDE_CANO = (96, 184, 52)
VERDE_BORDA = (70, 140, 35)
CHAO = (222, 216, 149)
CHAO_BORDA = (190, 160, 70)
AMARELO = (252, 210, 60)
LARANJA = (240, 128, 40)
BRANCO = (255, 255, 255)
PRETO = (30, 30, 30)
VERMELHO = (220, 60, 60)

GRAVIDADE = 0.45
FLAP_V = -8.0
VEL_SCROLL = 3.0
VAO = 150
LARGURA_CANO = 70
ALTURA_CHAO = 80


@dataclass
class Cano:
    x: float
    gap_y: float  # centro do vão
    passou: bool = False

    @property
    def topo_rect(self) -> pygame.Rect:
        h = int(self.gap_y - VAO / 2)
        return pygame.Rect(int(self.x), 0, LARGURA_CANO, h)

    @property
    def base_rect(self) -> pygame.Rect:
        y = int(self.gap_y + VAO / 2)
        return pygame.Rect(int(self.x), y, LARGURA_CANO, ALTURA - ALTURA_CHAO - y)


class Jogo:
    def __init__(self, demo: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("Flappy Bird — didático")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("dejavusans", 48, bold=True)
        self.fonte_m = pygame.font.SysFont("dejavusans", 22)
        self.fonte_p = pygame.font.SysFont("dejavusans", 16)
        self.demo = demo
        self.reiniciar()
        self.pedir_print: List[str] = []
        self.prints_feitos: set = set()
        self.demo_timer = 0.0

    def reiniciar(self) -> None:
        self.bird_x = 80.0
        self.bird_y = ALTURA / 2
        self.bird_v = 0.0
        self.angulo = 0.0
        self.canos: List[Cano] = []
        self.spawn_timer = 0.0
        self.score = 0
        self.vivo = True
        self.chao_off = 0.0
        self.asa = 0.0
        # primeiros canos
        for i in range(3):
            self.canos.append(self._novo_cano(LARGURA + 80 + i * 220))

    def _novo_cano(self, x: float) -> Cano:
        gap_y = random.randint(140, ALTURA - ALTURA_CHAO - 140)
        return Cano(x=x, gap_y=float(gap_y))

    def flap(self) -> None:
        if not self.vivo:
            return
        self.bird_v = FLAP_V
        self.asa = 0.25

    def bird_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.bird_x) - 14, int(self.bird_y) - 12, 28, 24)

    def atualizar(self, dt: float) -> None:
        self.asa = max(0.0, self.asa - dt)
        self.chao_off = (self.chao_off + VEL_SCROLL) % 40
        if not self.vivo:
            # cai um pouco
            self.bird_v += GRAVIDADE
            self.bird_y += self.bird_v
            return
        self.bird_v += GRAVIDADE
        self.bird_y += self.bird_v
        self.angulo = max(-30, min(70, self.bird_v * 4))
        # canos
        self.spawn_timer += dt
        for c in self.canos:
            c.x -= VEL_SCROLL
            if not c.passou and c.x + LARGURA_CANO < self.bird_x:
                c.passou = True
                self.score += 1
        self.canos = [c for c in self.canos if c.x > -LARGURA_CANO - 10]
        if not self.canos or self.canos[-1].x < LARGURA - 220:
            self.canos.append(self._novo_cano(LARGURA + 40))
        # colisões
        br = self.bird_rect()
        chao_y = ALTURA - ALTURA_CHAO
        if br.bottom >= chao_y or br.top <= 0:
            self.vivo = False
            return
        for c in self.canos:
            if br.colliderect(c.topo_rect) or br.colliderect(c.base_rect):
                self.vivo = False
                return
        if self.demo:
            self._auto_flap()

    def _auto_flap(self) -> None:
        """Mantém o pássaro perto do centro do vão do próximo cano."""
        prox = None
        for c in self.canos:
            if c.x + LARGURA_CANO >= self.bird_x - 20:
                prox = c
                break
        alvo = ALTURA / 2 - 20
        if prox:
            alvo = prox.gap_y
        # margem de segurança abaixo do alvo
        if self.bird_y > alvo + 8 and self.bird_v > -4:
            self.flap()
        if self.bird_y > ALTURA - ALTURA_CHAO - 80 and self.bird_v >= 0:
            self.flap()
        if self.bird_y < 40 and self.bird_v < 0:
            pass  # deixa cair um pouco

    def desenhar_cano(self, c: Cano) -> None:
        for rect in (c.topo_rect, c.base_rect):
            pygame.draw.rect(self.tela, VERDE_CANO, rect)
            pygame.draw.rect(self.tela, VERDE_BORDA, rect, 3)
            # boca do cano
            if rect.y == 0:
                boca = pygame.Rect(rect.x - 4, rect.bottom - 28, rect.w + 8, 28)
            else:
                boca = pygame.Rect(rect.x - 4, rect.top, rect.w + 8, 28)
            pygame.draw.rect(self.tela, VERDE_CANO, boca)
            pygame.draw.rect(self.tela, VERDE_BORDA, boca, 3)

    def desenhar_bird(self) -> None:
        cx, cy = int(self.bird_x), int(self.bird_y)
        # corpo
        corpo = pygame.Surface((36, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(corpo, AMARELO, (0, 2, 32, 24))
        pygame.draw.ellipse(corpo, PRETO, (0, 2, 32, 24), 2)
        # asa
        asa_y = 6 if self.asa > 0 else 12
        pygame.draw.ellipse(corpo, (250, 180, 40), (6, asa_y, 16, 10))
        pygame.draw.ellipse(corpo, PRETO, (6, asa_y, 16, 10), 1)
        # olho
        pygame.draw.circle(corpo, BRANCO, (24, 10), 5)
        pygame.draw.circle(corpo, PRETO, (26, 10), 2)
        # bico
        pygame.draw.polygon(corpo, LARANJA, [(30, 12), (40, 14), (30, 18)])
        pygame.draw.polygon(corpo, PRETO, [(30, 12), (40, 14), (30, 18)], 1)
        rot = pygame.transform.rotate(corpo, -self.angulo)
        self.tela.blit(rot, rot.get_rect(center=(cx, cy)))

    def desenhar_chao(self) -> None:
        y = ALTURA - ALTURA_CHAO
        pygame.draw.rect(self.tela, CHAO, (0, y, LARGURA, ALTURA_CHAO))
        pygame.draw.rect(self.tela, CHAO_BORDA, (0, y, LARGURA, 8))
        # faixas
        for i in range(-1, LARGURA // 40 + 2):
            x = int(i * 40 - self.chao_off)
            pygame.draw.line(self.tela, CHAO_BORDA, (x, y + 8), (x + 20, y + 8), 3)

    def desenhar(self) -> None:
        self.tela.fill(CEU)
        # nuvens simples
        for cx, cy, r in ((60, 80, 28), (200, 50, 22), (320, 90, 30)):
            pygame.draw.circle(self.tela, (230, 245, 250), (cx, cy), r)
            pygame.draw.circle(self.tela, (230, 245, 250), (cx + 20, cy + 5), r - 6)
        for c in self.canos:
            self.desenhar_cano(c)
        self.desenhar_chao()
        self.desenhar_bird()
        # score
        img = self.fonte.render(str(self.score), True, BRANCO)
        sombra = self.fonte.render(str(self.score), True, PRETO)
        self.tela.blit(sombra, (LARGURA // 2 - img.get_width() // 2 + 2, 42))
        self.tela.blit(img, (LARGURA // 2 - img.get_width() // 2, 40))
        if not self.vivo:
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.tela.blit(overlay, (0, 0))
            t = self.fonte_m.render("GAME OVER", True, BRANCO)
            self.tela.blit(t, t.get_rect(center=(LARGURA // 2, ALTURA // 2 - 30)))
            s = self.fonte_p.render(f"Score: {self.score}  ·  R reinicia  ·  Espaço também", True, BRANCO)
            self.tela.blit(s, s.get_rect(center=(LARGURA // 2, ALTURA // 2 + 10)))
        else:
            dica = self.fonte_p.render("Espaço / clique = flap", True, (40, 80, 90))
            self.tela.blit(dica, (10, ALTURA - 24))
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
        if "inicio.png" not in self.prints_feitos and self.demo_timer > 0.3:
            self.pedir_print.append("inicio.png")
            self.prints_feitos.add("inicio.png")
        if "meio.png" not in self.prints_feitos and (self.score >= 1 or self.demo_timer > 2.5):
            self.pedir_print.append("meio.png")
            self.prints_feitos.add("meio.png")
        if "fim.png" not in self.prints_feitos and (not self.vivo or self.demo_timer > 6.5):
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
                    self.reiniciar()
                if ev.key == pygame.K_SPACE:
                    if not self.vivo:
                        self.reiniciar()
                    else:
                        self.flap()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if not self.vivo:
                    self.reiniciar()
                else:
                    self.flap()
        return True

    def rodar(self) -> None:
        rodando = True
        while rodando:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            # física em passos fixos-ish: usa fator de frame
            # (valores de gravidade calibrados a ~60 FPS)
            frames = max(1, int(round(dt * FPS)))
            rodando = self.tratar()
            for _ in range(min(frames, 3)):
                self.atualizar(1.0 / FPS)
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
            if self.demo and "fim.png" in self.prints_feitos and not self.vivo and self.demo_timer > 1.5:
                rodando = False
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Flappy Bird didático (Pygame)")
    parser.add_argument("--demo", action="store_true", help="Auto-flap + prints/")
    args = parser.parse_args()
    if args.demo and not os.environ.get("DISPLAY") and not os.environ.get("SDL_VIDEODRIVER"):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    Jogo(demo=args.demo).rodar()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrida de Espermatozoides — protótipo didático em Pygame
==========================================================
Inspirado num joguinho web engraçado que o professor Elzo achou.
Estilo visual: corrida pseudo-3D (OutRun / Top Gear), vista de trás.

Controles:
  Setas / WASD  — mover esquerda/direita
  Espaço        — impulso / turbo (gasta energia)
  P             — pausa
  R             — reiniciar
  ESC           — sair

Rodar:
  python3 main.py
  python3 main.py --demo   # autoplay + screenshots em prints/

Só usa pygame e desenho com primitivas (círculos, elipses, polígonos, seno).
"""

from __future__ import annotations

import argparse
import math
import os
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# ---------------------------------------------------------------------------
# Constantes da janela e do jogo
# ---------------------------------------------------------------------------
LARGURA = 1024
ALTURA = 576
FPS = 60
TITULO = "Corrida de Espermatozoides — protótipo"

TOTAL_CORREDORES = 80
COMPRIMENTO_PISTA = 3800.0
META_Z = COMPRIMENTO_PISTA
SEG_LEN = 16.0

# Cores do túnel / pista (tons rosados)
ROSA_CLARO = (255, 190, 200)
ROSA_MEDIO = (240, 130, 155)
ROSA_ESCURO = (200, 80, 110)
ROSA_PAREDE_A = (170, 55, 95)
ROSA_PAREDE_B = (140, 40, 80)
ROSA_TETO_A = (120, 45, 75)
ROSA_TETO_B = (95, 30, 60)
ROSA_FUNDO = (70, 20, 45)
BRANCO = (255, 255, 255)
PRETO = (25, 12, 22)
AMARELO = (255, 230, 80)
CIANO = (120, 230, 255)
VERDE = (80, 220, 120)
VERMELHO = (255, 80, 100)
DOURADO = (255, 210, 60)
CINZA_HUD = (40, 20, 35)
ZEBRA_A = (255, 255, 255)
ZEBRA_B = (35, 15, 30)

# Perspectiva OutRun:
# y_tela = HORIZONTE_Y + PROJ_Y / z_rel
# Em z_rel ≈ Z_PERTO, y chega perto da base da tela.
HORIZONTE_Y = 160
Z_PERTO = 12.0
PROJ_Y = (ALTURA - 30 - HORIZONTE_Y) * Z_PERTO   # ~4632
PROJ_W = 520.0 * Z_PERTO                           # largura da pista perto
FOV_BASE = 1.0
FOV_TURBO = 1.22


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def clamp(v: float, a: float, b: float) -> float:
    return a if v < a else b if v > b else v


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def cor_lerp(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = clamp(t, 0.0, 1.0)
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


# ---------------------------------------------------------------------------
# Pista: segmentos com curvatura
# ---------------------------------------------------------------------------
@dataclass
class Segmento:
    z: float
    curva: float = 0.0
    largura: float = 1.0


def gerar_pista(comprimento: float) -> List[Segmento]:
    segs: List[Segmento] = []
    z = 0.0
    curva = 0.0
    alvo = 0.0
    while z < comprimento + 400:
        if int(z / SEG_LEN) % 18 == 0:
            alvo = random.uniform(-1.8, 1.8)
            if z < 280 or z > comprimento - 500:
                alvo = 0.0
        curva = lerp(curva, alvo, 0.06)
        largura = 0.82 if 1500 < z < 2300 else 1.0
        segs.append(Segmento(z=z, curva=curva, largura=largura))
        z += SEG_LEN
    return segs


# ---------------------------------------------------------------------------
# Corredores
# ---------------------------------------------------------------------------
@dataclass
class Corredor:
    nome: str
    z: float
    x: float
    vx: float = 0.0
    velocidade: float = 0.0
    velocidade_base: float = 40.0
    energia: float = 100.0
    turbo: bool = False
    eh_jogador: bool = False
    cor_corpo: Tuple[int, int, int] = (255, 245, 200)
    fase_cauda: float = 0.0
    empurrado: float = 0.0
    terminou: bool = False
    tempo_chegada: float = 0.0
    alvo_x: float = 0.0
    timer_ia: float = 0.0


def criar_rivais(n: int) -> List[Corredor]:
    rivais = []
    cores = [
        (255, 240, 180), (255, 220, 200), (240, 255, 200),
        (255, 200, 220), (230, 230, 255), (255, 255, 210),
        (250, 230, 190), (255, 235, 215),
    ]
    for i in range(n):
        z0 = random.uniform(-50, 80)
        x0 = random.uniform(-0.75, 0.75)
        vb = random.uniform(32.0, 50.0)
        rivais.append(Corredor(
            nome=f"Rival {i+1}",
            z=z0,
            x=x0,
            velocidade=vb * 0.55,
            velocidade_base=vb,
            cor_corpo=random.choice(cores),
            fase_cauda=random.uniform(0, math.tau),
            alvo_x=x0,
            timer_ia=random.uniform(0.4, 2.0),
        ))
    return rivais


@dataclass
class Globulo:
    z: float
    x: float
    raio: float
    fase: float = 0.0


def gerar_globulos(pista_len: float, qtd: int = 30) -> List[Globulo]:
    return [
        Globulo(
            z=random.uniform(300, pista_len - 400),
            x=random.uniform(-0.65, 0.65),
            raio=random.uniform(0.07, 0.14),
            fase=random.uniform(0, math.tau),
        )
        for _ in range(qtd)
    ]


@dataclass
class Particula:
    x: float
    y: float
    vy: float
    vida: float
    comprimento: float


# ---------------------------------------------------------------------------
# Projeção pseudo-3D
# ---------------------------------------------------------------------------
def projetar_yz(z_rel: float, fov: float) -> Tuple[float, float]:
    """Retorna (y_tela, fator_escala) para uma distância z_rel à frente."""
    z_rel = max(z_rel, 2.0)
    inv = fov / z_rel
    y = HORIZONTE_Y + PROJ_Y * inv
    escala = PROJ_W * inv  # "metade da pista" em px quando largura=1
    return y, escala


# ---------------------------------------------------------------------------
# Desenho dos sprites (só primitivas)
# ---------------------------------------------------------------------------
def desenhar_esperma(surf: pygame.Surface, cx: float, cy: float, escala: float,
                     cor: Tuple[int, int, int], fase: float,
                     destaque: bool = False, inclinacao: float = 0.0) -> None:
    """Espermatozoide fofo visto de trás/cima: cabeça + carinha + cauda senoidal."""
    if escala < 0.35:
        pygame.draw.circle(surf, cor, (int(cx), int(cy)), max(1, int(escala * 3)))
        return

    s = escala
    rw = max(2, int(9 * s))
    rh = max(2, int(12 * s))
    rect = pygame.Rect(int(cx - rw), int(cy - rh), rw * 2, rh * 2)
    pygame.draw.ellipse(surf, cor, rect)
    borda = (255, 255, 255) if destaque else (210, 170, 130)
    pygame.draw.ellipse(surf, borda, rect, max(1, int(min(s, 3))))

    if s > 1.0:
        olho_y = cy - rh * 0.28
        olho_dx = rw * 0.38
        orad = max(1, int(1.5 * s))
        pygame.draw.circle(surf, PRETO, (int(cx - olho_dx), int(olho_y)), orad)
        pygame.draw.circle(surf, PRETO, (int(cx + olho_dx), int(olho_y)), orad)
        if s > 1.4:
            smile = pygame.Rect(
                int(cx - rw * 0.45), int(cy - rh * 0.05),
                int(rw * 0.9), int(rh * 0.55),
            )
            pygame.draw.arc(surf, PRETO, smile, math.pi * 1.1, math.pi * 1.9,
                            max(1, int(s * 0.6)))

    # Cauda ondulada (para baixo = atrás, na vista de trás)
    n = max(5, int(9 * min(s, 3.5)))
    comprimento = 20 * s
    pontos = []
    for i in range(n + 1):
        t = i / n
        onda = math.sin(fase + t * 4.8) * (5.0 * s) * (0.25 + 0.75 * t)
        px = cx + onda + inclinacao * t * 10
        py = cy + rh * 0.9 + t * comprimento
        pontos.append((px, py))
    if len(pontos) >= 2:
        esp = max(1, int(2.0 * s))
        pygame.draw.lines(surf, cor, False, pontos, esp)
        pygame.draw.circle(surf, BRANCO, (int(pontos[-1][0]), int(pontos[-1][1])),
                           max(1, esp // 2))


def desenhar_globulo(surf: pygame.Surface, cx: float, cy: float,
                     raio_px: float, fase: float) -> None:
    r = max(3, int(raio_px))
    pygame.draw.circle(surf, (255, 150, 180), (int(cx), int(cy)), r + 3)
    pygame.draw.circle(surf, (255, 100, 140), (int(cx), int(cy)), r)
    pygame.draw.circle(surf, (255, 220, 230),
                       (int(cx - r * 0.3), int(cy - r * 0.3)), max(1, r // 3))
    pulso = int(2 + math.sin(fase) * 1.5)
    pygame.draw.circle(surf, (255, 180, 200), (int(cx), int(cy)), r + pulso, 1)


def desenhar_ovulo(surf: pygame.Surface, cx: float, cy: float, escala: float) -> None:
    r = max(4, int(26 * escala))
    for i in range(5, 0, -1):
        c = cor_lerp((255, 230, 120), (255, 170, 190), i / 5)
        pygame.draw.circle(surf, c, (int(cx), int(cy)), r + i * 5)
    pygame.draw.circle(surf, (255, 240, 210), (int(cx), int(cy)), r)
    pygame.draw.circle(surf, (255, 200, 160), (int(cx), int(cy)), int(r * 0.7))
    pygame.draw.circle(surf, (255, 140, 120), (int(cx), int(cy)), max(2, int(r * 0.32)))
    pygame.draw.circle(surf, BRANCO,
                       (int(cx - r * 0.35), int(cy - r * 0.35)), max(2, r // 5))


# ---------------------------------------------------------------------------
# Jogo
# ---------------------------------------------------------------------------
class Jogo:
    def __init__(self, demo: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("DejaVu Sans", 22)
        self.fonte_g = pygame.font.SysFont("DejaVu Sans", 48, bold=True)
        self.fonte_m = pygame.font.SysFont("DejaVu Sans", 28, bold=True)
        self.fonte_p = pygame.font.SysFont("DejaVu Sans", 16)
        self.demo = demo
        self.som_ligado = True
        self.reiniciar()

    def reiniciar(self) -> None:
        random.seed(7 if self.demo else None)
        self.pista = gerar_pista(COMPRIMENTO_PISTA)
        self.jogador = Corredor(
            nome="Você", z=0.0, x=0.0, velocidade=0.0,
            velocidade_base=46.0, energia=100.0, eh_jogador=True,
            cor_corpo=(255, 250, 210),
        )
        self.rivais = criar_rivais(TOTAL_CORREDORES - 1)
        self.globulos = gerar_globulos(COMPRIMENTO_PISTA)
        self.particulas: List[Particula] = []
        self.estado = "contagem"
        self.contagem = 3.6
        self.tempo = 0.0
        self.fov = FOV_BASE
        self.menu_opcao = 0
        self.mensagem_final = ""
        self.posicao_final = 0
        self.demo_timer = 0.0
        self.demo_prints_feitos: set = set()
        self.pedir_print: List[str] = []  # nomes a salvar APÓS desenhar
        self._centro_proximo = LARGURA / 2.0
        # Cache de projeção por frame
        self._proj: List[dict] = []

    def todos(self) -> List[Corredor]:
        return [self.jogador] + self.rivais

    def ranking(self) -> int:
        ordenados = sorted(self.todos(), key=lambda c: c.z, reverse=True)
        for i, c in enumerate(ordenados):
            if c.eh_jogador:
                return i + 1
        return TOTAL_CORREDORES

    def progresso(self) -> float:
        return clamp(self.jogador.z / META_Z, 0.0, 1.0)

    # ----- update -----
    def atualizar(self, dt: float) -> None:
        if self.estado == "pausa":
            return

        if self.estado in ("vitoria", "derrota"):
            self.tempo += dt
            if self.demo:
                self.demo_timer += dt
                self._demo_agendar_prints()
            return

        if self.estado == "contagem":
            self.contagem -= dt
            self.tempo += dt
            self.jogador.fase_cauda += dt * 8
            for r in self.rivais:
                r.fase_cauda += dt * 8
            if self.demo:
                self.demo_timer += dt
                self._demo_agendar_prints()
            if self.contagem <= 0:
                self.estado = "correndo"
            return

        self.tempo += dt
        self._atualizar_jogador(dt)
        self._atualizar_rivais(dt)
        self._atualizar_globulos(dt)
        self._atualizar_particulas(dt)
        self._gerar_particulas(dt)

        alvo_fov = FOV_TURBO if self.jogador.turbo else FOV_BASE
        self.fov = lerp(self.fov, alvo_fov, min(1.0, dt * 5))

        if self.jogador.z >= META_Z and not self.jogador.terminou:
            self.jogador.terminou = True
            self.jogador.tempo_chegada = self.tempo
            self.jogador.z = META_Z
            pos = self.ranking()
            self.posicao_final = pos
            if pos == 1:
                self.estado = "vitoria"
                self.mensagem_final = "Parabéns, você existe!"
            else:
                self.estado = "derrota"
                self.mensagem_final = f"Você chegou em {pos}º... tente outra vida"

        if self.demo:
            self.demo_timer += dt
            self._demo_agendar_prints()
            # Acelera demo depois da largada para chegar à meta
            if self.estado == "correndo" and self.demo_timer > 6.5:
                # Só acelera o demo DEPOIS do print do meio
                self.jogador.z += 240 * dt
                self.jogador.velocidade = max(self.jogador.velocidade, 95)

    def _atualizar_jogador(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        j = self.jogador

        if self.demo:
            j.x = math.sin(self.tempo * 1.4) * 0.4
            j.vx = math.cos(self.tempo * 1.4) * 0.4
            j.turbo = (int(self.tempo * 2) % 5) < 2 and j.energia > 8
        else:
            move = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                move -= 1.0
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                move += 1.0
            j.vx = move * 1.9
            j.x += j.vx * dt
            j.turbo = keys[pygame.K_SPACE] and j.energia > 0

        j.x = clamp(j.x, -0.92, 0.92)

        if j.turbo and j.energia > 0:
            j.energia = max(0.0, j.energia - 30 * dt)
            if j.energia <= 0:
                j.turbo = False
        else:
            j.energia = min(100.0, j.energia + 11 * dt)

        alvo = j.velocidade_base * (1.7 if j.turbo else 1.0)
        if j.empurrado > 0:
            alvo *= 0.42
            j.empurrado -= dt
        if abs(j.x) > 0.88:
            alvo *= 0.85
        j.velocidade = lerp(j.velocidade, alvo, min(1.0, dt * 3.2))
        j.z += j.velocidade * dt
        j.fase_cauda += dt * (10 + j.velocidade * 0.15)

    def _atualizar_rivais(self, dt: float) -> None:
        for r in self.rivais:
            if r.terminou:
                continue
            r.timer_ia -= dt
            if r.timer_ia <= 0:
                r.alvo_x = random.uniform(-0.7, 0.7)
                r.timer_ia = random.uniform(0.7, 2.4)
                r.turbo = random.random() < 0.22 and r.energia > 25

            r.x = lerp(r.x, r.alvo_x, min(1.0, dt * 1.6))
            r.x += math.sin(self.tempo * 2.1 + r.fase_cauda) * 0.1 * dt
            r.x = clamp(r.x, -0.9, 0.9)

            if r.turbo and r.energia > 0:
                r.energia = max(0.0, r.energia - 20 * dt)
            else:
                r.turbo = False
                r.energia = min(100.0, r.energia + 7 * dt)

            alvo = r.velocidade_base * (1.5 if r.turbo else 1.0)
            if r.empurrado > 0:
                alvo *= 0.5
                r.empurrado -= dt
            alvo *= 0.9 + 0.1 * math.sin(self.tempo * 1.6 + r.fase_cauda)
            r.velocidade = lerp(r.velocidade, alvo, min(1.0, dt * 2.4))
            r.z += r.velocidade * dt
            r.fase_cauda += dt * (9 + r.velocidade * 0.12)

            if r.z >= META_Z:
                r.terminou = True
                r.tempo_chegada = self.tempo
                r.z = META_Z

    def _atualizar_globulos(self, dt: float) -> None:
        for g in self.globulos:
            g.fase += dt * 3
            for c in self.todos():
                if c.terminou:
                    continue
                if abs(g.z - c.z) < 16 and abs(g.x - c.x) < (g.raio + 0.11):
                    c.empurrado = max(c.empurrado, 0.5 if c.eh_jogador else 0.35)
                    emp = 0.25 if c.x >= g.x else -0.25
                    c.x = clamp(c.x + emp, -0.9, 0.9)
                    if not c.eh_jogador:
                        c.alvo_x = c.x

    def _gerar_particulas(self, dt: float) -> None:
        taxa = 10 + self.jogador.velocidade * 0.3
        if self.jogador.turbo:
            taxa *= 1.9
        n = int(taxa * dt)
        if random.random() < (taxa * dt) % 1:
            n += 1
        for _ in range(n):
            self.particulas.append(Particula(
                x=random.uniform(40, LARGURA - 40),
                y=random.uniform(HORIZONTE_Y + 30, ALTURA - 60),
                vy=180 + self.jogador.velocidade * 5,
                vida=random.uniform(0.12, 0.4),
                comprimento=random.uniform(10, 36),
            ))

    def _atualizar_particulas(self, dt: float) -> None:
        vivas = []
        for p in self.particulas:
            p.y += p.vy * dt
            p.vida -= dt
            if p.vida > 0 and p.y < ALTURA + 30:
                vivas.append(p)
        self.particulas = vivas[:140]

    # ----- demo prints (agenda; salva depois do flip) -----
    def _demo_agendar_prints(self) -> None:
        if "largada" not in self.demo_prints_feitos and self.estado == "contagem" and self.contagem < 2.9:
            self.pedir_print.append("largada.png")
            self.demo_prints_feitos.add("largada")
        if "meio" not in self.demo_prints_feitos and self.estado == "correndo" and 0.10 < self.progresso() < 0.40:
            # Empurra alguns rivais para a zona visível (ultrapassagem no print)
            if "meio_prep" not in self.demo_prints_feitos:
                for i, r in enumerate(self.rivais[:12]):
                    r.z = self.jogador.z + 35 + i * 28
                    r.x = -0.55 + (i % 5) * 0.25
                self.demo_prints_feitos.add("meio_prep")
            else:
                self.pedir_print.append("meio.png")
                self.demo_prints_feitos.add("meio")
        if "chegada" not in self.demo_prints_feitos and self.estado in ("vitoria", "derrota"):
            self.pedir_print.append("chegada.png")
            self.demo_prints_feitos.add("chegada")

    def _salvar_prints_pendentes(self) -> None:
        if not self.pedir_print:
            return
        pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prints")
        os.makedirs(pasta, exist_ok=True)
        for nome in self.pedir_print:
            caminho = os.path.join(pasta, nome)
            pygame.image.save(self.tela, caminho)
            print(f"[demo] screenshot salvo: {caminho}")
        self.pedir_print.clear()

    # ----- render pista -----
    def _montar_projecao(self) -> None:
        """Pré-calcula centro/y/largura de cada segmento visível (OutRun)."""
        cam_z = self.jogador.z
        base_i = int(cam_z / SEG_LEN)
        base_i = clamp(base_i, 0, len(self.pista) - 2)

        proj = []
        curva_acum = 0.0
        x_off = 0.0
        max_n = 90

        for n in range(max_n):
            i = base_i + n
            if i >= len(self.pista) - 1:
                break
            seg = self.pista[i]
            z_rel = seg.z - cam_z + Z_PERTO * 0.5
            if z_rel < 3:
                continue

            curva_acum += seg.curva
            x_off += curva_acum

            y, esc = projetar_yz(z_rel, self.fov)
            # Segmentos perto demais ficam abaixo da tela: pula, NÃO para
            # (senão a pista inteira some — os longe vêm depois).
            if y > ALTURA + 120:
                continue
            if y < HORIZONTE_Y - 30:
                break  # já passou do horizonte

            # Centro deslocado pela curva e pela posição do jogador
            centro = LARGURA / 2 + x_off * (esc / 90) - self.jogador.x * esc * 0.55
            metade = esc * 0.5 * seg.largura
            # Limita metade para não explodir nas laterais
            metade = min(metade, LARGURA * 0.75)
            proj.append({
                "y": y, "centro": centro, "metade": metade,
                "esc": esc, "seg": seg, "z_rel": z_rel, "i": i,
            })

        self._proj = proj
        if proj:
            # Segmento mais próximo (menor z_rel = índice 0 da lista filtrada)
            self._centro_proximo = proj[0]["centro"]

    def desenhar_pista(self) -> None:
        # Fundo / teto do túnel (gradiente)
        self.tela.fill(ROSA_FUNDO)
        for i in range(HORIZONTE_Y + 8):
            t = i / (HORIZONTE_Y + 8)
            c = cor_lerp((55, 15, 35), ROSA_ESCURO, t)
            pygame.draw.line(self.tela, c, (0, i), (LARGURA, i))

        self._montar_projecao()
        proj = self._proj
        if len(proj) < 2:
            return

        # Desenha do longe → perto.
        # proj[0] = mais perto (y maior); proj[-1] = horizonte (y menor).
        for k in range(len(proj) - 1, 0, -1):
            a = proj[k]       # mais longe
            b = proj[k - 1]   # mais perto
            y1, y2 = a["y"], b["y"]
            if y2 <= y1 + 0.2:
                continue
            # Clip leve: mantém faixa visível mesmo se um lado passa da tela
            y1c = min(y1, ALTURA + 2)
            y2c = min(y2, ALTURA + 2)

            faixa = int(a["seg"].z / SEG_LEN) % 2
            cor_chao = ROSA_CLARO if faixa == 0 else ROSA_MEDIO
            cor_parede = ROSA_PAREDE_A if faixa == 0 else ROSA_PAREDE_B
            cor_teto = ROSA_TETO_A if faixa == 0 else ROSA_TETO_B
            cor_zebra = ZEBRA_A if faixa == 0 else ZEBRA_B

            c1, m1 = a["centro"], a["metade"]
            c2, m2 = b["centro"], b["metade"]

            # Chão
            pygame.draw.polygon(self.tela, cor_chao, [
                (c1 - m1, y1c), (c1 + m1, y1c),
                (c2 + m2, y2c), (c2 - m2, y2c),
            ])

            # Altura das paredes / teto (proporcional, com teto)
            h1 = min(a["esc"] * 0.55, y1c - 20)
            h2 = min(b["esc"] * 0.55, y2c - 20)
            h1 = max(8, h1)
            h2 = max(8, h2)
            y1, y2 = y1c, y2c

            # Parede esquerda
            pygame.draw.polygon(self.tela, cor_parede, [
                (c1 - m1, y1), (c1 - m1 - h1 * 0.25, y1 - h1),
                (c2 - m2 - h2 * 0.25, y2 - h2), (c2 - m2, y2),
            ])
            # Parede direita
            pygame.draw.polygon(self.tela, cor_parede, [
                (c1 + m1, y1), (c1 + m1 + h1 * 0.25, y1 - h1),
                (c2 + m2 + h2 * 0.25, y2 - h2), (c2 + m2, y2),
            ])
            # Teto (faixa superior do túnel)
            pygame.draw.polygon(self.tela, cor_teto, [
                (c1 - m1 - h1 * 0.25, y1 - h1),
                (c1 + m1 + h1 * 0.25, y1 - h1),
                (c2 + m2 + h2 * 0.25, y2 - h2),
                (c2 - m2 - h2 * 0.25, y2 - h2),
            ])

            # Zebras laterais
            lw = max(1, int(a["esc"] * 0.04))
            pygame.draw.line(self.tela, cor_zebra, (c1 - m1, y1), (c2 - m2, y2), lw)
            pygame.draw.line(self.tela, cor_zebra, (c1 + m1, y1), (c2 + m2, y2), lw)

            # Tracejado central
            if faixa == 0:
                pygame.draw.line(
                    self.tela, (255, 250, 250),
                    (c1, y1), (c2, y2), max(1, lw // 2 + 1),
                )

        # Estende o chão do segmento mais próximo até a base da tela
        if proj:
            p0 = proj[0]
            y0 = min(p0["y"], ALTURA - 1)
            if y0 < ALTURA - 2:
                c0, m0 = p0["centro"], p0["metade"]
                # Largura na base: um pouco maior (perspectiva)
                m_base = min(m0 * 1.35, LARGURA * 0.78)
                faixa = int(p0["seg"].z / SEG_LEN) % 2
                cor = ROSA_CLARO if faixa == 0 else ROSA_MEDIO
                pygame.draw.polygon(self.tela, cor, [
                    (c0 - m0, y0), (c0 + m0, y0),
                    (LARGURA / 2 + m_base - self.jogador.x * 40, ALTURA),
                    (LARGURA / 2 - m_base - self.jogador.x * 40, ALTURA),
                ])
                # Continuação das zebras
                pygame.draw.line(self.tela, ZEBRA_A,
                                 (c0 - m0, y0),
                                 (LARGURA / 2 - m_base - self.jogador.x * 40, ALTURA), 3)
                pygame.draw.line(self.tela, ZEBRA_A,
                                 (c0 + m0, y0),
                                 (LARGURA / 2 + m_base - self.jogador.x * 40, ALTURA), 3)

        self._desenhar_meta()

    def _desenhar_meta(self) -> None:
        z_rel = META_Z - self.jogador.z + Z_PERTO * 0.5
        if z_rel < 3:
            return

        # Óvulo no horizonte quando ainda longe
        if z_rel > 1100:
            t = clamp(1.0 - (z_rel - 1100) / 2000, 0, 1)
            if t > 0:
                desenhar_ovulo(self.tela, LARGURA / 2, HORIZONTE_Y - 8, 0.35 + t * 0.5)
            return

        y, esc = projetar_yz(z_rel, self.fov)
        if y > ALTURA + 40 or y < HORIZONTE_Y - 20:
            return

        centro = LARGURA / 2 - self.jogador.x * esc * 0.55
        metade = esc * 0.5

        # Faixa de chegada quadriculada
        n_quad = 14
        qw = (metade * 2) / n_quad
        qh = max(5, esc * 0.08)
        for i in range(n_quad):
            cor = PRETO if i % 2 == 0 else BRANCO
            x0 = centro - metade + i * qw
            pygame.draw.rect(
                self.tela, cor,
                pygame.Rect(int(x0), int(y - qh), max(1, int(qw) + 1), int(qh)),
            )
            cor2 = BRANCO if i % 2 == 0 else PRETO
            pygame.draw.rect(
                self.tela, cor2,
                pygame.Rect(int(x0), int(y - 2 * qh), max(1, int(qw) + 1), int(qh)),
            )

        ov_esc = clamp(esc / 140, 0.4, 5.5)
        desenhar_ovulo(self.tela, centro, y - qh * 2 - 18 * ov_esc, ov_esc)

    def _x_na_pista(self, x_mundo: float, z_rel: float) -> Tuple[float, float, float]:
        """Converte (x_mundo, z_rel) → (sx, sy, escala_sprite) usando a projeção atual."""
        y, esc = projetar_yz(max(z_rel, 3), self.fov)
        # Interpola centro a partir dos segmentos projetados
        centro = LARGURA / 2
        if self._proj:
            # Acha o segmento mais próximo em z_rel
            melhor = self._proj[0]
            for p in self._proj:
                if abs(p["z_rel"] - z_rel) < abs(melhor["z_rel"] - z_rel):
                    melhor = p
            centro = melhor["centro"]
            y = melhor["y"]
            esc = melhor["esc"]
        sx = centro + (x_mundo - self.jogador.x) * esc * 0.55
        return sx, y, esc

    def desenhar_globulos_e_rivais(self) -> None:
        cam_z = self.jogador.z
        itens = []
        for g in self.globulos:
            z_rel = g.z - cam_z + Z_PERTO * 0.5
            if 6 < z_rel < 1000:
                itens.append(("g", z_rel, g))
        for r in self.rivais:
            z_rel = r.z - cam_z + Z_PERTO * 0.5
            if -30 < z_rel < 1000:
                itens.append(("r", z_rel, r))
        itens.sort(key=lambda t: -t[1])

        for tipo, z_rel, obj in itens:
            if tipo == "g":
                g: Globulo = obj
                sx, sy, esc = self._x_na_pista(g.x, z_rel)
                desenhar_globulo(self.tela, sx, sy, g.raio * esc * 0.7, g.fase)
            else:
                r: Corredor = obj
                if z_rel < 6:
                    # Ultrapassado: grande, perto da base
                    sx = LARGURA / 2 + (r.x - self.jogador.x) * 140
                    sy = ALTURA - 95 + max(0, -z_rel) * 1.2
                    esc_s = clamp(3.0 + (-z_rel) * 0.04, 2.5, 4.2)
                else:
                    sx, sy, esc = self._x_na_pista(r.x, z_rel)
                    esc_s = clamp(esc / 55, 0.35, 4.8)
                desenhar_esperma(self.tela, sx, sy, esc_s, r.cor_corpo, r.fase_cauda)

    def desenhar_jogador(self) -> None:
        cx = LARGURA / 2 + self.jogador.x * 100
        cy = ALTURA - 105
        esc = 3.4
        if self.jogador.turbo:
            for i in range(3):
                desenhar_esperma(
                    self.tela, cx, cy + 10 + i * 12, esc * 0.65,
                    (255, 255, 170), self.jogador.fase_cauda - i * 0.8,
                )
        desenhar_esperma(
            self.tela, cx, cy, esc, self.jogador.cor_corpo,
            self.jogador.fase_cauda, destaque=True,
            inclinacao=self.jogador.vx * 0.15,
        )

    def desenhar_particulas(self) -> None:
        for p in self.particulas:
            t = clamp(p.vida / 0.4, 0, 1)
            cor = cor_lerp(ROSA_MEDIO, BRANCO, t)
            pygame.draw.line(self.tela, cor, (p.x, p.y), (p.x, p.y + p.comprimento), 2)

    def desenhar_hud(self) -> None:
        pos = self.ranking()
        txt = f"{pos}º / {TOTAL_CORREDORES}"
        self.tela.blit(self.fonte_g.render(txt, True, PRETO), (22, 18))
        self.tela.blit(self.fonte_g.render(txt, True, AMARELO), (20, 16))

        mms = int(self.jogador.velocidade * 2.8)
        self.tela.blit(self.fonte_m.render(f"{mms} mm/s", True, CIANO), (20, 70))

        bx, by, bw, bh = LARGURA - 220, 24, 180, 22
        pygame.draw.rect(self.tela, CINZA_HUD, (bx - 2, by - 2, bw + 4, bh + 4), border_radius=6)
        pygame.draw.rect(self.tela, (60, 30, 50), (bx, by, bw, bh), border_radius=5)
        ew = int(bw * (self.jogador.energia / 100.0))
        cor_e = DOURADO if self.jogador.turbo else (VERDE if self.jogador.energia > 30 else VERMELHO)
        pygame.draw.rect(self.tela, cor_e, (bx, by, ew, bh), border_radius=5)
        self.tela.blit(self.fonte_p.render("ENERGIA / TURBO", True, BRANCO), (bx, by - 18))

        px, py, pw, ph = LARGURA // 2 - 160, 12, 320, 14
        pygame.draw.rect(self.tela, CINZA_HUD, (px - 2, py - 2, pw + 4, ph + 4), border_radius=4)
        pygame.draw.rect(self.tela, (50, 25, 40), (px, py, pw, ph), border_radius=3)
        pygame.draw.rect(self.tela, (255, 160, 180), (px, py, int(pw * self.progresso()), ph), border_radius=3)
        pygame.draw.circle(self.tela, DOURADO, (px + pw + 12, py + ph // 2), 8)
        pygame.draw.circle(self.tela, (255, 140, 120), (px + pw + 12, py + ph // 2), 4)

        # Minimapa
        mx, my, mw, mh = LARGURA - 36, 70, 12, 200
        pygame.draw.rect(self.tela, (50, 25, 40), (mx, my, mw, mh), border_radius=3)
        for r in self.rivais:
            ry = my + mh - int(clamp(r.z / META_Z, 0, 1) * mh)
            pygame.draw.circle(self.tela, (200, 180, 160), (mx + mw // 2, ry), 2)
        jy = my + mh - int(self.progresso() * mh)
        pygame.draw.circle(self.tela, AMARELO, (mx + mw // 2, jy), 4)
        pygame.draw.circle(self.tela, DOURADO, (mx + mw // 2, my), 5)

    def desenhar_contagem(self) -> None:
        if self.estado != "contagem":
            return
        if self.contagem <= 0.45:
            texto, cor = "GO!", VERDE
        else:
            texto, cor = str(max(1, math.ceil(self.contagem))), AMARELO
        sombra = self.fonte_g.render(texto, True, PRETO)
        img = self.fonte_g.render(texto, True, cor)
        rect = img.get_rect(center=(LARGURA // 2, ALTURA // 2 - 30))
        self.tela.blit(sombra, rect.move(3, 3))
        self.tela.blit(img, rect)
        dica = self.fonte.render(
            "Setas/WASD move · Espaço turbo · P pausa · R reinicia", True, BRANCO
        )
        self.tela.blit(dica, dica.get_rect(center=(LARGURA // 2, ALTURA - 36)))

    def desenhar_pausa(self) -> None:
        if self.estado != "pausa":
            return
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((30, 10, 25, 185))
        self.tela.blit(overlay, (0, 0))
        tit = self.fonte_g.render("PAUSA", True, AMARELO)
        self.tela.blit(tit, tit.get_rect(center=(LARGURA // 2, 140)))
        opcoes = [
            "Resume",
            f"Sound {'on' if self.som_ligado else 'off'}",
            "Restart from the beginning",
        ]
        for i, op in enumerate(opcoes):
            cor = DOURADO if i == self.menu_opcao else BRANCO
            pref = "> " if i == self.menu_opcao else "  "
            img = self.fonte_m.render(pref + op, True, cor)
            self.tela.blit(img, img.get_rect(center=(LARGURA // 2, 250 + i * 50)))
        dica = self.fonte_p.render("↑↓ escolhe · Enter confirma · P volta", True, ROSA_CLARO)
        self.tela.blit(dica, dica.get_rect(center=(LARGURA // 2, 450)))

    def desenhar_final(self) -> None:
        if self.estado not in ("vitoria", "derrota"):
            return
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((20, 5, 20, 170))
        self.tela.blit(overlay, (0, 0))
        cor = VERDE if self.estado == "vitoria" else AMARELO
        img = self.fonte_g.render(self.mensagem_final, True, cor)
        if img.get_width() > LARGURA - 40:
            img = self.fonte_m.render(self.mensagem_final, True, cor)
        self.tela.blit(img, img.get_rect(center=(LARGURA // 2, ALTURA // 2 - 30)))
        sub = self.fonte.render(
            f"Posição final: {self.posicao_final}º / {TOTAL_CORREDORES}  ·  R reinicia",
            True, BRANCO,
        )
        self.tela.blit(sub, sub.get_rect(center=(LARGURA // 2, ALTURA // 2 + 40)))

    def desenhar(self) -> None:
        self.desenhar_pista()
        self.desenhar_globulos_e_rivais()
        self.desenhar_particulas()
        self.desenhar_jogador()
        self.desenhar_hud()
        self.desenhar_contagem()
        self.desenhar_pausa()
        self.desenhar_final()
        pygame.display.flip()
        self._salvar_prints_pendentes()

    def tratar_eventos(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.estado == "pausa":
                        self.estado = "correndo"
                    else:
                        return False
                if ev.key == pygame.K_r:
                    self.reiniciar()
                if ev.key == pygame.K_p:
                    if self.estado == "correndo":
                        self.estado = "pausa"
                        self.menu_opcao = 0
                    elif self.estado == "pausa":
                        self.estado = "correndo"
                if self.estado == "pausa":
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        self.menu_opcao = (self.menu_opcao - 1) % 3
                    if ev.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_opcao = (self.menu_opcao + 1) % 3
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.menu_opcao == 0:
                            self.estado = "correndo"
                        elif self.menu_opcao == 1:
                            self.som_ligado = not self.som_ligado
                        else:
                            self.reiniciar()
        return True

    def rodar(self) -> None:
        rodando = True
        while rodando:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            rodando = self.tratar_eventos()
            self.atualizar(dt)
            self.desenhar()
            if self.demo and self.demo_timer > 40.0:
                for nome, key in (("largada.png", "largada"),
                                  ("meio.png", "meio"),
                                  ("chegada.png", "chegada")):
                    if key not in self.demo_prints_feitos:
                        self.pedir_print.append(nome)
                        self.demo_prints_feitos.add(key)
                self.desenhar()
                rodando = False
            if self.demo and "chegada" in self.demo_prints_feitos:
                if self.estado in ("vitoria", "derrota") and self.demo_timer > 0:
                    # Um frame extra já gravou; encerra logo
                    if self.tempo > self.jogador.tempo_chegada + 0.8:
                        rodando = False
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Corrida de Espermatozoides (Pygame)")
    parser.add_argument("--demo", action="store_true",
                        help="Autoplay + salva screenshots em prints/")
    args = parser.parse_args()
    if args.demo and not os.environ.get("DISPLAY") and not os.environ.get("SDL_VIDEODRIVER"):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    Jogo(demo=args.demo).rodar()


if __name__ == "__main__":
    main()

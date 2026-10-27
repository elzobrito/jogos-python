#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sudoku — jogo didático em Pygame
================================
Grade 9×9 clássica, bordas 3×3 grossas, gerador com solução única,
níveis de dificuldade, destaque de linha/coluna/bloco e conflitos.

Controles:
  Clique / setas  — selecionar célula
  1–9            — preencher
  0 / Backspace / Delete — apagar
  N              — novo puzzle (mesma dificuldade)
  1/2/3 em modo menu — fácil / médio / difícil (ver teclas D)
  D              — ciclar dificuldade e gerar novo
  H              — dica (preenche uma célula)
  R              — reiniciar puzzle atual (mantém givens)
  ESC            — sair

Rodar:
  python3 main.py
  python3 main.py --demo   # auto-solve animado + prints/
"""

from __future__ import annotations

import argparse
import copy
import os
import random
from typing import List, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# Constantes visuais
# ---------------------------------------------------------------------------
LARGURA = 700
ALTURA = 780
FPS = 30
MARGEM = 40
TAM = 64
GRADE_X = MARGEM
GRADE_Y = MARGEM

BRANCO = (255, 255, 255)
PRETO = (20, 20, 20)
CINZA = (200, 200, 200)
AZUL_ESC = (25, 90, 180)       # célula selecionada
AZUL_CLA = (200, 220, 245)     # linha/coluna/bloco
VERMELHO = (220, 50, 50)       # conflito
VERDE = (40, 160, 80)
FUNDO = (245, 245, 248)
GIVEN = (10, 10, 10)
USER = (30, 80, 160)

DIFF_FUROS = {"facil": 35, "medio": 45, "dificil": 55}

Grid = List[List[int]]  # 0 = vazio


# ---------------------------------------------------------------------------
# Solver / gerador (backtracking)
# ---------------------------------------------------------------------------
def encontra_vazio(g: Grid) -> Optional[Tuple[int, int]]:
    for r in range(9):
        for c in range(9):
            if g[r][c] == 0:
                return r, c
    return None


def valido(g: Grid, r: int, c: int, n: int) -> bool:
    if any(g[r][i] == n for i in range(9) if i != c):
        return False
    if any(g[i][c] == n for i in range(9) if i != r):
        return False
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if (i, j) != (r, c) and g[i][j] == n:
                return False
    return True


def resolver(g: Grid) -> bool:
    vazio = encontra_vazio(g)
    if not vazio:
        return True
    r, c = vazio
    nums = list(range(1, 10))
    random.shuffle(nums)
    for n in nums:
        if valido(g, r, c, n):
            g[r][c] = n
            if resolver(g):
                return True
            g[r][c] = 0
    return False


def contar_solucoes(g: Grid, limite: int = 2) -> int:
    """Conta soluções até `limite` (para testar unicidade)."""
    vazio = encontra_vazio(g)
    if not vazio:
        return 1
    r, c = vazio
    total = 0
    for n in range(1, 10):
        if valido(g, r, c, n):
            g[r][c] = n
            total += contar_solucoes(g, limite)
            g[r][c] = 0
            if total >= limite:
                return total
    return total


def gerar_completo() -> Grid:
    g = [[0] * 9 for _ in range(9)]
    # preenche diagonal dos blocos 3x3 (independentes) para acelerar
    for k in range(0, 9, 3):
        nums = list(range(1, 10))
        random.shuffle(nums)
        i = 0
        for r in range(k, k + 3):
            for c in range(k, k + 3):
                g[r][c] = nums[i]
                i += 1
    resolver(g)
    return g


def gerar_puzzle(dificuldade: str = "medio") -> Tuple[Grid, Grid]:
    """Retorna (puzzle, solucao). Puzzle tem solução única."""
    solucao = gerar_completo()
    puzzle = copy.deepcopy(solucao)
    furos = DIFF_FUROS.get(dificuldade, 45)
    casas = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(casas)
    removidos = 0
    for r, c in casas:
        if removidos >= furos:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        teste = copy.deepcopy(puzzle)
        if contar_solucoes(teste, 2) != 1:
            puzzle[r][c] = backup
        else:
            removidos += 1
    return puzzle, solucao


def conflitos(g: Grid, r: int, c: int) -> bool:
    n = g[r][c]
    if n == 0:
        return False
    return not valido(g, r, c, n)


def completo_e_valido(g: Grid) -> bool:
    for r in range(9):
        for c in range(9):
            if g[r][c] == 0 or not valido(g, r, c, g[r][c]):
                return False
    return True


# ---------------------------------------------------------------------------
# Jogo
# ---------------------------------------------------------------------------
class Jogo:
    def __init__(self, demo: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("Sudoku — didático")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.fonte_u = pygame.font.SysFont("dejavusans", 36)
        self.fonte_m = pygame.font.SysFont("dejavusans", 22)
        self.fonte_p = pygame.font.SysFont("dejavusans", 16)
        self.demo = demo
        self.dificuldade = "medio"
        self.novo_puzzle()
        self.pedir_print: List[str] = []
        self.prints_feitos: set = set()
        self.demo_timer = 0.0
        self.demo_passos: List[Tuple[int, int, int]] = []
        self.demo_idx = 0
        self.demo_espera = 0.0
        if demo:
            self._preparar_demo()

    def novo_puzzle(self) -> None:
        self.puzzle, self.solucao = gerar_puzzle(self.dificuldade)
        self.grade = copy.deepcopy(self.puzzle)
        self.sel = (4, 4)
        self.vitoria = False
        self.msg = f"Dificuldade: {self.dificuldade}  ·  D troca  ·  N novo"

    def _preparar_demo(self) -> None:
        # lista de células a preencher na ordem de varredura
        self.demo_passos = []
        for r in range(9):
            for c in range(9):
                if self.puzzle[r][c] == 0:
                    self.demo_passos.append((r, c, self.solucao[r][c]))
        self.demo_idx = 0

    def celula_em(self, mx: int, my: int) -> Optional[Tuple[int, int]]:
        if not (GRADE_X <= mx < GRADE_X + 9 * TAM and GRADE_Y <= my < GRADE_Y + 9 * TAM):
            return None
        return (my - GRADE_Y) // TAM, (mx - GRADE_X) // TAM

    def setar(self, n: int) -> None:
        if self.vitoria:
            return
        r, c = self.sel
        if self.puzzle[r][c] != 0:
            return  # given
        self.grade[r][c] = n
        if completo_e_valido(self.grade):
            self.vitoria = True
            self.msg = "Parabéns! Sudoku completo!"

    def dica(self) -> None:
        vazias = [(r, c) for r in range(9) for c in range(9)
                  if self.grade[r][c] == 0]
        if not vazias:
            return
        r, c = random.choice(vazias)
        self.sel = (r, c)
        self.grade[r][c] = self.solucao[r][c]
        if completo_e_valido(self.grade):
            self.vitoria = True
            self.msg = "Parabéns! Sudoku completo!"

    def desenhar(self) -> None:
        self.tela.fill(FUNDO)
        sr, sc = self.sel
        # fundo relacionados
        for r in range(9):
            for c in range(9):
                x = GRADE_X + c * TAM
                y = GRADE_Y + r * TAM
                cor = BRANCO
                if r == sr or c == sc or (r // 3 == sr // 3 and c // 3 == sc // 3):
                    cor = AZUL_CLA
                if (r, c) == self.sel:
                    cor = AZUL_ESC
                pygame.draw.rect(self.tela, cor, (x, y, TAM, TAM))
        # números
        for r in range(9):
            for c in range(9):
                n = self.grade[r][c]
                if n == 0:
                    continue
                x = GRADE_X + c * TAM + TAM // 2
                y = GRADE_Y + r * TAM + TAM // 2
                given = self.puzzle[r][c] != 0
                conf = conflitos(self.grade, r, c)
                if conf:
                    cor = VERMELHO
                elif given:
                    cor = GIVEN
                else:
                    cor = USER if (r, c) != self.sel else BRANCO
                if (r, c) == self.sel and not conf:
                    cor = BRANCO if not given else (230, 230, 255)
                fonte = self.fonte if given else self.fonte_u
                img = fonte.render(str(n), True, cor)
                self.tela.blit(img, img.get_rect(center=(x, y)))
        # grades
        for i in range(10):
            esp = 3 if i % 3 == 0 else 1
            # vertical
            pygame.draw.line(self.tela, PRETO,
                             (GRADE_X + i * TAM, GRADE_Y),
                             (GRADE_X + i * TAM, GRADE_Y + 9 * TAM), esp)
            # horizontal
            pygame.draw.line(self.tela, PRETO,
                             (GRADE_X, GRADE_Y + i * TAM),
                             (GRADE_X + 9 * TAM, GRADE_Y + i * TAM), esp)
        # HUD
        cor_msg = VERDE if self.vitoria else PRETO
        self.tela.blit(self.fonte_m.render(self.msg, True, cor_msg), (MARGEM, ALTURA - 90))
        dica = "Setas/clique · 1-9 · 0 apaga · H dica · D dificuldade · N novo · R reset · ESC"
        self.tela.blit(self.fonte_p.render(dica, True, (100, 100, 100)), (MARGEM, ALTURA - 55))
        if self.vitoria:
            overlay = pygame.Surface((LARGURA, 80), pygame.SRCALPHA)
            overlay.fill((40, 160, 80, 200))
            self.tela.blit(overlay, (0, ALTURA // 2 - 40))
            t = self.fonte.render("VOCÊ RESOLVEU!", True, BRANCO)
            self.tela.blit(t, t.get_rect(center=(LARGURA // 2, ALTURA // 2)))
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

    def _demo_tick(self, dt: float) -> None:
        self.demo_timer += dt
        if "inicio.png" not in self.prints_feitos and self.demo_timer > 0.3:
            self.pedir_print.append("inicio.png")
            self.prints_feitos.add("inicio.png")
        self.demo_espera += dt
        if self.demo_idx < len(self.demo_passos) and self.demo_espera > 0.08:
            self.demo_espera = 0.0
            r, c, n = self.demo_passos[self.demo_idx]
            self.sel = (r, c)
            self.grade[r][c] = n
            self.demo_idx += 1
            if self.demo_idx == max(1, len(self.demo_passos) // 2):
                if "meio.png" not in self.prints_feitos:
                    self.pedir_print.append("meio.png")
                    self.prints_feitos.add("meio.png")
            if self.demo_idx >= len(self.demo_passos):
                self.vitoria = True
                self.msg = "Parabéns! Sudoku completo!"
                if "fim.png" not in self.prints_feitos:
                    self.pedir_print.append("fim.png")
                    self.prints_feitos.add("fim.png")

    def tratar(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return False
                if self.demo:
                    continue
                if ev.key == pygame.K_n:
                    self.novo_puzzle()
                if ev.key == pygame.K_d:
                    ordem = ["facil", "medio", "dificil"]
                    self.dificuldade = ordem[(ordem.index(self.dificuldade) + 1) % 3]
                    self.novo_puzzle()
                if ev.key == pygame.K_r:
                    self.grade = copy.deepcopy(self.puzzle)
                    self.vitoria = False
                    self.msg = f"Dificuldade: {self.dificuldade}"
                if ev.key == pygame.K_h:
                    self.dica()
                if ev.key in (pygame.K_0, pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_KP0):
                    self.setar(0)
                nums = {
                    pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4, pygame.K_5: 5,
                    pygame.K_6: 6, pygame.K_7: 7, pygame.K_8: 8, pygame.K_9: 9,
                    pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3, pygame.K_KP4: 4, pygame.K_KP5: 5,
                    pygame.K_KP6: 6, pygame.K_KP7: 7, pygame.K_KP8: 8, pygame.K_KP9: 9,
                }
                if ev.key in nums:
                    self.setar(nums[ev.key])
                r, c = self.sel
                if ev.key == pygame.K_UP:
                    self.sel = ((r - 1) % 9, c)
                if ev.key == pygame.K_DOWN:
                    self.sel = ((r + 1) % 9, c)
                if ev.key == pygame.K_LEFT:
                    self.sel = (r, (c - 1) % 9)
                if ev.key == pygame.K_RIGHT:
                    self.sel = (r, (c + 1) % 9)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and not self.demo:
                cel = self.celula_em(*ev.pos)
                if cel:
                    self.sel = cel
        return True

    def rodar(self) -> None:
        rodando = True
        while rodando:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            rodando = self.tratar()
            if self.demo:
                self._demo_tick(dt)
            self.desenhar()
            if self.demo and ("fim.png" in self.prints_feitos) and self.demo_timer > 1.0:
                # um frame extra já gravou
                if self.vitoria:
                    rodando = False
            if self.demo and self.demo_timer > 7.5:
                if "fim.png" not in self.prints_feitos:
                    self.pedir_print.append("fim.png")
                    self.prints_feitos.add("fim.png")
                    self.desenhar()
                rodando = False
        pygame.quit()


def _teste_unicidade() -> None:
    random.seed(42)
    for dif in ("facil", "medio", "dificil"):
        puz, sol = gerar_puzzle(dif)
        assert completo_e_valido(sol), dif
        t = copy.deepcopy(puz)
        n = contar_solucoes(t, 2)
        assert n == 1, f"{dif} soluções={n}"
        # solução bate
        t2 = copy.deepcopy(puz)
        assert resolver(t2) and t2 == sol
        print(f"OK gerador {dif}: solução única")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sudoku didático (Pygame)")
    parser.add_argument("--demo", action="store_true", help="Auto-solve + prints/")
    parser.add_argument("--test", action="store_true", help="Testa gerador (unicidade)")
    args = parser.parse_args()
    if args.test:
        _teste_unicidade()
        return
    if args.demo and not os.environ.get("DISPLAY") and not os.environ.get("SDL_VIDEODRIVER"):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    Jogo(demo=args.demo).rodar()


if __name__ == "__main__":
    main()

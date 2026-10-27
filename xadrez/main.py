#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xadrez — jogo didático em Pygame
================================
Tabuleiro estilo chess.com (creme / verde), rótulos A–H e 1–8,
peças desenhadas com polígonos, clique para selecionar/mover.

Regras: movimento legal, roque, en passant, promoção, xeque,
xeque-mate e afogamento. Modos: 2 jogadores ou vs IA (minimax
profundidade 2). Modo --demo: IA vs IA + screenshots em prints/.

Controles:
  Clique  — selecionar casa / mover
  1       — modo 2 jogadores
  2       — jogar de Brancas vs IA
  3       — jogar de Pretas vs IA
  R       — reiniciar
  ESC     — sair

Rodar:
  python3 main.py
  python3 main.py --demo
  python3 main.py --perft 3   # teste de geração de lances
"""

from __future__ import annotations

import argparse
import copy
import os
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# Constantes visuais (referência chess.com)
# ---------------------------------------------------------------------------
LARGURA = 720
ALTURA = 780
FPS = 30
MARGEM = 40
TAM_CASA = 80
TAB_X = MARGEM
TAB_Y = MARGEM

COR_CLARA = (240, 217, 181)      # creme
COR_ESCURA = (118, 150, 86)      # verde
COR_SEL = (246, 246, 105)        # amarelo seleção
COR_MOV = (106, 135, 77)         # destaque lance legal
COR_ULT = (205, 210, 106)        # último lance
COR_FUNDO = (48, 46, 43)
COR_TEXTO = (235, 235, 235)
COR_ROTULO = (90, 90, 90)
BRANCO_PECA = (245, 245, 245)
PRETO_PECA = (40, 40, 40)
CONTORNO = (20, 20, 20)

# Peças: maiúsculas = brancas, minúsculas = pretas
# Pawn Knight Bishop Rook Queen King
VALOR = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}

# ---------------------------------------------------------------------------
# Motor de xadrez (tabuleiro 8x8, fila 0 = rank 8)
# ---------------------------------------------------------------------------
Pos = Tuple[int, int]  # (fila, coluna) 0..7


@dataclass
class Lance:
    fr: int
    fc: int
    tr: int
    tc: int
    promo: Optional[str] = None  # 'Q','R','B','N' (sempre maiúscula; cor pelo turno)
    especial: Optional[str] = None  # 'castle_k','castle_q','ep'


@dataclass
class Estado:
    tab: List[List[Optional[str]]]
    branco: bool = True
    # direitos de roque: KQkq
    roque: dict = field(default_factory=lambda: {"K": True, "Q": True, "k": True, "q": True})
    ep: Optional[Pos] = None  # casa alvo en passant
    meio_lances: int = 0
    numero: int = 1

    def copia(self) -> "Estado":
        return Estado(
            tab=[row[:] for row in self.tab],
            branco=self.branco,
            roque=dict(self.roque),
            ep=self.ep,
            meio_lances=self.meio_lances,
            numero=self.numero,
        )


def tabuleiro_inicial() -> List[List[Optional[str]]]:
    return [
        list("rnbqkbnr"),
        list("pppppppp"),
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        list("PPPPPPPP"),
        list("RNBQKBNR"),
    ]


def dentro(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def eh_branco(p: Optional[str]) -> bool:
    return p is not None and p.isupper()


def eh_preto(p: Optional[str]) -> bool:
    return p is not None and p.islower()


def mesma_cor(a: Optional[str], b: Optional[str]) -> bool:
    if a is None or b is None:
        return False
    return eh_branco(a) == eh_branco(b)


def achar_rei(est: Estado, branco: bool) -> Pos:
    alvo = "K" if branco else "k"
    for r in range(8):
        for c in range(8):
            if est.tab[r][c] == alvo:
                return r, c
    return -1, -1


def atacada(est: Estado, r: int, c: int, por_branco: bool) -> bool:
    """A casa (r,c) está atacada por peças da cor por_branco?"""
    # peões
    dr = -1 if por_branco else 1
    for dc in (-1, 1):
        rr, cc = r + dr, c + dc
        if dentro(rr, cc):
            p = est.tab[rr][cc]
            if p == ("P" if por_branco else "p"):
                return True
    # cavalos
    for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)):
        rr, cc = r + dr, c + dc
        if dentro(rr, cc):
            p = est.tab[rr][cc]
            if p == ("N" if por_branco else "n"):
                return True
    # rei
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if dentro(rr, cc):
                p = est.tab[rr][cc]
                if p == ("K" if por_branco else "k"):
                    return True
    # torres / damas (linhas)
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        while dentro(rr, cc):
            p = est.tab[rr][cc]
            if p is not None:
                if por_branco and p in ("R", "Q"):
                    return True
                if not por_branco and p in ("r", "q"):
                    return True
                break
            rr += dr
            cc += dc
    # bispos / damas (diagonais)
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rr, cc = r + dr, c + dc
        while dentro(rr, cc):
            p = est.tab[rr][cc]
            if p is not None:
                if por_branco and p in ("B", "Q"):
                    return True
                if not por_branco and p in ("b", "q"):
                    return True
                break
            rr += dr
            cc += dc
    return False


def em_xeque(est: Estado, branco: bool) -> bool:
    rk, ck = achar_rei(est, branco)
    if rk < 0:
        return True
    return atacada(est, rk, ck, not branco)


def _add_deslize(est: Estado, r: int, c: int, dirs, out: List[Lance]) -> None:
    for dr, dc in dirs:
        rr, cc = r + dr, c + dc
        while dentro(rr, cc):
            alvo = est.tab[rr][cc]
            if alvo is None:
                out.append(Lance(r, c, rr, cc))
            else:
                if not mesma_cor(est.tab[r][c], alvo):
                    out.append(Lance(r, c, rr, cc))
                break
            rr += dr
            cc += dc


def geradores_pseudo(est: Estado) -> List[Lance]:
    """Todos os lances pseudo-legais (podem deixar o próprio rei em xeque)."""
    out: List[Lance] = []
    branco = est.branco
    for r in range(8):
        for c in range(8):
            p = est.tab[r][c]
            if p is None:
                continue
            if branco and not eh_branco(p):
                continue
            if not branco and not eh_preto(p):
                continue
            tipo = p.upper()
            if tipo == "P":
                dr = -1 if branco else 1
                # avanço
                rr = r + dr
                if dentro(rr, c) and est.tab[rr][c] is None:
                    if rr == (0 if branco else 7):
                        for promo in ("Q", "R", "B", "N"):
                            out.append(Lance(r, c, rr, c, promo=promo))
                    else:
                        out.append(Lance(r, c, rr, c))
                        # duplo
                        base = 6 if branco else 1
                        rr2 = r + 2 * dr
                        if r == base and est.tab[rr2][c] is None:
                            out.append(Lance(r, c, rr2, c))
                # capturas
                for dc in (-1, 1):
                    rr, cc = r + dr, c + dc
                    if not dentro(rr, cc):
                        continue
                    alvo = est.tab[rr][cc]
                    if alvo is not None and not mesma_cor(p, alvo):
                        if rr == (0 if branco else 7):
                            for promo in ("Q", "R", "B", "N"):
                                out.append(Lance(r, c, rr, cc, promo=promo))
                        else:
                            out.append(Lance(r, c, rr, cc))
                    # en passant
                    if est.ep == (rr, cc):
                        out.append(Lance(r, c, rr, cc, especial="ep"))
            elif tipo == "N":
                for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                               (1, -2), (1, 2), (2, -1), (2, 1)):
                    rr, cc = r + dr, c + dc
                    if dentro(rr, cc) and not mesma_cor(p, est.tab[rr][cc]):
                        out.append(Lance(r, c, rr, cc))
            elif tipo == "B":
                _add_deslize(est, r, c, ((-1, -1), (-1, 1), (1, -1), (1, 1)), out)
            elif tipo == "R":
                _add_deslize(est, r, c, ((-1, 0), (1, 0), (0, -1), (0, 1)), out)
            elif tipo == "Q":
                _add_deslize(est, r, c,
                             ((-1, -1), (-1, 1), (1, -1), (1, 1),
                              (-1, 0), (1, 0), (0, -1), (0, 1)), out)
            elif tipo == "K":
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if dentro(rr, cc) and not mesma_cor(p, est.tab[rr][cc]):
                            out.append(Lance(r, c, rr, cc))
                # roque
                if branco and r == 7 and c == 4:
                    if est.roque["K"] and est.tab[7][5] is None and est.tab[7][6] is None:
                        if (not atacada(est, 7, 4, False)
                                and not atacada(est, 7, 5, False)
                                and not atacada(est, 7, 6, False)):
                            out.append(Lance(7, 4, 7, 6, especial="castle_k"))
                    if est.roque["Q"] and est.tab[7][3] is None and est.tab[7][2] is None and est.tab[7][1] is None:
                        if (not atacada(est, 7, 4, False)
                                and not atacada(est, 7, 3, False)
                                and not atacada(est, 7, 2, False)):
                            out.append(Lance(7, 4, 7, 2, especial="castle_q"))
                if not branco and r == 0 and c == 4:
                    if est.roque["k"] and est.tab[0][5] is None and est.tab[0][6] is None:
                        if (not atacada(est, 0, 4, True)
                                and not atacada(est, 0, 5, True)
                                and not atacada(est, 0, 6, True)):
                            out.append(Lance(0, 4, 0, 6, especial="castle_k"))
                    if est.roque["q"] and est.tab[0][3] is None and est.tab[0][2] is None and est.tab[0][1] is None:
                        if (not atacada(est, 0, 4, True)
                                and not atacada(est, 0, 3, True)
                                and not atacada(est, 0, 2, True)):
                            out.append(Lance(0, 4, 0, 2, especial="castle_q"))
    return out


def aplicar(est: Estado, lance: Lance) -> Estado:
    novo = est.copia()
    p = novo.tab[lance.fr][lance.fc]
    capturou = novo.tab[lance.tr][lance.tc] is not None
    novo.tab[lance.fr][lance.fc] = None
    # en passant
    if lance.especial == "ep":
        # peão capturado fica na casa de origem do duplo
        novo.tab[lance.fr][lance.tc] = None
        capturou = True
    # promoção
    if lance.promo:
        p = lance.promo if eh_branco(p) else lance.promo.lower()
    novo.tab[lance.tr][lance.tc] = p
    # roque: mover torre
    if lance.especial == "castle_k":
        if lance.fr == 7:
            novo.tab[7][7] = None
            novo.tab[7][5] = "R"
        else:
            novo.tab[0][7] = None
            novo.tab[0][5] = "r"
    elif lance.especial == "castle_q":
        if lance.fr == 7:
            novo.tab[7][0] = None
            novo.tab[7][3] = "R"
        else:
            novo.tab[0][0] = None
            novo.tab[0][3] = "r"
    # atualizar direitos de roque
    if p in ("K", "k"):
        if eh_branco(p):
            novo.roque["K"] = novo.roque["Q"] = False
        else:
            novo.roque["k"] = novo.roque["q"] = False
    if (lance.fr, lance.fc) == (7, 0) or (lance.tr, lance.tc) == (7, 0):
        novo.roque["Q"] = False
    if (lance.fr, lance.fc) == (7, 7) or (lance.tr, lance.tc) == (7, 7):
        novo.roque["K"] = False
    if (lance.fr, lance.fc) == (0, 0) or (lance.tr, lance.tc) == (0, 0):
        novo.roque["q"] = False
    if (lance.fr, lance.fc) == (0, 7) or (lance.tr, lance.tc) == (0, 7):
        novo.roque["k"] = False
    # en passant alvo
    novo.ep = None
    if p and p.upper() == "P" and abs(lance.tr - lance.fr) == 2:
        novo.ep = ((lance.fr + lance.tr) // 2, lance.fc)
    # contadores
    if capturou or (p and p.upper() == "P"):
        novo.meio_lances = 0
    else:
        novo.meio_lances += 1
    if not novo.branco:
        novo.numero += 1
    novo.branco = not novo.branco
    return novo


def legais(est: Estado) -> List[Lance]:
    out = []
    for lance in geradores_pseudo(est):
        novo = aplicar(est, lance)
        # após o lance, o lado que jogou NÃO pode estar em xeque
        if not em_xeque(novo, not novo.branco):
            out.append(lance)
    return out


def perft(est: Estado, depth: int) -> int:
    if depth == 0:
        return 1
    n = 0
    for lance in legais(est):
        n += perft(aplicar(est, lance), depth - 1)
    return n


def avaliar(est: Estado) -> int:
    """Avaliação material simples (positiva = vantagem brancas)."""
    score = 0
    for r in range(8):
        for c in range(8):
            p = est.tab[r][c]
            if p is None:
                continue
            v = VALOR[p.upper()]
            # bônus central leve
            centro = 3.5
            bonus = int(3 - abs(r - centro) - abs(c - centro))
            if eh_branco(p):
                score += v + bonus
            else:
                score -= v + bonus
    return score


def minimax(est: Estado, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[Lance]]:
    lances = legais(est)
    if depth == 0 or not lances:
        if not lances:
            if em_xeque(est, est.branco):
                # mate: péssimo para quem deveria jogar
                return (-100000 if est.branco else 100000), None
            return 0, None  # afogamento
        return avaliar(est), None
    melhor_lance: Optional[Lance] = None
    if est.branco:
        melhor = -10**9
        random.shuffle(lances)
        for lance in lances:
            val, _ = minimax(aplicar(est, lance), depth - 1, alpha, beta)
            if val > melhor:
                melhor = val
                melhor_lance = lance
            alpha = max(alpha, melhor)
            if beta <= alpha:
                break
        return melhor, melhor_lance
    else:
        melhor = 10**9
        random.shuffle(lances)
        for lance in lances:
            val, _ = minimax(aplicar(est, lance), depth - 1, alpha, beta)
            if val < melhor:
                melhor = val
                melhor_lance = lance
            beta = min(beta, melhor)
            if beta <= alpha:
                break
        return melhor, melhor_lance


# ---------------------------------------------------------------------------
# Desenho das peças (polígonos — sem assets externos)
# ---------------------------------------------------------------------------
def desenhar_peca(surf: pygame.Surface, peca: str, cx: int, cy: int, tam: int) -> None:
    branca = eh_branco(peca)
    fill = BRANCO_PECA if branca else PRETO_PECA
    edge = CONTORNO
    t = tam
    tipo = peca.upper()

    def poly(pts, f=fill):
        pygame.draw.polygon(surf, f, pts)
        pygame.draw.polygon(surf, edge, pts, 2)

    def circ(r, f=fill):
        pygame.draw.circle(surf, f, (cx, cy - int(t * 0.15)), r)
        pygame.draw.circle(surf, edge, (cx, cy - int(t * 0.15)), r, 2)

    base_y = cy + int(t * 0.32)
    # base comum
    pygame.draw.ellipse(surf, fill, (cx - int(t * 0.28), base_y - 4, int(t * 0.56), 12))
    pygame.draw.ellipse(surf, edge, (cx - int(t * 0.28), base_y - 4, int(t * 0.56), 12), 2)

    if tipo == "P":
        pygame.draw.circle(surf, fill, (cx, cy - int(t * 0.08)), int(t * 0.14))
        pygame.draw.circle(surf, edge, (cx, cy - int(t * 0.08)), int(t * 0.14), 2)
        poly([(cx - int(t * 0.12), cy + int(t * 0.05)),
              (cx + int(t * 0.12), cy + int(t * 0.05)),
              (cx + int(t * 0.18), base_y),
              (cx - int(t * 0.18), base_y)])
    elif tipo == "R":
        poly([(cx - int(t * 0.22), cy - int(t * 0.22)),
              (cx - int(t * 0.22), cy - int(t * 0.05)),
              (cx + int(t * 0.22), cy - int(t * 0.05)),
              (cx + int(t * 0.22), cy - int(t * 0.22)),
              (cx + int(t * 0.14), cy - int(t * 0.22)),
              (cx + int(t * 0.14), cy - int(t * 0.32)),
              (cx + int(t * 0.06), cy - int(t * 0.32)),
              (cx + int(t * 0.06), cy - int(t * 0.22)),
              (cx - int(t * 0.06), cy - int(t * 0.22)),
              (cx - int(t * 0.06), cy - int(t * 0.32)),
              (cx - int(t * 0.14), cy - int(t * 0.32)),
              (cx - int(t * 0.14), cy - int(t * 0.22))])
        poly([(cx - int(t * 0.18), cy - int(t * 0.05)),
              (cx + int(t * 0.18), cy - int(t * 0.05)),
              (cx + int(t * 0.22), base_y),
              (cx - int(t * 0.22), base_y)])
    elif tipo == "N":
        poly([(cx - int(t * 0.18), base_y),
              (cx + int(t * 0.22), base_y),
              (cx + int(t * 0.18), cy + int(t * 0.05)),
              (cx + int(t * 0.28), cy - int(t * 0.05)),
              (cx + int(t * 0.10), cy - int(t * 0.28)),
              (cx - int(t * 0.05), cy - int(t * 0.35)),
              (cx - int(t * 0.22), cy - int(t * 0.18)),
              (cx - int(t * 0.10), cy - int(t * 0.05)),
              (cx - int(t * 0.22), cy + int(t * 0.10))])
        # olho
        olho = CONTORNO if branca else (200, 200, 200)
        pygame.draw.circle(surf, olho, (cx + int(t * 0.02), cy - int(t * 0.18)), 3)
    elif tipo == "B":
        poly([(cx, cy - int(t * 0.38)),
              (cx + int(t * 0.16), cy - int(t * 0.10)),
              (cx + int(t * 0.10), base_y),
              (cx - int(t * 0.10), base_y),
              (cx - int(t * 0.16), cy - int(t * 0.10))])
        pygame.draw.circle(surf, fill, (cx, cy - int(t * 0.28)), int(t * 0.08))
        pygame.draw.circle(surf, edge, (cx, cy - int(t * 0.28)), int(t * 0.08), 2)
        # fenda
        pygame.draw.line(surf, edge, (cx - 2, cy - int(t * 0.22)), (cx + 6, cy - int(t * 0.05)), 2)
    elif tipo == "Q":
        pts = [(cx - int(t * 0.24), base_y), (cx + int(t * 0.24), base_y),
               (cx + int(t * 0.20), cy + int(t * 0.05))]
        crowas = [(-0.22, -0.10), (-0.11, -0.35), (0.0, -0.15),
                  (0.11, -0.35), (0.22, -0.10)]
        for dx, dy in crowas:
            pts.append((cx + int(t * dx), cy + int(t * dy)))
        pts.append((cx - int(t * 0.20), cy + int(t * 0.05)))
        poly(pts)
        for dx, dy in crowas:
            pygame.draw.circle(surf, fill, (cx + int(t * dx), cy + int(t * dy)), 4)
            pygame.draw.circle(surf, edge, (cx + int(t * dx), cy + int(t * dy)), 4, 1)
    elif tipo == "K":
        poly([(cx - int(t * 0.22), base_y),
              (cx + int(t * 0.22), base_y),
              (cx + int(t * 0.18), cy + int(t * 0.02)),
              (cx + int(t * 0.14), cy - int(t * 0.18)),
              (cx - int(t * 0.14), cy - int(t * 0.18)),
              (cx - int(t * 0.18), cy + int(t * 0.02))])
        # cruz
        pygame.draw.rect(surf, fill, (cx - 3, cy - int(t * 0.42), 6, int(t * 0.28)))
        pygame.draw.rect(surf, edge, (cx - 3, cy - int(t * 0.42), 6, int(t * 0.28)), 1)
        pygame.draw.rect(surf, fill, (cx - int(t * 0.10), cy - int(t * 0.34), int(t * 0.20), 6))
        pygame.draw.rect(surf, edge, (cx - int(t * 0.10), cy - int(t * 0.34), int(t * 0.20), 6), 1)


# ---------------------------------------------------------------------------
# Jogo / UI
# ---------------------------------------------------------------------------
class Jogo:
    def __init__(self, demo: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("Xadrez — didático")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("dejavusans", 22)
        self.fonte_p = pygame.font.SysFont("dejavusans", 16)
        self.fonte_g = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.demo = demo
        self.reiniciar()
        self.pedir_print: List[str] = []
        self.prints_feitos: set = set()
        self.demo_timer = 0.0
        self.ai_espera = 0.0
        if demo:
            self.modo = "ai_ai"  # IA vs IA

    def reiniciar(self) -> None:
        self.est = Estado(tab=tabuleiro_inicial())
        self.sel: Optional[Pos] = None
        self.lances_sel: List[Lance] = []
        self.ultimo: Optional[Lance] = None
        self.msg = "Brancas jogam"
        self.fim = False
        self.modo = getattr(self, "modo", "2p")  # 2p | vs_ai_w | vs_ai_b | ai_ai
        self.promo_pendente: Optional[Lance] = None

    def casa_em(self, mx: int, my: int) -> Optional[Pos]:
        if not (TAB_X <= mx < TAB_X + 8 * TAM_CASA and TAB_Y <= my < TAB_Y + 8 * TAM_CASA):
            return None
        c = (mx - TAB_X) // TAM_CASA
        r = (my - TAB_Y) // TAM_CASA
        return int(r), int(c)

    def atualizar_status(self) -> None:
        lances = legais(self.est)
        if not lances:
            if em_xeque(self.est, self.est.branco):
                vencedor = "Pretas" if self.est.branco else "Brancas"
                self.msg = f"Xeque-mate! {vencedor} vencem"
            else:
                self.msg = "Afogamento — empate"
            self.fim = True
        elif em_xeque(self.est, self.est.branco):
            lado = "Brancas" if self.est.branco else "Pretas"
            self.msg = f"Xeque! {lado} jogam"
        else:
            lado = "Brancas" if self.est.branco else "Pretas"
            self.msg = f"{lado} jogam"

    def tentar_mover(self, lance: Lance) -> None:
        # promoção: se peão chega ao fim sem promo definida, força rainha
        p = self.est.tab[lance.fr][lance.fc]
        if p and p.upper() == "P" and lance.tr in (0, 7) and not lance.promo:
            lance = Lance(lance.fr, lance.fc, lance.tr, lance.tc, promo="Q", especial=lance.especial)
        self.est = aplicar(self.est, lance)
        self.ultimo = lance
        self.sel = None
        self.lances_sel = []
        self.atualizar_status()

    def clique(self, pos: Pos) -> None:
        if self.fim or self.modo == "ai_ai":
            return
        # se é turno da IA, ignore
        if self.modo == "vs_ai_w" and not self.est.branco:
            return
        if self.modo == "vs_ai_b" and self.est.branco:
            return
        r, c = pos
        if self.sel is None:
            p = self.est.tab[r][c]
            if p and ((self.est.branco and eh_branco(p)) or (not self.est.branco and eh_preto(p))):
                self.sel = pos
                self.lances_sel = [L for L in legais(self.est) if L.fr == r and L.fc == c]
        else:
            escolhido = None
            for L in self.lances_sel:
                if L.tr == r and L.tc == c:
                    escolhido = L
                    break
            if escolhido:
                self.tentar_mover(escolhido)
            else:
                p = self.est.tab[r][c]
                if p and ((self.est.branco and eh_branco(p)) or (not self.est.branco and eh_preto(p))):
                    self.sel = pos
                    self.lances_sel = [L for L in legais(self.est) if L.fr == r and L.fc == c]
                else:
                    self.sel = None
                    self.lances_sel = []

    def turno_da_ia(self) -> bool:
        if self.fim:
            return False
        if self.modo == "ai_ai":
            return True
        if self.modo == "vs_ai_w" and not self.est.branco:
            return True
        if self.modo == "vs_ai_b" and self.est.branco:
            return True
        return False

    def jogar_ia(self) -> None:
        _, lance = minimax(self.est, 2, -10**9, 10**9)
        if lance is None:
            self.atualizar_status()
            return
        self.tentar_mover(lance)

    def desenhar(self) -> None:
        self.tela.fill(COR_FUNDO)
        # casas
        for r in range(8):
            for c in range(8):
                clara = (r + c) % 2 == 0
                cor = COR_CLARA if clara else COR_ESCURA
                # último lance
                if self.ultimo and ((r, c) == (self.ultimo.fr, self.ultimo.fc)
                                    or (r, c) == (self.ultimo.tr, self.ultimo.tc)):
                    cor = COR_ULT
                if self.sel == (r, c):
                    cor = COR_SEL
                rect = pygame.Rect(TAB_X + c * TAM_CASA, TAB_Y + r * TAM_CASA, TAM_CASA, TAM_CASA)
                pygame.draw.rect(self.tela, cor, rect)
        # lances legais
        for L in self.lances_sel:
            cx = TAB_X + L.tc * TAM_CASA + TAM_CASA // 2
            cy = TAB_Y + L.tr * TAM_CASA + TAM_CASA // 2
            if self.est.tab[L.tr][L.tc] is not None or L.especial == "ep":
                pygame.draw.circle(self.tela, (220, 60, 60), (cx, cy), 34, 4)
            else:
                pygame.draw.circle(self.tela, (40, 40, 40), (cx, cy), 12)
        # peças
        for r in range(8):
            for c in range(8):
                p = self.est.tab[r][c]
                if p:
                    cx = TAB_X + c * TAM_CASA + TAM_CASA // 2
                    cy = TAB_Y + r * TAM_CASA + TAM_CASA // 2
                    desenhar_peca(self.tela, p, cx, cy, TAM_CASA)
        # rótulos arquivos A-H
        for c, letra in enumerate("ABCDEFGH"):
            img = self.fonte_p.render(letra, True, COR_TEXTO)
            self.tela.blit(img, (TAB_X + c * TAM_CASA + TAM_CASA // 2 - img.get_width() // 2,
                                 TAB_Y + 8 * TAM_CASA + 6))
        # rótulos ranks 8-1
        for r in range(8):
            img = self.fonte_p.render(str(8 - r), True, COR_TEXTO)
            self.tela.blit(img, (TAB_X - 22, TAB_Y + r * TAM_CASA + TAM_CASA // 2 - img.get_height() // 2))
        # HUD
        img = self.fonte.render(self.msg, True, COR_TEXTO)
        self.tela.blit(img, (MARGEM, ALTURA - 90))
        modo_txt = {
            "2p": "Modo: 2 jogadores (tecla 1)",
            "vs_ai_w": "Modo: você Brancas vs IA (2)",
            "vs_ai_b": "Modo: você Pretas vs IA (3)",
            "ai_ai": "Modo: IA vs IA (demo)",
        }.get(self.modo, "")
        self.tela.blit(self.fonte_p.render(modo_txt + "  ·  R reinicia  ·  ESC sai", True, (180, 180, 180)),
                       (MARGEM, ALTURA - 55))
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
        if "meio.png" not in self.prints_feitos and self.est.numero >= 4:
            self.pedir_print.append("meio.png")
            self.prints_feitos.add("meio.png")
        if "fim.png" not in self.prints_feitos and (self.fim or self.demo_timer > 6.5):
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
                    if self.demo:
                        self.modo = "ai_ai"
                if ev.key == pygame.K_1:
                    self.reiniciar(); self.modo = "2p"
                if ev.key == pygame.K_2:
                    self.reiniciar(); self.modo = "vs_ai_w"
                if ev.key == pygame.K_3:
                    self.reiniciar(); self.modo = "vs_ai_b"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                casa = self.casa_em(*ev.pos)
                if casa:
                    self.clique(casa)
        return True

    def atualizar(self, dt: float) -> None:
        if self.demo:
            self.demo_timer += dt
            self._demo_prints()
        if self.turno_da_ia() and not self.fim:
            self.ai_espera += dt
            espera = 0.35 if self.demo else 0.45
            if self.ai_espera >= espera:
                self.ai_espera = 0.0
                self.jogar_ia()

    def rodar(self) -> None:
        self.atualizar_status()
        rodando = True
        while rodando:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            rodando = self.tratar()
            self.atualizar(dt)
            self.desenhar()
            if self.demo and (self.demo_timer > 7.5 or ("fim.png" in self.prints_feitos and self.demo_timer > 1.0 and self.fim)):
                if "fim.png" not in self.prints_feitos:
                    self.pedir_print.append("fim.png")
                    self.prints_feitos.add("fim.png")
                    self.desenhar()
                rodando = False
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Xadrez didático (Pygame)")
    parser.add_argument("--demo", action="store_true", help="IA vs IA + prints/")
    parser.add_argument("--perft", type=int, default=0, help="Roda perft na posição inicial")
    args = parser.parse_args()
    if args.perft:
        est = Estado(tab=tabuleiro_inicial())
        t0 = time.time()
        n = perft(est, args.perft)
        print(f"perft({args.perft}) = {n}  ({time.time() - t0:.2f}s)")
        return
    if args.demo and not os.environ.get("DISPLAY") and not os.environ.get("SDL_VIDEODRIVER"):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    Jogo(demo=args.demo).rodar()


if __name__ == "__main__":
    main()

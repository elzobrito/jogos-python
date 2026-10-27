#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
DINO RUNNER — Versão de Aula (Python 3 + Pygame-CE)
================================================================================
Jogo estilo endless runner inspirado no dinossauro do Chrome, desenvolvido
integralmente em um único arquivo sem assets externos (toda a pixel art e os
efeitos sonoros são gerados via código).

Suporta dois temas visuais (alternáveis com a tecla [T] ou flag `--classico`):
  1. Tema Colorido (padrão): deserto com camadas em parallax (montanhas, dunas,
     nuvens, ciclo dia/noite) e sprites coloridos.
  2. Tema Clássico (referência Chrome Dino): fundo branco, T-rex cinza-escuro
     (#535353), cactos saguaro, nuvens pixeladas com contorno claro e chão como
     linha fina com pequenas saliências e pontinhos espalhados.

Organização didática do arquivo:
  - ETAPA 1: Dinossauro correndo e pulando (Game loop, eventos, gravidade)
  - ETAPA 2: Chão e cenário rolando (Coordenadas, delta time, animação)
  - ETAPA 3: Cactos surgindo (Objetos, aleatoriedade, colisões)
  - ETAPA 4: Pontuação e game over (Condicionais, estados, persistência)
  - ETAPA 5: Pterodáctilos e agachar (Herança/composição, hitboxes)
  - ETAPA 6: Música, efeitos e polimento (Áudio sintetizado, partículas, temas)
================================================================================
"""

from __future__ import annotations

import argparse
import json
import math
import random
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

# ==============================================================================
# CONFIGURAÇÕES GERAIS E CONSTANTES DO JOGO
# ==============================================================================
LARGURA_TELA = 960
ALTURA_TELA = 540
FPS_ALVO = 60

# Posição vertical da linha de referência do solo onde o dinossauro pisa
Y_CHAO = 430
X_FIXO_DINO = 120

# Parâmetros de velocidade e progressão de dificuldade (conforme SPEC.md)
VELOCIDADE_INICIAL = 320.0   # Começa em 320 px/s
INCREMENTO_VELOCIDADE = 8.0  # +8 px/s a cada intervalo
INTERVALO_INCREMENTO = 10.0  # A cada 10 segundos
VELOCIDADE_MAXIMA = 620.0    # Máximo de 620 px/s

# Parâmetros físicos do pulo do dinossauro
IMPULSO_PULO = -740.0        # Velocidade vertical inicial do pulo (px/s)
GRAVIDADE = 1800.0           # Aceleração da gravidade (px/s²)
GRAVIDADE_QUEDA_RAPIDA = 3600.0  # Gravidade extra ao segurar seta para baixo no ar

# Cores do tema clássico (referência Chrome Dino)
COR_CLASSICO_ESCURA = (83, 83, 83)      # #535353
COR_CLASSICO_FUNDO = (255, 255, 255)    # #FFFFFF
COR_CLASSICO_CONTORNO_NUVEM = (212, 212, 212)

# Identificadores de tema
TEMA_COLORIDO = "colorido"
TEMA_CLASSICO = "classico"

# Diretório base do script para salvar recorde.json e pasta prints/
DIRETORIO_BASE = Path(__file__).resolve().parent
ARQUIVO_RECORDE = DIRETORIO_BASE / "recorde.json"
PASTA_PRINTS = DIRETORIO_BASE / "prints"


# ==============================================================================
# UTILITÁRIOS DE PIXEL ART E FONTE PIXEL EM NEGRITO (HUD)
# ==============================================================================
def criar_superficie_pixel_art(
    grade: Sequence[str],
    paleta: Dict[str, Tuple[int, int, int]],
    escala: int = 3,
) -> pygame.Surface:
    """
    Converte uma matriz de caracteres (strings) em uma pygame.Surface.
    Espaços ou '.' são tratados como pixels transparentes.
    """
    altura = len(grade)
    largura = max(len(linha) for linha in grade) if altura > 0 else 1
    superficie = pygame.Surface((largura * escala, altura * escala), pygame.SRCALPHA)

    for y, linha in enumerate(grade):
        for x, caractere in enumerate(linha):
            if caractere in paleta:
                cor = paleta[caractere]
                pygame.draw.rect(
                    superficie,
                    cor,
                    pygame.Rect(x * escala, y * escala, escala, escala),
                )
    return superficie


def interpolar_cor(
    cor_a: Tuple[int, int, int],
    cor_b: Tuple[int, int, int],
    fator: float,
) -> Tuple[int, int, int]:
    """Interpola linearmente duas cores RGB com fator entre 0.0 e 1.0."""
    f = max(0.0, min(1.0, fator))
    return (
        int(cor_a[0] + (cor_b[0] - cor_a[0]) * f),
        int(cor_a[1] + (cor_b[1] - cor_a[1]) * f),
        int(cor_a[2] + (cor_b[2] - cor_a[2]) * f),
    )


# Glifos 6x7 em negrito para renderizar a HUD no formato "HI 000849  000660"
GLIFOS_HUD_PIXEL: Dict[str, Sequence[str]] = {
    "H": [
        "XX..XX",
        "XX..XX",
        "XX..XX",
        "XXXXXX",
        "XX..XX",
        "XX..XX",
        "XX..XX",
    ],
    "I": [
        "XXXXXX",
        "..XX..",
        "..XX..",
        "..XX..",
        "..XX..",
        "..XX..",
        "XXXXXX",
    ],
    "0": [
        ".XXXX.",
        "XX..XX",
        "XX..XX",
        "XX..XX",
        "XX..XX",
        "XX..XX",
        ".XXXX.",
    ],
    "1": [
        "..XX..",
        ".XXX..",
        "..XX..",
        "..XX..",
        "..XX..",
        "..XX..",
        "XXXXXX",
    ],
    "2": [
        ".XXXX.",
        "XX..XX",
        "....XX",
        "..XXX.",
        ".XX...",
        "XX....",
        "XXXXXX",
    ],
    "3": [
        "XXXXX.",
        "....XX",
        "....XX",
        ".XXXX.",
        "....XX",
        "....XX",
        "XXXXX.",
    ],
    "4": [
        "XX..XX",
        "XX..XX",
        "XX..XX",
        "XXXXXX",
        "....XX",
        "....XX",
        "....XX",
    ],
    "5": [
        "XXXXXX",
        "XX....",
        "XXXXX.",
        "....XX",
        "....XX",
        "XX..XX",
        ".XXXX.",
    ],
    "6": [
        ".XXXX.",
        "XX....",
        "XXXXX.",
        "XX..XX",
        "XX..XX",
        "XX..XX",
        ".XXXX.",
    ],
    "7": [
        "XXXXXX",
        "....XX",
        "...XX.",
        "..XX..",
        "..XX..",
        "..XX..",
        "..XX..",
    ],
    "8": [
        ".XXXX.",
        "XX..XX",
        "XX..XX",
        ".XXXX.",
        "XX..XX",
        "XX..XX",
        ".XXXX.",
    ],
    "9": [
        ".XXXX.",
        "XX..XX",
        "XX..XX",
        ".XXXXX",
        "....XX",
        "XX..XX",
        ".XXXX.",
    ],
    " ": [
        "....",
        "....",
        "....",
        "....",
        "....",
        "....",
        "....",
    ],
}


def renderizar_texto_pixel_negrito(
    texto: str,
    cor: Tuple[int, int, int],
    escala: int = 3,
    cor_sombra: Optional[Tuple[int, int, int]] = None,
) -> pygame.Surface:
    """Renderiza texto usando a fonte bitmap em negrito estilo Chrome Dino."""
    grades_caracteres = [GLIFOS_HUD_PIXEL.get(ch, GLIFOS_HUD_PIXEL[" "]) for ch in texto]
    largura_unidades = sum(len(g[0]) + 1 for g in grades_caracteres)
    altura_unidades = 7
    extra_sombra = 1 if cor_sombra else 0
    superficie = pygame.Surface(
        ((largura_unidades + extra_sombra) * escala, (altura_unidades + extra_sombra) * escala),
        pygame.SRCALPHA,
    )

    cursor_x = 0
    for grade in grades_caracteres:
        larg_char = len(grade[0])
        for y, linha in enumerate(grade):
            for x, pixel in enumerate(linha):
                if pixel == "X":
                    if cor_sombra:
                        pygame.draw.rect(
                            superficie,
                            cor_sombra,
                            pygame.Rect(
                                (cursor_x + x + 1) * escala,
                                (y + 1) * escala,
                                escala,
                                escala,
                            ),
                        )
                    pygame.draw.rect(
                        superficie,
                        cor,
                        pygame.Rect(
                            (cursor_x + x) * escala,
                            y * escala,
                            escala,
                            escala,
                        ),
                    )
        cursor_x += larg_char + 1
    return superficie


# ==============================================================================
# ETAPA 1: DINOSSAURO CORRENDO E PULANDO (Game loop, eventos, gravidade)
# ==============================================================================
# Paleta para o tema colorido e para o tema clássico (#535353)
PALETAS_DINO: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    TEMA_COLORIDO: {
        "V": (46, 160, 67),    # Verde principal do corpo
        "E": (27, 107, 45),    # Verde escuro (contorno/dorso)
        "C": (143, 224, 130),  # Verde claro (peito/barriga)
        "B": (255, 255, 255),  # Olho branco
        "R": (230, 75, 60),    # Detalhe do olho na colisão
    },
    TEMA_CLASSICO: {
        "V": COR_CLASSICO_ESCURA,
        "E": COR_CLASSICO_ESCURA,
        "C": COR_CLASSICO_ESCURA,
        "B": COR_CLASSICO_FUNDO,
        "R": COR_CLASSICO_ESCURA,
    },
}

# Silhueta do T-Rex do Chrome em ambos os temas (20 colunas x 14 linhas superiores)
TOPO_TREX_EM_PE = [
    "..........EEEEEEEEEE",
    ".........EVVVVVVVVVV",
    ".........EVVBVVVVVVV",
    ".........EVVVVVVVVVV",
    ".........EVVVVVVVVVV",
    ".........EVVVVVEEEEE",
    ".........EVVVVVVVEEE",
    "E.......EVVVVVVVE...",
    "EV.....EVVVVVVVVEEE.",
    "EVV...EVVVVVVCCVVVVE",
    "EVVV.EVVVVVVCCCVV..E",
    ".EVVVVVVVVVVCCCV....",
    "..EVVVVVVVVVCCVE....",
    "...EEVVVVVVVVVE.....",
]

# 6 quadros de animação para as pernas durante a corrida
PERNAS_CORRIDA_6_QUADROS = [
    [
        ".....EVVVVVVVVE.....",
        "......EVVV..EVV.....",
        "......EV.....EE.....",
        "......EEE...........",
    ],
    [
        ".....EVVVVVVVVE.....",
        "......EVVV...EV.....",
        ".......EEE...EEE....",
        "....................",
    ],
    [
        ".....EVVVVVVVVE.....",
        "......EEE...EVVV....",
        "............EV......",
        "............EEE.....",
    ],
    [
        ".....EVVVVVVVVE.....",
        "......EV....EVVV....",
        "......EEE....EV.....",
        ".............EEE....",
    ],
    [
        ".....EVVVVVVVVE.....",
        "......EVVV..EEE.....",
        "......EV............",
        "......EEE...........",
    ],
    [
        ".....EVVVVVVVVE.....",
        "......EVV...EVV.....",
        "......EEE...EEE.....",
        "....................",
    ],
]

# Pernas no salto
PERNAS_PULO = [
    ".....EVVVVVVVVE.....",
    "......EVVV..EVVV....",
    "......EEE....EEE....",
    "....................",
]

# Quadro de colisão (olho arregalado e boca aberta)
GRADE_TREX_COLISAO = [
    "..........EEEEEEEEEE",
    ".........EVVVVVVVVVV",
    ".........EVBBBVVVVVV",
    ".........EVBRBVVVVVV",
    ".........EVBBBVVVVVV",
    ".........EVVVVVEEEEE",
    ".........EVVVVVVVEEE",
    "E.......EVVVVVVVE...",
    "EV.....EVVVVVVVVEEE.",
    "EVV...EVVVVVVCCVVVVE",
    "EVVV.EVVVVVVCCCVV..E",
    ".EVVVVVVVVVVCCCV....",
    "..EVVVVVVVVVCCVE....",
    "...EEVVVVVVVVVE.....",
    ".....EVVVVVVVVE.....",
    "......EVVV..EVVV....",
    "......EV.....EV.....",
    "......EEE....EEE....",
]

# Silhueta do T-Rex do Chrome agachado (Etapa 5: 24 colunas x 11 linhas)
GRADES_TREX_ABAIXADO = [
    [
        "........................",
        "E............EEEEEEEEEE.",
        "EVV...EEEEEEEVVVVVVVVVVE",
        "EVVV.EVVVVVVVVVBVVVVVVVE",
        ".EVVVVVVVVVVVVVVVVVVVVVE",
        "..EVVVVVVVVCCCVVVVEEEEEE",
        "...EEVVVVVVCCCVVVVVEEE..",
        ".....EEVVVVVVVVVE..E....",
        ".......EVVV..EVV........",
        ".......EV.....EE........",
        ".......EEE..............",
    ],
    [
        "........................",
        "E............EEEEEEEEEE.",
        "EVV...EEEEEEEVVVVVVVVVVE",
        "EVVV.EVVVVVVVVVBVVVVVVVE",
        ".EVVVVVVVVVVVVVVVVVVVVVE",
        "..EVVVVVVVVCCCVVVVEEEEEE",
        "...EEVVVVVVCCCVVVVVEEE..",
        ".....EEVVVVVVVVVE..E....",
        ".......EEE...EVVV.......",
        ".............EV.........",
        ".............EEE........",
    ],
]


class Dinossauro(pygame.sprite.Sprite):
    """
    Representa o T-Rex controlado pelo jogador (ou pelo piloto automático).
    Herda de pygame.sprite.Sprite e utiliza delta time (dt) para física e animação.
    """

    def __init__(self, x: int = X_FIXO_DINO, y_chao: int = Y_CHAO, tema: str = TEMA_COLORIDO) -> None:
        super().__init__()
        self.x_fixo = x
        self.y_chao = y_chao
        self.tema = tema

        # Pré-renderiza os conjuntos de sprites para ambos os temas
        escala = 3
        self.sprites_por_tema: Dict[str, Dict[str, List[pygame.Surface]]] = {}
        for nome_tema, paleta in PALETAS_DINO.items():
            self.sprites_por_tema[nome_tema] = {
                "corrida": [
                    criar_superficie_pixel_art(TOPO_TREX_EM_PE + pernas, paleta, escala)
                    for pernas in PERNAS_CORRIDA_6_QUADROS
                ],
                "pulo": [
                    criar_superficie_pixel_art(TOPO_TREX_EM_PE + PERNAS_PULO, paleta, escala)
                ],
                "abaixado": [
                    criar_superficie_pixel_art(grade, paleta, escala)
                    for grade in GRADES_TREX_ABAIXADO
                ],
                "colisao": [
                    criar_superficie_pixel_art(GRADE_TREX_COLISAO, paleta, escala)
                ],
            }

        # Estado físico e de animação
        self.pos_y_inferior: float = float(self.y_chao)
        self.velocidade_y: float = 0.0
        self.no_chao: bool = True
        self.abaixado: bool = False
        self.bateu: bool = False
        self.acabou_de_pousar: bool = False

        self.indice_quadro: int = 0
        self.tempo_animacao: float = 0.0
        self.intervalo_quadro: float = 0.075

        self.image: pygame.Surface = self.sprites_por_tema[self.tema]["corrida"][0]
        self.rect: pygame.Rect = self.image.get_rect(midbottom=(self.x_fixo, self.y_chao))

    def definir_tema(self, novo_tema: str) -> None:
        """Alterna o tema visual do T-Rex preservando sua posição e estado."""
        self.tema = novo_tema
        self._atualizar_imagem_atual()

    def reiniciar(self) -> None:
        """Restaura o dinossauro ao estado inicial no solo."""
        self.pos_y_inferior = float(self.y_chao)
        self.velocidade_y = 0.0
        self.no_chao = True
        self.abaixado = False
        self.bateu = False
        self.acabou_de_pousar = False
        self.indice_quadro = 0
        self.tempo_animacao = 0.0
        self._atualizar_imagem_atual()

    def pular(self) -> bool:
        """Inicia o pulo somente se estiver no chão (sem pulo duplo)."""
        if self.no_chao and not self.bateu:
            self.velocidade_y = IMPULSO_PULO
            self.no_chao = False
            self.abaixado = False
            return True
        return False

    def definir_abaixado(self, ativo: bool) -> None:
        """Ativa ou desativa a postura agachada."""
        if not self.bateu:
            self.abaixado = ativo

    @property
    def hitbox(self) -> pygame.Rect:
        """Hitbox levemente menor que o sprite e mais baixa ao agachar."""
        if self.abaixado and self.no_chao:
            return self.rect.inflate(-18, -8)
        return self.rect.inflate(-20, -10)

    def _atualizar_imagem_atual(self) -> None:
        conjunto = self.sprites_por_tema[self.tema]
        if self.bateu:
            self.image = conjunto["colisao"][0]
        elif not self.no_chao:
            self.image = conjunto["pulo"][0]
        elif self.abaixado:
            quadros = conjunto["abaixado"]
            self.image = quadros[self.indice_quadro % len(quadros)]
        else:
            quadros = conjunto["corrida"]
            self.image = quadros[self.indice_quadro % len(quadros)]
        self.rect = self.image.get_rect(midbottom=(self.x_fixo, int(round(self.pos_y_inferior))))

    def update(self, dt: float) -> None:
        """Atualiza física vertical (gravidade) e animação do dinossauro."""
        self.acabou_de_pousar = False

        if self.bateu:
            self._atualizar_imagem_atual()
            return

        # 1. Física vertical (pulo e gravidade com delta time)
        if not self.no_chao:
            gravidade_atual = GRAVIDADE_QUEDA_RAPIDA if self.abaixado else GRAVIDADE
            self.velocidade_y += gravidade_atual * dt
            self.pos_y_inferior += self.velocidade_y * dt

            if self.pos_y_inferior >= self.y_chao:
                self.pos_y_inferior = float(self.y_chao)
                self.velocidade_y = 0.0
                self.no_chao = True
                self.acabou_de_pousar = True

        # 2. Avanço de quadros da animação
        self.tempo_animacao += dt
        if self.abaixado and self.no_chao:
            if self.tempo_animacao >= self.intervalo_quadro * 1.2:
                self.tempo_animacao = 0.0
                self.indice_quadro = (self.indice_quadro + 1) % 2
        elif self.no_chao:
            if self.tempo_animacao >= self.intervalo_quadro:
                self.tempo_animacao = 0.0
                self.indice_quadro = (self.indice_quadro + 1) % 6

        self._atualizar_imagem_atual()


# ==============================================================================
# ETAPA 2: CHÃO E CENÁRIO ROLANDO (Coordenadas, delta time, animação)
# ==============================================================================
PALETAS_NUVEM: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    TEMA_COLORIDO: {
        "C": (222, 232, 245),  # Contorno suave azulado
        "B": (255, 255, 255),  # Interior branco
    },
    TEMA_CLASSICO: {
        "C": COR_CLASSICO_CONTORNO_NUVEM,  # Contorno claro estilo Chrome
        "B": COR_CLASSICO_FUNDO,           # Interior branco
    },
}

GRADE_NUVEM = [
    ".....CCCCCC.....",
    "...CCBBBBBBCC...",
    ".CCBBBBBBBBBBCC.",
    "CBBBBBBBBBBBBBBC",
    "CCCCCCCCCCCCCCCC",
]


class Nuvem(pygame.sprite.Sprite):
    """Nuvem decorativa em pixel art com contorno claro."""

    def __init__(
        self,
        x: float,
        y: float,
        escala: int = 4,
        fator_velocidade: float = 0.18,
        tema: str = TEMA_COLORIDO,
    ) -> None:
        super().__init__()
        self.escala = escala
        self.tema = tema
        self.imagens = {
            t: criar_superficie_pixel_art(GRADE_NUVEM, pal, escala)
            for t, pal in PALETAS_NUVEM.items()
        }
        self.image = self.imagens[self.tema]
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.fator_velocidade = fator_velocidade
        self.rect = self.image.get_rect(topleft=(int(self.pos_x), int(self.pos_y)))

    def definir_tema(self, novo_tema: str) -> None:
        self.tema = novo_tema
        self.image = self.imagens[self.tema]

    def update(self, dt: float, velocidade_mundo: float) -> None:
        self.pos_x -= velocidade_mundo * self.fator_velocidade * dt
        if self.pos_x + self.rect.width < -20:
            self.pos_x = float(LARGURA_TELA + random.randint(40, 220))
            self.pos_y = float(random.randint(55, 200))
        self.rect.topleft = (int(self.pos_x), int(self.pos_y))


class CenarioDeserto:
    """
    Gerencia o cenário em ambos os temas:
    - Tema Colorido: deserto em parallax (céu com ciclo dia/noite, sol/lua,
      montanhas, dunas, nuvens e faixa de areia com pedrinhas).
    - Tema Clássico: fundo branco (#FFFFFF), nuvens pixel com contorno claro e
      chão como linha fina (#535353) com pequenas saliências e pontinhos espalhados.
    """

    def __init__(self, y_chao: int = Y_CHAO, tema: str = TEMA_COLORIDO) -> None:
        self.y_chao = y_chao
        self.tema = tema
        self.deslocamento_montanhas = 0.0
        self.deslocamento_dunas = 0.0
        self.deslocamento_chao = 0.0

        # Ciclo dia/noite para o tema colorido
        self.tempo_ciclo = 0.0
        self.duracao_ciclo_completo = 60.0

        # Grupo de nuvens
        self.grupo_nuvens = pygame.sprite.Group()
        posicoes_iniciais = [
            (150, 80, 3, 0.15),
            (410, 125, 4, 0.20),
            (680, 70, 3, 0.12),
            (870, 145, 4, 0.17),
        ]
        for x, y, esc, fat in posicoes_iniciais:
            self.grupo_nuvens.add(Nuvem(x, y, esc, fat, tema=self.tema))

        rng = random.Random(42)
        self.estrelas: List[Tuple[int, int, int]] = [
            (rng.randint(20, LARGURA_TELA - 20), rng.randint(20, 240), rng.choice([2, 3]))
            for _ in range(36)
        ]

        # Pontinhos e pedrinhas espalhados abaixo da linha do chão
        self.detalhes_chao: List[Tuple[int, int, int, int]] = [
            (rng.randint(0, LARGURA_TELA), rng.randint(6, 48), rng.choice([2, 3, 5, 8]), 2)
            for _ in range(55)
        ]

        # Pequenas saliências na linha do horizonte para o tema clássico (pos_x, larg, alt_desvio)
        self.saliencias_chao: List[Tuple[int, int, int]] = [
            (90, 18, -4),
            (260, 14, 3),
            (430, 22, -5),
            (610, 16, -3),
            (790, 20, 4),
            (910, 14, -4),
        ]

    def definir_tema(self, novo_tema: str) -> None:
        self.tema = novo_tema
        for nuvem in self.grupo_nuvens:
            nuvem.definir_tema(novo_tema)

    def atualizar(self, dt: float, velocidade_mundo: float) -> None:
        self.deslocamento_montanhas = (self.deslocamento_montanhas + velocidade_mundo * 0.12 * dt) % LARGURA_TELA
        self.deslocamento_dunas = (self.deslocamento_dunas + velocidade_mundo * 0.30 * dt) % LARGURA_TELA
        self.deslocamento_chao = (self.deslocamento_chao + velocidade_mundo * dt) % LARGURA_TELA
        self.tempo_ciclo = (self.tempo_ciclo + dt) % self.duracao_ciclo_completo
        self.grupo_nuvens.update(dt, velocidade_mundo)

    def fator_noite(self) -> float:
        angulo = (self.tempo_ciclo / self.duracao_ciclo_completo) * 2.0 * math.pi
        bruto = (1.0 - math.cos(angulo)) * 0.5
        return max(0.0, min(1.0, (bruto - 0.25) / 0.5)) if bruto > 0.25 else 0.0

    def _desenhar_tema_classico(self, tela: pygame.Surface) -> None:
        """Renderiza o cenário clássico estilo Chrome Dino (fundo branco e linha com saliências)."""
        tela.fill(COR_CLASSICO_FUNDO)
        self.grupo_nuvens.draw(tela)

        # Linha fina do horizonte com pequenas saliências que rolam com o chão
        y_linha = self.y_chao - 2
        mapa_saliencias: List[Tuple[int, int, int]] = []
        for sx, larg, desvio in self.saliencias_chao:
            x_atual = int((sx - self.deslocamento_chao) % LARGURA_TELA)
            if x_atual + larg < LARGURA_TELA:
                mapa_saliencias.append((x_atual, x_atual + larg, desvio))

        mapa_saliencias.sort(key=lambda item: item[0])
        cursor_x = 0
        for ini, fim, desvio in mapa_saliencias:
            if ini > cursor_x:
                pygame.draw.line(tela, COR_CLASSICO_ESCURA, (cursor_x, y_linha), (ini, y_linha), 2)
            # Desenha a pequena saliência (degrau de pixel art na linha do chão)
            pygame.draw.line(tela, COR_CLASSICO_ESCURA, (ini, y_linha), (ini + 3, y_linha + desvio), 2)
            pygame.draw.line(
                tela,
                COR_CLASSICO_ESCURA,
                (ini + 3, y_linha + desvio),
                (fim - 3, y_linha + desvio),
                2,
            )
            pygame.draw.line(tela, COR_CLASSICO_ESCURA, (fim - 3, y_linha + desvio), (fim, y_linha), 2)
            cursor_x = fim

        if cursor_x < LARGURA_TELA:
            pygame.draw.line(tela, COR_CLASSICO_ESCURA, (cursor_x, y_linha), (LARGURA_TELA, y_linha), 2)

        # Pontinhos espalhados abaixo da linha do solo
        for px, py_rel, larg, alt in self.detalhes_chao:
            x_tela = int((px - self.deslocamento_chao) % LARGURA_TELA)
            pygame.draw.rect(
                tela,
                COR_CLASSICO_ESCURA,
                pygame.Rect(x_tela, self.y_chao + (py_rel % 26) + 2, larg, alt),
            )

    def _desenhar_tema_colorido(self, tela: pygame.Surface) -> None:
        """Renderiza o deserto colorido com camadas em parallax."""
        noite = self.fator_noite()

        cor_topo = interpolar_cor((115, 198, 245), (20, 26, 56), noite)
        cor_horizonte = interpolar_cor((252, 232, 186), (58, 48, 92), noite)

        faixas = 12
        altura_faixa = math.ceil(self.y_chao / faixas)
        for i in range(faixas):
            f = i / max(1, faixas - 1)
            cor_faixa = interpolar_cor(cor_topo, cor_horizonte, f)
            pygame.draw.rect(
                tela,
                cor_faixa,
                pygame.Rect(0, i * altura_faixa, LARGURA_TELA, altura_faixa + 1),
            )

        if noite > 0.15:
            brilho = int(230 * noite)
            cor_estrela = (brilho, brilho, min(255, brilho + 25))
            for sx, sy, tam in self.estrelas:
                pygame.draw.rect(tela, cor_estrela, pygame.Rect(sx, sy, tam, tam))

        cor_astro = interpolar_cor((255, 225, 95), (235, 240, 255), noite)
        pygame.draw.circle(tela, cor_astro, (790, 92), 28)

        # Montanhas distantes
        cor_montanha = interpolar_cor((198, 152, 116), (48, 44, 78), noite)
        cor_montanha_sombra = interpolar_cor((172, 126, 94), (36, 33, 62), noite)
        picos_base = [
            (0, 350), (140, 255), (270, 330), (420, 235),
            (590, 340), (740, 265), (880, 320), (LARGURA_TELA, 350),
        ]
        for repeticao in range(2):
            offset_x = -int(self.deslocamento_montanhas) + repeticao * LARGURA_TELA
            pontos = [(px + offset_x, py) for px, py in picos_base]
            poligono = [(offset_x, self.y_chao)] + pontos + [(offset_x + LARGURA_TELA, self.y_chao)]
            pygame.draw.polygon(tela, cor_montanha, poligono)
            pygame.draw.lines(tela, cor_montanha_sombra, False, pontos, 3)

        # Dunas intermediárias
        cor_duna = interpolar_cor((230, 186, 122), (72, 62, 96), noite)
        picos_dunas = [
            (0, 390), (180, 355), (360, 395), (540, 350),
            (760, 388), (LARGURA_TELA, 390),
        ]
        for repeticao in range(2):
            offset_x = -int(self.deslocamento_dunas) + repeticao * LARGURA_TELA
            pontos = [(px + offset_x, py) for px, py in picos_dunas]
            poligono = [(offset_x, self.y_chao)] + pontos + [(offset_x + LARGURA_TELA, self.y_chao)]
            pygame.draw.polygon(tela, cor_duna, poligono)

        self.grupo_nuvens.draw(tela)

        # Solo do deserto
        cor_areia = interpolar_cor((242, 208, 139), (92, 82, 112), noite)
        cor_borda_solo = interpolar_cor((156, 112, 68), (50, 44, 68), noite)
        cor_pedrinha = interpolar_cor((192, 148, 92), (66, 58, 86), noite)

        pygame.draw.rect(
            tela,
            cor_areia,
            pygame.Rect(0, self.y_chao, LARGURA_TELA, ALTURA_TELA - self.y_chao),
        )
        pygame.draw.line(tela, cor_borda_solo, (0, self.y_chao), (LARGURA_TELA, self.y_chao), 4)

        for px, py_rel, larg, alt in self.detalhes_chao:
            x_tela = int((px - self.deslocamento_chao) % LARGURA_TELA)
            pygame.draw.rect(
                tela,
                cor_pedrinha,
                pygame.Rect(x_tela, self.y_chao + py_rel, larg, alt),
            )

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.tema == TEMA_CLASSICO:
            self._desenhar_tema_classico(tela)
        else:
            self._desenhar_tema_colorido(tela)


# ==============================================================================
# ETAPA 3: CACTOS SURGINDO (Objetos, aleatoriedade, colisões)
# ETAPA 5: PTERODÁCTILOS E AGACHAR (Herança/composição, hitboxes)
# ==============================================================================
PALETAS_CACTO: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    TEMA_COLORIDO: {
        "V": (36, 138, 61),
        "E": (22, 89, 38),
        "C": (112, 204, 110),
    },
    TEMA_CLASSICO: {
        "V": COR_CLASSICO_ESCURA,
        "E": COR_CLASSICO_ESCURA,
        "C": COR_CLASSICO_ESCURA,
    },
}

# Cacto saguaro simples (com braços laterais em alturas diferentes)
GRADE_CACTO_SAGUARO_SIMPLES = [
    ".....EE.....",
    "....EVVE....",
    ".EE.EVVE....",
    "EVV.EVVE.EE.",
    "EVV.EVCE.VVE",
    "EVV.EVCE.VVE",
    "EVVEEVCE.VVE",
    ".EEVVVCEEVVE",
    "...EVVCEVVE.",
    "....EVCEEE..",
    "....EVCE....",
    "....EVVE....",
    "....EVVE....",
    "...EEVVEE...",
    "...EEEEEE...",
]

# Grupos de 2 e 3 cactos saguaro de tamanhos diferentes
GRADES_GRUPOS_SAGUARO = [
    # Grupo de 3 cactos saguaro (médio, alto e baixo)
    [
        ".............EE.............",
        "............EVVE............",
        "....EE......EVVE..EE........",
        "...EVVE..EE.EVCE.EVVE.......",
        ".E.EVVE.EVV.EVCE.EVVE....EE.",
        "EV.EVCE.EVV.EVCE.EVVE.E.EVVE",
        "EVEEVCE.EVVEEVCEEVVEE.V.EVCE",
        ".EEVVCEE.EEVVVCEVVEE..VEEVCE",
        "...EVVCE...EVVCE..E...EEVVCE",
        "...EVCE....EVCE........EVCE.",
        "...EVCE....EVCE........EVCE.",
        "...EVVE....EVVE........EVVE.",
        "...EVVE....EVVE........EVVE.",
        "..EEVVEE..EEVVEE......EEVVEE",
        "..EEEEEE..EEEEEE......EEEEEE",
    ],
    # Grupo de 2 cactos saguaro de alturas diferentes
    [
        ".....EE.............",
        "....EVVE............",
        ".EE.EVVE......EE....",
        "EVV.EVCE.EE..EVVE...",
        "EVV.EVCE.VVE.EVCE.EE",
        "EVVEEVCE.VVE.EVCE.VV",
        ".EEVVVCEEVVEEEVCE.VV",
        "...EVVCEVVEE.VVCEEVV",
        "....EVCEEE...EVVCEEE",
        "....EVCE......EVCE..",
        "....EVCE......EVCE..",
        "....EVVE......EVVE..",
        "....EVVE......EVVE..",
        "...EEVVEE....EEVVEE.",
        "...EEEEEE....EEEEEE.",
    ],
]

PALETAS_PTERO: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    TEMA_COLORIDO: {
        "R": (132, 76, 168),
        "E": (78, 40, 108),
        "C": (188, 138, 222),
        "B": (245, 190, 66),
        "O": (255, 255, 255),
    },
    TEMA_CLASSICO: {
        "R": COR_CLASSICO_ESCURA,
        "E": COR_CLASSICO_ESCURA,
        "C": COR_CLASSICO_ESCURA,
        "B": COR_CLASSICO_ESCURA,
        "O": COR_CLASSICO_FUNDO,
    },
}

GRADES_PTERODACTILO = [
    [
        "........EE......",
        ".......ERCE.....",
        "......ERRRCE....",
        "..EEE.ERRRRE....",
        "BBBBEEERRRRRE...",
        ".BBBEORRRRRRREEE",
        "....EEEEEEEEEEEE",
        "................",
        "................",
    ],
    [
        "................",
        "................",
        "..EEE...........",
        "BBBBEEE.........",
        ".BBBEORRRRRRREEE",
        "....EEERRRRRRE..",
        "......ERRRCE....",
        ".......ERCE.....",
        "........EE......",
    ],
]


class Obstaculo(pygame.sprite.Sprite):
    """Classe base para todos os obstáculos do jogo (Etapas 3 e 5)."""

    def __init__(
        self,
        x: float,
        y_base: int,
        margem_hitbox: Tuple[int, int] = (-14, -10),
        tema: str = TEMA_COLORIDO,
    ) -> None:
        super().__init__()
        self.pos_x = float(x)
        self.y_base = y_base
        self.margem_hitbox = margem_hitbox
        self.tema = tema
        self.tipo = "obstaculo"
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(int(self.pos_x), self.y_base))

    def definir_tema(self, novo_tema: str) -> None:
        self.tema = novo_tema

    @property
    def hitbox(self) -> pygame.Rect:
        return self.rect.inflate(*self.margem_hitbox)

    def update(self, dt: float, velocidade_mundo: float) -> None:
        self.pos_x -= velocidade_mundo * dt
        self.rect.x = int(round(self.pos_x))
        if self.rect.right < -40:
            self.kill()


class CactoSimples(Obstaculo):
    """Cacto saguaro individual."""

    def __init__(self, x: float, y_chao: int = Y_CHAO, escala: int = 3, tema: str = TEMA_COLORIDO) -> None:
        super().__init__(x, y_chao, margem_hitbox=(-10, -8), tema=tema)
        self.tipo = "cacto_simples"
        self.imagens = {
            t: criar_superficie_pixel_art(GRADE_CACTO_SAGUARO_SIMPLES, pal, escala)
            for t, pal in PALETAS_CACTO.items()
        }
        self.image = self.imagens[self.tema]
        self.rect = self.image.get_rect(midbottom=(int(self.pos_x), self.y_base))

    def definir_tema(self, novo_tema: str) -> None:
        super().definir_tema(novo_tema)
        pos_x_atual = self.rect.x
        self.image = self.imagens[self.tema]
        self.rect = self.image.get_rect(midbottom=(pos_x_atual + self.image.get_width() // 2, self.y_base))


class GrupoCactos(Obstaculo):
    """Agrupamento de 2 a 3 cactos saguaro de tamanhos diferentes."""

    def __init__(
        self,
        x: float,
        y_chao: int = Y_CHAO,
        escala: int = 3,
        variante: Optional[int] = None,
        tema: str = TEMA_COLORIDO,
    ) -> None:
        super().__init__(x, y_chao, margem_hitbox=(-14, -8), tema=tema)
        self.tipo = "grupo_cactos"
        indice = variante if variante is not None else random.randint(0, len(GRADES_GRUPOS_SAGUARO) - 1)
        grade = GRADES_GRUPOS_SAGUARO[indice % len(GRADES_GRUPOS_SAGUARO)]
        self.imagens = {
            t: criar_superficie_pixel_art(grade, pal, escala)
            for t, pal in PALETAS_CACTO.items()
        }
        self.image = self.imagens[self.tema]
        self.rect = self.image.get_rect(midbottom=(int(self.pos_x), self.y_base))

    def definir_tema(self, novo_tema: str) -> None:
        super().definir_tema(novo_tema)
        pos_x_atual = self.rect.x
        self.image = self.imagens[self.tema]
        self.rect = self.image.get_rect(midbottom=(pos_x_atual + self.image.get_width() // 2, self.y_base))


class Pterodactilo(Obstaculo):
    """Obstáculo voador animado em várias alturas (Etapa 5)."""

    ALTURAS = {
        "baixo": Y_CHAO - 14,
        "medio": Y_CHAO - 40,
        "alto": Y_CHAO - 84,
    }

    def __init__(
        self,
        x: float,
        nivel_altura: str = "medio",
        escala: int = 4,
        tema: str = TEMA_COLORIDO,
    ) -> None:
        y_base = self.ALTURAS.get(nivel_altura, self.ALTURAS["medio"])
        super().__init__(x, y_base, margem_hitbox=(-14, -10), tema=tema)
        self.tipo = f"pterodactilo_{nivel_altura}"
        self.nivel_altura = nivel_altura
        self.quadros_por_tema = {
            t: [criar_superficie_pixel_art(grade, pal, escala) for grade in GRADES_PTERODACTILO]
            for t, pal in PALETAS_PTERO.items()
        }
        self.indice_quadro = 0
        self.tempo_animacao = 0.0
        self.image = self.quadros_por_tema[self.tema][0]
        self.rect = self.image.get_rect(midbottom=(int(self.pos_x), self.y_base))

    def definir_tema(self, novo_tema: str) -> None:
        super().definir_tema(novo_tema)
        self.image = self.quadros_por_tema[self.tema][self.indice_quadro]

    def update(self, dt: float, velocidade_mundo: float) -> None:
        self.pos_x -= (velocidade_mundo * 1.08) * dt
        self.tempo_animacao += dt
        if self.tempo_animacao >= 0.14:
            self.tempo_animacao = 0.0
            self.indice_quadro = (self.indice_quadro + 1) % 2
            self.image = self.quadros_por_tema[self.tema][self.indice_quadro]
        self.rect.x = int(round(self.pos_x))
        if self.rect.right < -40:
            self.kill()


class GeradorObstaculos:
    """
    Controla o surgimento de obstáculos respeitando a velocidade atual para
    garantir que nunca existam combinações impossíveis (sempre há espaço para pousar).
    """

    def __init__(self, modo_demo: bool = False, tema: str = TEMA_COLORIDO) -> None:
        self.modo_demo = modo_demo
        self.tema = tema
        self.distancia_ate_proximo = 260.0
        self.indice_roteiro_demo = 0

    def definir_tema(self, novo_tema: str) -> None:
        self.tema = novo_tema

    def reiniciar(self) -> None:
        self.distancia_ate_proximo = 240.0 if self.modo_demo else 320.0
        self.indice_roteiro_demo = 0

    def calcular_espacamento_seguro(self, velocidade_atual: float) -> float:
        duracao_pulo = (2.0 * abs(IMPULSO_PULO)) / GRAVIDADE
        distancia_pulo = velocidade_atual * duracao_pulo
        margem_seguranca = 140.0 + (velocidade_atual - VELOCIDADE_INICIAL) * 0.30
        minimo = distancia_pulo + margem_seguranca
        maximo = minimo + random.uniform(110.0, 290.0)
        return random.uniform(minimo, maximo)

    def atualizar(
        self,
        dt: float,
        velocidade_atual: float,
        tempo_decorrido: float,
        grupo_obstaculos: pygame.sprite.Group,
    ) -> None:
        self.distancia_ate_proximo -= velocidade_atual * dt

        if grupo_obstaculos:
            maior_x = max(obs.rect.right for obs in grupo_obstaculos)
            if LARGURA_TELA - maior_x < 260:
                return

        if self.distancia_ate_proximo <= 0.0:
            x_spawn = float(LARGURA_TELA + 40)
            novo = self._escolher_obstaculo(x_spawn, tempo_decorrido)
            grupo_obstaculos.add(novo)
            if self.modo_demo:
                self.distancia_ate_proximo = 330.0
            else:
                self.distancia_ate_proximo = self.calcular_espacamento_seguro(velocidade_atual)

    def _escolher_obstaculo(self, x_spawn: float, tempo_decorrido: float) -> Obstaculo:
        if self.modo_demo:
            sequencia_demo = [
                lambda: GrupoCactos(x_spawn, variante=0, tema=self.tema),
                lambda: CactoSimples(x_spawn, tema=self.tema),
                lambda: Pterodactilo(x_spawn, "medio", tema=self.tema),
                lambda: GrupoCactos(x_spawn, variante=1, tema=self.tema),
            ]
            fabrica = sequencia_demo[self.indice_roteiro_demo % len(sequencia_demo)]
            self.indice_roteiro_demo += 1
            return fabrica()

        if tempo_decorrido < 8.0:
            return CactoSimples(x_spawn, tema=self.tema)
        if tempo_decorrido < 18.0:
            return random.choice([
                CactoSimples(x_spawn, tema=self.tema),
                GrupoCactos(x_spawn, tema=self.tema),
            ])

        sorteio = random.random()
        if sorteio < 0.42:
            return CactoSimples(x_spawn, tema=self.tema)
        if sorteio < 0.72:
            return GrupoCactos(x_spawn, tema=self.tema)
        altura = random.choice(["baixo", "medio", "medio", "alto"])
        return Pterodactilo(x_spawn, altura, tema=self.tema)


# ==============================================================================
# ETAPA 4: PONTUAÇÃO E GAME OVER (Condicionais, estados, persistência)
# ==============================================================================
ESTADO_TITULO = "TITULO"
ESTADO_JOGANDO = "JOGANDO"
ESTADO_PAUSA = "PAUSA"
ESTADO_GAMEOVER = "GAMEOVER"


def carregar_recorde() -> int:
    """Lê o recorde salvo em recorde.json ao lado de main.py."""
    try:
        if ARQUIVO_RECORDE.exists():
            dados = json.loads(ARQUIVO_RECORDE.read_text(encoding="utf-8"))
            return int(dados.get("recorde", 0))
    except Exception:
        pass
    return 0


def salvar_recorde(novo_recorde: int) -> None:
    """Salva o recorde atualizado em recorde.json ao lado de main.py."""
    try:
        ARQUIVO_RECORDE.write_text(
            json.dumps({"recorde": int(novo_recorde)}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


# ==============================================================================
# ETAPA 6: MÚSICA, EFEITOS E POLIMENTO (Áudio sem numpy, partículas, temas)
# ==============================================================================
class SintetizadorAudio:
    """
    Gera efeitos sonoros retrô em memória (PCM 16-bit mono, 22050 Hz) sem usar numpy,
    carregando-os via pygame.mixer.Sound(buffer=...).
    Falha silenciosamente se não houver dispositivo de áudio disponível.
    """

    TAXA_AMOSTRAGEM = 22050

    def __init__(self) -> None:
        self.ativo = False
        self.som_pulo: Optional[pygame.mixer.Sound] = None
        self.som_colisao: Optional[pygame.mixer.Sound] = None
        self.som_marco: Optional[pygame.mixer.Sound] = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.TAXA_AMOSTRAGEM, size=-16, channels=1, buffer=512)
            self.som_pulo = self._criar_som_pulo()
            self.som_colisao = self._criar_som_colisao()
            self.som_marco = self._criar_som_marco()
            self.ativo = True
        except Exception:
            self.ativo = False

    def _gerar_buffer_pcm(self, amostras_float: Sequence[float]) -> bytes:
        pacotes = [
            struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767))
            for v in amostras_float
        ]
        return b"".join(pacotes)

    def _criar_som_pulo(self) -> pygame.mixer.Sound:
        duracao = 0.14
        total = int(self.TAXA_AMOSTRAGEM * duracao)
        amostras: List[float] = []
        fase = 0.0
        for i in range(total):
            progresso = i / total
            freq = 280.0 + 420.0 * (progresso ** 1.2)
            fase += (2.0 * math.pi * freq) / self.TAXA_AMOSTRAGEM
            envelope = (1.0 - progresso) * 0.35
            onda = 1.0 if math.sin(fase) >= 0 else -1.0
            amostras.append(onda * envelope)
        return pygame.mixer.Sound(buffer=self._gerar_buffer_pcm(amostras))

    def _criar_som_colisao(self) -> pygame.mixer.Sound:
        duracao = 0.28
        total = int(self.TAXA_AMOSTRAGEM * duracao)
        rng = random.Random(101)
        amostras: List[float] = []
        fase = 0.0
        for i in range(total):
            progresso = i / total
            freq = 190.0 - 130.0 * progresso
            fase += (2.0 * math.pi * freq) / self.TAXA_AMOSTRAGEM
            ruido = rng.uniform(-1.0, 1.0) * 0.5 + math.sin(fase) * 0.5
            envelope = (1.0 - progresso) * 0.45
            amostras.append(ruido * envelope)
        return pygame.mixer.Sound(buffer=self._gerar_buffer_pcm(amostras))

    def _criar_som_marco(self) -> pygame.mixer.Sound:
        duracao = 0.24
        total = int(self.TAXA_AMOSTRAGEM * duracao)
        amostras: List[float] = []
        fase = 0.0
        for i in range(total):
            progresso = i / total
            freq = 660.0 if progresso < 0.45 else 880.0
            fase += (2.0 * math.pi * freq) / self.TAXA_AMOSTRAGEM
            envelope = 0.32 * (1.0 - (progresso % 0.5))
            amostras.append(math.sin(fase) * envelope)
        return pygame.mixer.Sound(buffer=self._gerar_buffer_pcm(amostras))

    def tocar(self, som: Optional[pygame.mixer.Sound]) -> None:
        if not self.ativo or som is None:
            return
        try:
            som.play()
        except Exception:
            pass


class ParticulaPoeira:
    """Partícula de poeira levantada pelos passos e pelo pouso do dinossauro."""

    def __init__(self, x: float, y: float, vx: float, vy: float, tamanho: int) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.tamanho = tamanho
        self.vida = 1.0

    def atualizar(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vida -= dt * 2.6
        return self.vida > 0.0

    def desenhar(self, tela: pygame.Surface, tema: str) -> None:
        tam = max(2, int(self.tamanho * self.vida))
        if tema == TEMA_CLASSICO:
            cor = COR_CLASSICO_ESCURA if self.tamanho % 2 == 0 else (160, 160, 160)
        else:
            cor = (176, 134, 82) if self.tamanho % 2 == 0 else (250, 232, 190)
        pygame.draw.rect(tela, cor, pygame.Rect(int(self.x), int(self.y), tam, tam))


# ==============================================================================
# CONTROLADOR PRINCIPAL DO JOGO E MODO DEMO
# ==============================================================================
class JogoDinoRunner:
    """Integra as 6 etapas do projeto, alternância de temas e o modo --demo."""

    def __init__(self, modo_demo: bool = False, iniciar_classico: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("Dino Runner — Versão de Aula (Pygame-CE)")
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        self.relogio = pygame.time.Clock()
        self.modo_demo = modo_demo
        self.tema_atual = TEMA_CLASSICO if iniciar_classico else TEMA_COLORIDO

        # Fontes para telas de título, pausa e game over
        self.fonte_titulo = pygame.font.SysFont("monospace", 42, bold=True)
        self.fonte_texto = pygame.font.SysFont("monospace", 17, bold=True)

        # Entidades e subsistemas
        self.audio = SintetizadorAudio()
        self.cenario = CenarioDeserto(Y_CHAO, tema=self.tema_atual)
        self.dino = Dinossauro(X_FIXO_DINO, Y_CHAO, tema=self.tema_atual)
        self.grupo_dino = pygame.sprite.GroupSingle(self.dino)
        self.grupo_obstaculos = pygame.sprite.Group()
        self.gerador = GeradorObstaculos(modo_demo=self.modo_demo, tema=self.tema_atual)
        self.particulas: List[ParticulaPoeira] = []

        # Estado e pontuação
        self.estado = ESTADO_TITULO
        self.velocidade_mundo = VELOCIDADE_INICIAL
        self.tempo_jogando = 0.0
        self.distancia_percorrida = 0.0
        self.pontuacao = 0
        self.ultimo_marco_100 = 0
        self.recorde = carregar_recorde()
        self.tempo_acumulado_poeira = 0.0

        # Controle específico do modo --demo (4 prints: titulo, jogo, classico, gameover)
        self.tempo_demo_estado = 0.0
        self.print_titulo_salvo = False
        self.print_jogo_salvo = False
        self.print_classico_salvo = False
        self.print_gameover_salvo = False
        self.forcar_colisao_demo = False
        if self.modo_demo:
            PASTA_PRINTS.mkdir(parents=True, exist_ok=True)

    def definir_tema(self, novo_tema: str) -> None:
        """Aplica imediatamente o tema ('colorido' ou 'classico') a todo o jogo."""
        self.tema_atual = novo_tema
        self.cenario.definir_tema(novo_tema)
        self.dino.definir_tema(novo_tema)
        self.gerador.definir_tema(novo_tema)
        for obstaculo in self.grupo_obstaculos:
            if hasattr(obstaculo, "definir_tema"):
                obstaculo.definir_tema(novo_tema)

    def alternar_tema(self) -> None:
        """Alterna entre o tema colorido e o tema clássico (tecla T)."""
        proximo = TEMA_CLASSICO if self.tema_atual == TEMA_COLORIDO else TEMA_COLORIDO
        self.definir_tema(proximo)

    def iniciar_nova_partida(self) -> None:
        """Prepara uma nova corrida a partir do zero."""
        self.dino.reiniciar()
        self.grupo_obstaculos.empty()
        self.gerador.reiniciar()
        self.particulas.clear()
        self.velocidade_mundo = VELOCIDADE_INICIAL
        self.tempo_jogando = 0.0
        self.distancia_percorrida = 0.0
        self.pontuacao = 0
        self.ultimo_marco_100 = 0
        self.estado = ESTADO_JOGANDO
        self.tempo_demo_estado = 0.0
        self.forcar_colisao_demo = False

        if self.modo_demo:
            self.grupo_obstaculos.add(CactoSimples(460, tema=self.tema_atual))
            self.grupo_obstaculos.add(Pterodactilo(780, "medio", tema=self.tema_atual))
            self.gerador.distancia_ate_proximo = 320.0

    def emitir_poeira_corrida(self, dt: float) -> None:
        if not self.dino.no_chao or self.dino.bateu:
            return
        self.tempo_acumulado_poeira += dt
        if self.tempo_acumulado_poeira >= 0.08:
            self.tempo_acumulado_poeira = 0.0
            px = float(self.dino.rect.left + 8)
            py = float(self.dino.rect.bottom - 5)
            vx = -self.velocidade_mundo * 0.45 + random.uniform(-25.0, 10.0)
            vy = random.uniform(-45.0, -12.0)
            self.particulas.append(ParticulaPoeira(px, py, vx, vy, random.randint(4, 7)))

    def emitir_poeira_pouso(self) -> None:
        for _ in range(10):
            px = float(self.dino.rect.centerx + random.randint(-14, 14))
            py = float(self.dino.rect.bottom - 4)
            vx = -self.velocidade_mundo * 0.35 + random.uniform(-90.0, 70.0)
            vy = random.uniform(-95.0, -20.0)
            self.particulas.append(ParticulaPoeira(px, py, vx, vy, random.randint(5, 8)))

    def atualizar_piloto_automatico_demo(self) -> None:
        """IA do modo --demo: pula cactos e agacha sob pterodáctilos médios."""
        if self.forcar_colisao_demo:
            self.dino.definir_abaixado(False)
            return

        candidatos = [
            obs for obs in self.grupo_obstaculos
            if obs.rect.right > self.dino.rect.left + 6
        ]
        if not candidatos:
            self.dino.definir_abaixado(False)
            return

        proximo = min(candidatos, key=lambda o: o.rect.left)
        distancia_x = proximo.rect.left - self.dino.rect.right

        if isinstance(proximo, Pterodactilo) and proximo.nivel_altura == "medio":
            if distancia_x < 170:
                self.dino.definir_abaixado(True)
            else:
                self.dino.definir_abaixado(False)
        elif isinstance(proximo, Pterodactilo) and proximo.nivel_altura == "alto":
            self.dino.definir_abaixado(False)
        else:
            self.dino.definir_abaixado(False)
            alcance_pulo = 88 + (self.velocidade_mundo - VELOCIDADE_INICIAL) * 0.20
            if 0 <= distancia_x <= alcance_pulo:
                if self.dino.pular():
                    self.audio.tocar(self.audio.som_pulo)

    def atualizar_jogo(self, dt: float) -> None:
        self.tempo_jogando += dt

        escaloes = int(self.tempo_jogando // INTERVALO_INCREMENTO)
        self.velocidade_mundo = min(
            VELOCIDADE_MAXIMA,
            VELOCIDADE_INICIAL + escaloes * INCREMENTO_VELOCIDADE,
        )

        if self.modo_demo:
            self.atualizar_piloto_automatico_demo()

        self.cenario.atualizar(dt, self.velocidade_mundo)
        self.dino.update(dt)
        if self.dino.acabou_de_pousar:
            self.emitir_poeira_pouso()
        self.emitir_poeira_corrida(dt)

        self.gerador.atualizar(dt, self.velocidade_mundo, self.tempo_jogando, self.grupo_obstaculos)
        self.grupo_obstaculos.update(dt, self.velocidade_mundo)

        self.particulas = [p for p in self.particulas if p.atualizar(dt)]

        self.distancia_percorrida += self.velocidade_mundo * dt
        self.pontuacao = int(self.distancia_percorrida * 0.05)

        marco_atual = self.pontuacao // 100
        if marco_atual > self.ultimo_marco_100 and self.pontuacao > 0:
            self.ultimo_marco_100 = marco_atual
            self.audio.tocar(self.audio.som_marco)

        hitbox_dino = self.dino.hitbox
        for obstaculo in self.grupo_obstaculos:
            if hitbox_dino.colliderect(obstaculo.hitbox):
                self.registrar_game_over()
                break

    def registrar_game_over(self) -> None:
        if self.modo_demo:
            if not self.print_jogo_salvo:
                pygame.image.save(self.tela, str(PASTA_PRINTS / "jogo.png"))
                self.print_jogo_salvo = True
            if not self.print_classico_salvo:
                tema_anterior = self.tema_atual
                self.definir_tema(TEMA_CLASSICO)
                self.desenhar()
                pygame.image.save(self.tela, str(PASTA_PRINTS / "classico.png"))
                self.print_classico_salvo = True
                self.definir_tema(tema_anterior)

        self.dino.bateu = True
        self.dino.update(0.0)
        self.audio.tocar(self.audio.som_colisao)
        if self.pontuacao > self.recorde:
            self.recorde = self.pontuacao
            salvar_recorde(self.recorde)
        self.estado = ESTADO_GAMEOVER
        self.tempo_demo_estado = 0.0

    def desenhar_hud(self) -> None:
        """
        Desenha a HUD no canto superior direito no formato exato 'HI 000849  000660'
        (6 dígitos com zeros à esquerda, fonte pixel em negrito).
        """
        texto_hud = f"HI {self.recorde:06d}  {self.pontuacao:06d}"
        if self.tema_atual == TEMA_CLASSICO:
            surf_hud = renderizar_texto_pixel_negrito(texto_hud, COR_CLASSICO_ESCURA, escala=3)
        else:
            surf_hud = renderizar_texto_pixel_negrito(
                texto_hud,
                (255, 255, 255),
                escala=3,
                cor_sombra=(30, 30, 42),
            )
        pos_x = LARGURA_TELA - surf_hud.get_width() - 24
        pos_y = 20
        self.tela.blit(surf_hud, (pos_x, pos_y))

    def desenhar_painel_central(
        self,
        titulo: str,
        linhas: Sequence[str],
        cor_titulo: Tuple[int, int, int],
    ) -> None:
        largura_caixa = 740
        altura_caixa = 250
        x_caixa = (LARGURA_TELA - largura_caixa) // 2
        y_caixa = (ALTURA_TELA - altura_caixa) // 2 - 20

        painel = pygame.Surface((largura_caixa, altura_caixa), pygame.SRCALPHA)
        if self.tema_atual == TEMA_CLASSICO:
            pygame.draw.rect(painel, (255, 255, 255, 238), painel.get_rect(), border_radius=8)
            pygame.draw.rect(painel, COR_CLASSICO_ESCURA, painel.get_rect(), 3, border_radius=8)
            cor_titulo_efetiva = COR_CLASSICO_ESCURA
            cor_texto = COR_CLASSICO_ESCURA
        else:
            pygame.draw.rect(painel, (22, 26, 38, 222), painel.get_rect(), border_radius=12)
            pygame.draw.rect(painel, (240, 210, 130), painel.get_rect(), 3, border_radius=12)
            cor_titulo_efetiva = cor_titulo
            cor_texto = (240, 240, 245)

        self.tela.blit(painel, (x_caixa, y_caixa))

        surf_titulo = self.fonte_titulo.render(titulo, True, cor_titulo_efetiva)
        self.tela.blit(
            surf_titulo,
            (LARGURA_TELA // 2 - surf_titulo.get_width() // 2, y_caixa + 20),
        )

        y_texto = y_caixa + 84
        for linha in linhas:
            surf_linha = self.fonte_texto.render(linha, True, cor_texto)
            self.tela.blit(
                surf_linha,
                (LARGURA_TELA // 2 - surf_linha.get_width() // 2, y_texto),
            )
            y_texto += 29

    def desenhar(self) -> None:
        self.cenario.desenhar(self.tela)

        for particula in self.particulas:
            particula.desenhar(self.tela, self.tema_atual)

        self.grupo_obstaculos.draw(self.tela)
        self.grupo_dino.draw(self.tela)
        self.desenhar_hud()

        nome_tema = "Clássico (Chrome)" if self.tema_atual == TEMA_CLASSICO else "Deserto Colorido"

        if self.estado == ESTADO_TITULO:
            self.desenhar_painel_central(
                "DINO RUNNER",
                [
                    "Pressione [ESPAÇO] ou [SETA PARA CIMA] para correr e pular",
                    "Segure [SETA PARA BAIXO] para agachar sob pterodáctilos",
                    f"Pressione [T] para alternar tema (Atual: {nome_tema})",
                    "Pressione [P] ou [ESC] para pausar a partida",
                    f"Recorde atual: {self.recorde:06d} pontos",
                ],
                (143, 224, 130),
            )
        elif self.estado == ESTADO_PAUSA:
            self.desenhar_painel_central(
                "JOGO PAUSADO",
                [
                    "Pressione [P] ou [ESC] para continuar",
                    "Pressione [ESPAÇO] para retomar a corrida",
                ],
                (255, 220, 105),
            )
        elif self.estado == ESTADO_GAMEOVER:
            self.desenhar_painel_central(
                "FIM DE JOGO!",
                [
                    f"Pontuação final: {self.pontuacao:06d}  |  Recorde (HI): {self.recorde:06d}",
                    "Pressione [ESPAÇO], [R] ou [ENTER] para jogar novamente",
                    "Pressione [T] para alternar tema  |  [ESC] para sair",
                ],
                (255, 105, 95),
            )

        pygame.display.flip()

    def processar_eventos(self) -> bool:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_t and self.estado in (ESTADO_TITULO, ESTADO_GAMEOVER, ESTADO_PAUSA):
                    self.alternar_tema()
                    continue

                if self.estado == ESTADO_TITULO:
                    if evento.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN):
                        self.iniciar_nova_partida()
                        if self.dino.pular():
                            self.audio.tocar(self.audio.som_pulo)
                    elif evento.key == pygame.K_ESCAPE:
                        return False

                elif self.estado == ESTADO_JOGANDO:
                    if evento.key in (pygame.K_SPACE, pygame.K_UP):
                        if self.dino.pular():
                            self.audio.tocar(self.audio.som_pulo)
                    elif evento.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.estado = ESTADO_PAUSA
                    elif evento.key == pygame.K_t:
                        self.alternar_tema()

                elif self.estado == ESTADO_PAUSA:
                    if evento.key in (pygame.K_p, pygame.K_ESCAPE, pygame.K_SPACE):
                        self.estado = ESTADO_JOGANDO

                elif self.estado == ESTADO_GAMEOVER:
                    if evento.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_r, pygame.K_RETURN):
                        self.iniciar_nova_partida()
                    elif evento.key == pygame.K_ESCAPE:
                        return False

        if self.estado == ESTADO_JOGANDO and not self.modo_demo:
            teclas = pygame.key.get_pressed()
            self.dino.definir_abaixado(bool(teclas[pygame.K_DOWN]))

        return True

    def gerenciar_fluxo_demo(self, dt: float) -> bool:
        """
        Coordena a transição automática de estados no modo `--demo` (< 12s),
        salvando as 4 capturas exigidas em `prints/`:
          1. `prints/titulo.png`
          2. `prints/jogo.png` (tema colorido em ação)
          3. `prints/classico.png` (tema clássico estilo Chrome Dino em ação)
          4. `prints/gameover.png`
        """
        self.tempo_demo_estado += dt

        if self.estado == ESTADO_TITULO:
            if not self.print_titulo_salvo and self.tempo_demo_estado >= 0.15:
                pygame.image.save(self.tela, str(PASTA_PRINTS / "titulo.png"))
                self.print_titulo_salvo = True
            if self.tempo_demo_estado >= 0.35:
                self.iniciar_nova_partida()

        elif self.estado == ESTADO_JOGANDO:
            # 1) Em ~0.95s salva o print do jogo em ação no tema colorido
            if not self.print_jogo_salvo and self.tempo_demo_estado >= 0.95:
                if self.tema_atual != TEMA_COLORIDO:
                    self.definir_tema(TEMA_COLORIDO)
                    self.desenhar()
                pygame.image.save(self.tela, str(PASTA_PRINTS / "jogo.png"))
                self.print_jogo_salvo = True

            # 2) Em ~2.1s alterna para o tema clássico e salva prints/classico.png
            if not self.print_classico_salvo and self.tempo_demo_estado >= 2.10:
                self.definir_tema(TEMA_CLASSICO)
                self.desenhar()
                pygame.image.save(self.tela, str(PASTA_PRINTS / "classico.png"))
                self.print_classico_salvo = True

            # 3) Em ~3.1s prepara colisão para demonstrar tela de Game Over
            if self.tempo_demo_estado >= 3.10 and not self.forcar_colisao_demo:
                self.forcar_colisao_demo = True
                obstaculo_perto = any(
                    self.dino.rect.right < obs.rect.left < self.dino.rect.right + 180
                    for obs in self.grupo_obstaculos
                )
                if not obstaculo_perto:
                    self.grupo_obstaculos.add(CactoSimples(self.dino.rect.right + 90, tema=self.tema_atual))

            # Fallback de segurança caso ainda não tenha colidido até 4.6s
            if self.tempo_demo_estado >= 4.60 and self.estado == ESTADO_JOGANDO:
                self.registrar_game_over()

        elif self.estado == ESTADO_GAMEOVER:
            if not self.print_gameover_salvo and self.tempo_demo_estado >= 0.15:
                pygame.image.save(self.tela, str(PASTA_PRINTS / "gameover.png"))
                self.print_gameover_salvo = True
            if self.print_gameover_salvo and self.tempo_demo_estado >= 0.35:
                return False

        return True

    def executar(self) -> None:
        rodando = True
        while rodando:
            dt_real = self.relogio.tick(FPS_ALVO) / 1000.0
            dt = min(dt_real if dt_real > 0 else (1.0 / FPS_ALVO), 0.05)

            rodando = self.processar_eventos()
            if not rodando:
                break

            if self.estado == ESTADO_JOGANDO:
                self.atualizar_jogo(dt)
            elif self.estado == ESTADO_TITULO:
                self.cenario.grupo_nuvens.update(dt, 90.0)

            self.desenhar()

            if self.modo_demo:
                if not self.gerenciar_fluxo_demo(dt):
                    break

        pygame.quit()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dino Runner em Pygame-CE (Versão de Aula em Português)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Executa piloto automático, salva capturas em prints/ e encerra sozinho.",
    )
    parser.add_argument(
        "--classico",
        action="store_true",
        help="Inicia o jogo diretamente no tema clássico (estilo Chrome Dino #535353).",
    )
    args = parser.parse_args()

    jogo = JogoDinoRunner(modo_demo=args.demo, iniciar_classico=args.classico)
    jogo.executar()
    return 0


if __name__ == "__main__":
    sys.exit(main())

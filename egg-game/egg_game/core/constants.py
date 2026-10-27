# -*- coding: utf-8 -*-
"""Constantes físicas, geométricas e de configuração do núcleo do jogo."""

from __future__ import annotations

# Resolução lógica 9:16 (retrato)
LOGICAL_W: int = 720
LOGICAL_H: int = 1280
CENTER_X: float = LOGICAL_W / 2.0

# Coordenadas verticais de referência no mundo (eixo Y cresce para baixo)
START_WORLD_Y: float = 1020.0
PIXELS_PER_METER: float = 100.0
NEST_HEIGHT_M: int = 120
NEST_WORLD_Y: float = START_WORLD_Y - (NEST_HEIGHT_M * PIXELS_PER_METER)

# Parâmetros de física (SPEC §0.2)
GRAVITY: float = 2400.0        # px/s²
JUMP_IMPULSE: float = -950.0   # px/s (para cima)
FIXED_DT: float = 1.0 / 120.0  # Passo fixo de simulação (120 Hz)
MAX_FALL_SPEED: float = 1400.0

# Altura máxima teórica de um pulo: v0² / (2 * g) ≈ 188.02 px
MAX_JUMP_HEIGHT_PX: float = (JUMP_IMPULSE ** 2) / (2.0 * GRAVITY)

# Parâmetros do gerador de cestas (SPEC §0.4)
MIN_DELTA_Y: float = 88.0
MAX_DELTA_Y: float = 136.0
PLAYABLE_MIN_X: float = 130.0
PLAYABLE_MAX_X: float = LOGICAL_W - 130.0
DEFAULT_BASKET_WIDTH: float = 136.0
NEST_WIDTH: float = 210.0
DEFAULT_SEED: int = 20261027

# Margem mínima de janela temporal de pouso para validar alcançabilidade (s)
MIN_TIMING_WINDOW_S: float = 0.14

# Paleta de cores de referência (PRD §14)
PALETA_CORES = {
    "creme": (255, 240, 214),
    "casca": (248, 232, 200),
    "gema": (245, 184, 61),
    "palha": (218, 168, 95),
    "madeira": (128, 81, 57),
    "madeira_escura": (88, 52, 34),
    "folhagem": (95, 153, 59),
    "folhagem_escura": (58, 108, 36),
    "folhagem_clara": (136, 194, 84),
    "ceu_topo": (88, 176, 232),
    "ceu_base": (182, 228, 250),
    "traco": (42, 37, 33),
}

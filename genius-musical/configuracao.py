# -*- coding: utf-8 -*-
"""Constantes e configurações do Genius Musical.

Centraliza todas as definições visuais, temporais, acústicas e dimensionais
do jogo, eliminando números mágicos espalhados pelo código.
"""

from __future__ import annotations

from pathlib import Path

# -----------------------------------------------------------------------------
# Janela e Taxa de Atualização
# -----------------------------------------------------------------------------
LARGURA = 960
ALTURA = 720
FPS = 60
MAX_DELTA_TIME = 0.033  # Limite máximo de dt (~30 FPS) para estabilidade

# -----------------------------------------------------------------------------
# Paleta de Cores Flat (Hex -> RGB)
# -----------------------------------------------------------------------------
# Cores de fundo e estrutura
FUNDO = (16, 24, 39)          # #101827 - Azul escuro profundo
PAINEL = (30, 41, 59)         # #1E293B - Slate escuro
PAINEL_CARD = (23, 33, 51)    # Cartão neutro
BORDA = (51, 65, 85)          # #334155 - Borda suave
BORDA_DESTAQUE = (255, 255, 255)  # Branco para realce ativo

# Tipografia
TEXTO = (248, 250, 252)       # #F8FAFC - Branco suave
TEXTO_SUAVE = (148, 163, 184) # #94A3B8 - Cinza azulado
TEXTO_ESCURO = (16, 24, 39)   # #101827 - Para contraste sobre cartões claros

# Elementos em estado NORMAL
FOGO = (248, 113, 113)        # #F87171 - Coral / Vermelho
AGUA = (96, 165, 250)         # #60A5FA - Azul celeste
TERRA = (74, 222, 128)        # #4ADE80 - Verde brilhante
AR = (250, 204, 21)           # #FACC15 - Amarelo vibrante

CORES_ELEMENTOS = {
    "fogo": FOGO,
    "agua": AGUA,
    "terra": TERRA,
    "ar": AR,
}

# Elementos em estado ATIVO (tom clareado para feedback luminoso flat)
CORES_ATIVAS = {
    "fogo": (254, 180, 180),  # Coral clareado
    "agua": (175, 215, 254),  # Azul clareado
    "terra": (160, 245, 195), # Verde clareado
    "ar": (255, 235, 140),    # Amarelo clareado
}

# Elementos em estado INDISPONÍVEL / DEMONSTRAÇÃO PASSIVA
CORES_INDISPONIVEIS = {
    "fogo": (160, 75, 75),
    "agua": (65, 110, 165),
    "terra": (50, 145, 85),
    "ar": (165, 135, 20),
}

# -----------------------------------------------------------------------------
# Elementos e Frequências Musicais (Acorde Dó Maior - C4, E4, G4, C5)
# -----------------------------------------------------------------------------
ELEMENTOS = ("fogo", "agua", "terra", "ar")

FREQUENCIAS = {
    "fogo": 261.63,  # Dó4 (C4)
    "agua": 329.63,  # Mi4 (E4)
    "terra": 392.00, # Sol4 (G4)
    "ar": 523.25,    # Dó5 (C5)
}

ROTULOS = {
    "fogo": "FOGO",
    "agua": "ÁGUA",
    "terra": "TERRA",
    "ar": "AR",
}

TECLAS_ROTULO = {
    "fogo": "1",
    "agua": "2",
    "terra": "3",
    "ar": "4",
}

# -----------------------------------------------------------------------------
# Parâmetros de Temporização (Milissegundos e Segundos)
# -----------------------------------------------------------------------------
TEMPO_DESTAQUE_MS = 450
INTERVALO_ENTRE_NOTAS_MS = 200
FEEDBACK_TOQUE_MS = 180
INTERVALO_PROXIMA_RODADA_MS = 800

TEMPO_DESTAQUE_S = TEMPO_DESTAQUE_MS / 1000.0
INTERVALO_ENTRE_NOTAS_S = INTERVALO_ENTRE_NOTAS_MS / 1000.0
FEEDBACK_TOQUE_S = FEEDBACK_TOQUE_MS / 1000.0
INTERVALO_PROXIMA_RODADA_S = INTERVALO_PROXIMA_RODADA_MS / 1000.0

# -----------------------------------------------------------------------------
# Síntese de Áudio (PCM Mono 16-bit com Envelope)
# -----------------------------------------------------------------------------
FS = 44100            # Taxa de amostragem padrão (44.1 kHz)
AMPLITUDE = 24000     # Amplitude máxima dentro dos limites int16 (-32768..32767)
DURACAO_NOTA_S = TEMPO_DESTAQUE_S  # 450 ms (compatível com tempo de destaque)
TEMPO_ATAQUE_S = 0.010    # 10 ms de fade-in
TEMPO_LIBERACAO_S = 0.030 # 30 ms de fade-out

# -----------------------------------------------------------------------------
# Caminhos de Arquivos (Imagens)
# -----------------------------------------------------------------------------
DIRETORIO_BASE = Path(__file__).resolve().parent
PASTA_ASSETS_IMAGENS = DIRETORIO_BASE / "assets" / "imagens"

CAMINHOS_IMAGENS = {
    elem: PASTA_ASSETS_IMAGENS / f"{elem}.png" for elem in ELEMENTOS
}

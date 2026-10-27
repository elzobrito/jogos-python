# -*- coding: utf-8 -*-
"""Módulo de áudio do Genius Musical: síntese PCM e reprodução de notas.

Gera em tempo de execução ondas senoidais amostradas em formato PCM mono 16-bit
com envelope linear de ataque e liberação, dispensando arquivos WAV ou MP3 externos.
"""

from __future__ import annotations

import math
from array import array
from typing import Dict, Optional

import pygame

from configuracao import (
    AMPLITUDE,
    DURACAO_NOTA_S,
    ELEMENTOS,
    FREQUENCIAS,
    FS,
    TEMPO_ATAQUE_S,
    TEMPO_LIBERACAO_S,
)


def sintetizar_nota(
    freq: float,
    duracao: float = DURACAO_NOTA_S,
    fs: int = FS,
    amplitude: float = AMPLITUDE,
    tempo_ataque: float = TEMPO_ATAQUE_S,
    tempo_liberacao: float = TEMPO_LIBERACAO_S,
) -> array:
    """Gera um buffer de áudio em formato PCM mono 16-bit com sinal (array 'h').

    Aplica um envelope linear de ataque (fade-in) e liberação (fade-out) para
    eliminar estalos acústicos (clicks) nas extremidades do sinal senoidal.

    Args:
        freq: Frequência em Hertz (ex: 261.63 para Dó4).
        duracao: Duração em segundos.
        fs: Taxa de amostragem em Hz (padrão 44100).
        amplitude: Amplitude de pico (máximo seguro 32767).
        tempo_ataque: Duração da rampa de ataque em segundos.
        tempo_liberacao: Duração da rampa de decaimento em segundos.

    Returns:
        Um array('h') contendo as amostras inteiras de 16 bits.
    """
    total_amostras = max(1, int(duracao * fs))
    amostras_ataque = max(1, int(tempo_ataque * fs))
    amostras_liberacao = max(1, int(tempo_liberacao * fs))

    # Prepara o buffer de amostras inteiras com sinal (-32768..32767)
    buffer = array("h")
    fator_angular = 2.0 * math.pi * freq / fs

    for i in range(total_amostras):
        # Cálculo do envelope linear
        if i < amostras_ataque:
            envelope = i / amostras_ataque
        elif i > total_amostras - amostras_liberacao:
            envelope = (total_amostras - 1 - i) / amostras_liberacao
        else:
            envelope = 1.0

        # Amostra senoidal pura multiplicada pelo envelope e amplitude
        amostra_float = math.sin(fator_angular * i) * envelope * amplitude
        amostra_int = int(round(amostra_float))

        # Clamp de segurança para int16
        if amostra_int > 32767:
            amostra_int = 32767
        elif amostra_int < -32768:
            amostra_int = -32768

        buffer.append(amostra_int)

    return buffer


class Audio:
    """Controlador de áudio do jogo.

    Sintetiza e armazena os buffers na inicialização, fornecendo métodos de
    reprodução e controle de mudo com tolerância a falhas de hardware de áudio.
    """

    def __init__(self) -> None:
        self.disponivel: bool = False
        self.mudo: bool = False
        self.sons: Dict[str, pygame.mixer.Sound] = {}

        # Verifica se o mixer do Pygame foi inicializado previamente
        if pygame.mixer.get_init() is None:
            print("[Áudio] Dispositivo de áudio indisponível. O jogo continuará sem som.")
            return

        try:
            # Sintetiza as notas uma única vez na inicialização
            for elemento in ELEMENTOS:
                freq = FREQUENCIAS[elemento]
                amostras = sintetizar_nota(freq)
                self.sons[elemento] = pygame.mixer.Sound(buffer=amostras)
            self.disponivel = True
        except (pygame.error, Exception) as erro:
            print(f"[Áudio] Erro ao carregar sons sintetizados: {erro}")
            self.disponivel = False
            self.sons.clear()

    def tocar(self, elemento: str) -> None:
        """Reproduz a nota associada ao elemento especificado."""
        if not self.disponivel or self.mudo:
            return
        som = self.sons.get(elemento)
        if som is not None:
            som.play()

    def alternar_mudo(self) -> bool:
        """Alterna o estado de mudo e interrompe reproduções ativas."""
        self.mudo = not self.mudo
        if self.mudo and self.disponivel:
            try:
                pygame.mixer.stop()
            except pygame.error:
                pass
        return self.mudo

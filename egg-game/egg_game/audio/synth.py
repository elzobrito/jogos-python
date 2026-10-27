# -*- coding: utf-8 -*-
"""
Síntese procedural de efeitos sonoros e loop musical em código (SPEC §3).
Usa `pygame.mixer.Sound(buffer=...)` sem dependências externas e falha
silenciosamente caso não haja dispositivo de áudio disponível.
"""

from __future__ import annotations

import math
import random
import struct
from typing import Dict, List, Optional, Sequence

import pygame


class AudioService:
    """Gerencia efeitos sonoros (SFX) e música de fundo (BGM) sintetizados."""

    SAMPLE_RATE = 22050

    def __init__(self, music_enabled: bool = True, sfx_enabled: bool = True) -> None:
        self.music_enabled = bool(music_enabled)
        self.sfx_enabled = bool(sfx_enabled)
        self.available = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.bgm_channel: Optional[pygame.mixer.Channel] = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self.sounds["jump"] = self._synth_jump()
            self.sounds["land"] = self._synth_land()
            self.sounds["crack"] = self._synth_crack()
            self.sounds["game_over"] = self._synth_game_over()
            self.sounds["victory"] = self._synth_victory()
            self.sounds["ui_select"] = self._synth_ui_select()
            self.sounds["bgm_loop"] = self._synth_bgm_loop()
            self.available = True
        except Exception:
            self.available = False

    def _pack_pcm16(self, samples: Sequence[float]) -> bytes:
        return b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767))
            for s in samples
        )

    def _synth_jump(self) -> pygame.mixer.Sound:
        """Efeito elástico ascendente ('boing' suave) para o pulo do ovo."""
        duration = 0.16
        n = int(self.SAMPLE_RATE * duration)
        samples: List[float] = []
        phase = 0.0
        for i in range(n):
            t = i / n
            freq = 310.0 + 440.0 * (t ** 1.15)
            phase += (2.0 * math.pi * freq) / self.SAMPLE_RATE
            env = math.sin(math.pi * t) * (1.0 - 0.3 * t) * 0.36
            val = (0.75 * math.sin(phase) + 0.25 * math.sin(2.0 * phase)) * env
            samples.append(val)
        return pygame.mixer.Sound(buffer=self._pack_pcm16(samples))

    def _synth_land(self) -> pygame.mixer.Sound:
        """Som acolhedor de pouso na palha da cesta."""
        duration = 0.10
        n = int(self.SAMPLE_RATE * duration)
        rng = random.Random(12)
        samples: List[float] = []
        phase = 0.0
        for i in range(n):
            t = i / n
            freq = 180.0 + 90.0 * (1.0 - t)
            phase += (2.0 * math.pi * freq) / self.SAMPLE_RATE
            env = ((1.0 - t) ** 1.8) * 0.32
            rustle = rng.uniform(-0.35, 0.35)
            samples.append((0.7 * math.sin(phase) + rustle) * env)
        return pygame.mixer.Sound(buffer=self._pack_pcm16(samples))

    def _synth_crack(self) -> pygame.mixer.Sound:
        """Som cartunesco de casca rachando."""
        duration = 0.26
        n = int(self.SAMPLE_RATE * duration)
        rng = random.Random(99)
        samples: List[float] = []
        phase = 0.0
        for i in range(n):
            t = i / n
            freq = 240.0 - 150.0 * t
            phase += (2.0 * math.pi * freq) / self.SAMPLE_RATE
            burst = 1.0 if (i % 900 < 220) else 0.35
            noise = rng.uniform(-1.0, 1.0) * 0.55 * burst
            env = (1.0 - t) * 0.42
            samples.append((noise + 0.45 * math.sin(phase)) * env)
        return pygame.mixer.Sound(buffer=self._pack_pcm16(samples))

    def _synth_game_over(self) -> pygame.mixer.Sound:
        """Pequena sequência descendente cômica para o Game Over."""
        notas = [392.0, 349.23, 329.63, 261.63]
        dur_nota = 0.11
        samples: List[float] = []
        phase = 0.0
        for freq in notas:
            n = int(self.SAMPLE_RATE * dur_nota)
            for i in range(n):
                t = i / n
                phase += (2.0 * math.pi * freq) / self.SAMPLE_RATE
                env = (1.0 - t * 0.7) * 0.30
                samples.append(math.sin(phase) * env)
        return pygame.mixer.Sound(buffer=self._pack_pcm16(samples))

    def _synth_victory(self) -> pygame.mixer.Sound:
        """Fanfarra alegre ao alcançar o ninho final a 120 m."""
        notas = [523.25, 659.25, 783.99, 1046.50]
        dur_nota = 0.12
        samples: List[float] = []
        phase = 0.0
        for idx, freq in enumerate(notas):
            dur = dur_nota * (1.6 if idx == len(notas) - 1 else 1.0)
            n = int(self.SAMPLE_RATE * dur)
            for i in range(n):
                t = i / n
                phase += (2.0 * math.pi * freq) / self.SAMPLE_RATE
                env = (1.0 - t * 0.5) * 0.34
                samples.append((0.8 * math.sin(phase) + 0.2 * math.sin(2.0 * phase)) * env)
        return pygame.mixer.Sound(buffer=self._pack_pcm16(samples))

    def _synth_ui_select(self) -> pygame.mixer.Sound:
        """Clique de madeira suave para botões da interface."""
        duration = 0.06
        n = int(self.SAMPLE_RATE * duration)
        samples: List[float] = []
        phase = 0.0
        for i in range(n):
            t = i / n
            freq = 540.0 + 180.0 * (1.0 - t)
            phase += (2.0 * math.pi * freq) / self.SAMPLE_RATE
            env = ((1.0 - t) ** 2.0) * 0.28
            samples.append(math.sin(phase) * env)
        return pygame.mixer.Sound(buffer=self._pack_pcm16(samples))

    def _synth_bgm_loop(self) -> pygame.mixer.Sound:
        """Melodia suave estilo marimba para loop de fundo."""
        notas = [261.63, 329.63, 392.00, 329.63, 293.66, 349.23, 392.00, 349.23]
        dur_nota = 0.24
        samples: List[float] = []
        phase = 0.0
        for freq in notas:
            n = int(self.SAMPLE_RATE * dur_nota)
            for i in range(n):
                t = i / n
                phase += (2.0 * math.pi * freq) / self.SAMPLE_RATE
                env = math.exp(-3.5 * t) * 0.12
                samples.append(math.sin(phase) * env)
        return pygame.mixer.Sound(buffer=self._pack_pcm16(samples))

    def play_sfx(self, name: str) -> None:
        """Toca um efeito sonoro caso `sfx_enabled` esteja ativo."""
        if not self.available or not self.sfx_enabled:
            return
        som = self.sounds.get(name)
        if som is not None:
            try:
                som.play()
            except Exception:
                pass

    def update_music_state(self, should_play: bool) -> None:
        """Inicia ou interrompe o loop musical conforme `music_enabled`."""
        if not self.available:
            return
        bgm = self.sounds.get("bgm_loop")
        if bgm is None:
            return
        try:
            if should_play and self.music_enabled:
                if self.bgm_channel is None or not self.bgm_channel.get_busy():
                    self.bgm_channel = bgm.play(loops=-1)
            else:
                bgm.stop()
                self.bgm_channel = None
        except Exception:
            pass

    def set_music_enabled(self, enabled: bool) -> None:
        self.music_enabled = bool(enabled)
        self.update_music_state(self.music_enabled)

    def set_sfx_enabled(self, enabled: bool) -> None:
        self.sfx_enabled = bool(enabled)

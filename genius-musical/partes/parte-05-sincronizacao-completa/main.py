#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parte 5 — Sincronização, pausa e mute: o Genius Musical completo."""

from __future__ import annotations

import math
import random
import sys
from array import array
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pygame

# --- Configuração ---
LARGURA, ALTURA, FPS = 960, 720, 60
MAX_DELTA_TIME = 0.033
FS, AMPLITUDE = 44100, 24000
DURACAO_NOTA_S = 0.450
TEMPO_ATAQUE_S, TEMPO_LIBERACAO_S = 0.010, 0.030
TEMPO_DESTAQUE_S = 0.450
INTERVALO_ENTRE_NOTAS_S = 0.200
FEEDBACK_TOQUE_S = 0.180
INTERVALO_PROXIMA_RODADA_S = 0.800

FUNDO = (16, 24, 39)
PAINEL = (30, 41, 59)
TEXTO = (248, 250, 252)
TEXTO_ESCURO = (16, 24, 39)
TEXTO_SUAVE = (148, 163, 184)
BORDA = (51, 65, 85)
BORDA_DESTAQUE = (255, 255, 255)
FOGO = (248, 113, 113)
AGUA = (96, 165, 250)
TERRA = (74, 222, 128)
AR = (250, 204, 21)

ELEMENTOS = ("fogo", "agua", "terra", "ar")
FREQUENCIAS = {"fogo": 261.63, "agua": 329.63, "terra": 392.00, "ar": 523.25}
CORES_ELEMENTOS = {"fogo": FOGO, "agua": AGUA, "terra": TERRA, "ar": AR}
CORES_ATIVAS = {
    "fogo": (254, 180, 180), "agua": (175, 215, 254),
    "terra": (160, 245, 195), "ar": (255, 235, 140),
}
CORES_INDISPONIVEIS = {
    "fogo": (160, 75, 75), "agua": (65, 110, 165),
    "terra": (50, 145, 85), "ar": (165, 135, 20),
}
ROTULOS = {"fogo": "FOGO", "agua": "ÁGUA", "terra": "TERRA", "ar": "AR"}
TECLAS_ROTULO = {"fogo": "1", "agua": "2", "terra": "3", "ar": "4"}

# partes/parte-05-*/ → raiz do jogo → assets/imagens
DIRETORIO_BASE = Path(__file__).resolve().parent.parent.parent
PASTA_ASSETS_IMAGENS = DIRETORIO_BASE / "assets" / "imagens"
CAMINHOS_IMAGENS = {e: PASTA_ASSETS_IMAGENS / f"{e}.png" for e in ELEMENTOS}


def sintetizar_nota(
    freq: float,
    duracao: float = DURACAO_NOTA_S,
    fs: int = FS,
    amplitude: float = AMPLITUDE,
    tempo_ataque: float = TEMPO_ATAQUE_S,
    tempo_liberacao: float = TEMPO_LIBERACAO_S,
) -> array:
    total = max(1, int(duracao * fs))
    n_ataque = max(1, int(tempo_ataque * fs))
    n_liberacao = max(1, int(tempo_liberacao * fs))
    buffer = array("h")
    fator = 2.0 * math.pi * freq / fs
    for i in range(total):
        if i < n_ataque:
            envelope = i / n_ataque
        elif i > total - n_liberacao:
            envelope = (total - 1 - i) / n_liberacao
        else:
            envelope = 1.0
        amostra = int(round(math.sin(fator * i) * envelope * amplitude))
        buffer.append(max(-32768, min(32767, amostra)))
    return buffer


class Audio:
    def __init__(self) -> None:
        self.disponivel = False
        self.mudo = False
        self.sons: Dict[str, pygame.mixer.Sound] = {}
        if pygame.mixer.get_init() is None:
            print("[Áudio] Dispositivo indisponível.")
            return
        try:
            for elem in ELEMENTOS:
                self.sons[elem] = pygame.mixer.Sound(
                    buffer=sintetizar_nota(FREQUENCIAS[elem])
                )
            self.disponivel = True
        except pygame.error as erro:
            print(f"[Áudio] Erro: {erro}")

    def tocar(self, elemento: str) -> None:
        if not self.disponivel or self.mudo:
            return
        som = self.sons.get(elemento)
        if som is not None:
            som.play()

    def alternar_mudo(self) -> bool:
        self.mudo = not self.mudo
        if self.mudo and self.disponivel:
            try:
                pygame.mixer.stop()
            except pygame.error:
                pass
        return self.mudo


class EstadoJogo(Enum):
    MENU = auto()
    DEMONSTRANDO = auto()
    ENTRADA = auto()
    FEEDBACK = auto()
    FIM = auto()
    PAUSADO = auto()


class Jogo:
    def __init__(self, on_tocar_som: Optional[Callable[[str], None]] = None) -> None:
        self.on_tocar_som = on_tocar_som
        self.rng = random.Random()
        self.estado = EstadoJogo.MENU
        self.estado_anterior = EstadoJogo.MENU
        self.sequencia: List[str] = []
        self.pontuacao = 0
        self.indice_demonstracao = 0
        self.fase_demonstracao = "destaque"
        self.elemento_demonstrado: Optional[str] = None
        self.temporizador = 0.0
        self.indice_jogador = 0
        self.elemento_pressionado: Optional[str] = None
        self.temporizador_toque = 0.0
        self.temporizador_feedback = 0.0
        self.posicao_erro: Optional[int] = None

    @property
    def rodada(self) -> int:
        return self.pontuacao + 1

    @property
    def elemento_ativo(self) -> Optional[str]:
        if self.estado == EstadoJogo.DEMONSTRANDO:
            return self.elemento_demonstrado
        if self.estado in (EstadoJogo.ENTRADA, EstadoJogo.FEEDBACK):
            return self.elemento_pressionado
        return None

    @property
    def mensagem_status(self) -> str:
        if self.estado == EstadoJogo.MENU:
            return "Pressione Enter ou clique em Iniciar"
        if self.estado == EstadoJogo.DEMONSTRANDO:
            return "Observe a sequência"
        if self.estado == EstadoJogo.ENTRADA:
            return f"Sua vez — {self.indice_jogador} de {len(self.sequencia)}"
        if self.estado == EstadoJogo.FEEDBACK:
            return "Sequência correta!"
        if self.estado == EstadoJogo.FIM:
            return f"Você errou na posição {self.posicao_erro}! Enter para reiniciar"
        if self.estado == EstadoJogo.PAUSADO:
            return "PAUSADO — Pressione P ou Esc para continuar"
        return ""

    def iniciar(self) -> None:
        self.pontuacao = 0
        self.sequencia = [self.rng.choice(ELEMENTOS)]
        self.posicao_erro = None
        self.elemento_pressionado = None
        self._iniciar_demonstracao()

    def reiniciar(self) -> None:
        self.iniciar()

    def pausar_ou_retomar(self) -> None:
        if self.estado == EstadoJogo.PAUSADO:
            self.estado = self.estado_anterior
        elif self.estado in (EstadoJogo.DEMONSTRANDO, EstadoJogo.ENTRADA, EstadoJogo.FEEDBACK):
            self.estado_anterior = self.estado
            self.estado = EstadoJogo.PAUSADO

    def selecionar(self, elemento: str) -> bool:
        if self.estado != EstadoJogo.ENTRADA or elemento not in ELEMENTOS:
            return False
        self.elemento_pressionado = elemento
        self.temporizador_toque = FEEDBACK_TOQUE_S
        self._notificar_som(elemento)
        esperado = self.sequencia[self.indice_jogador]
        if elemento == esperado:
            self.indice_jogador += 1
            if self.indice_jogador == len(self.sequencia):
                self.estado = EstadoJogo.FEEDBACK
                self.temporizador_feedback = INTERVALO_PROXIMA_RODADA_S
            return True
        self.posicao_erro = self.indice_jogador + 1
        self.estado = EstadoJogo.FIM
        return False

    def atualizar(self, dt: float) -> None:
        if self.estado == EstadoJogo.PAUSADO:
            return
        if self.temporizador_toque > 0:
            self.temporizador_toque -= dt
            if self.temporizador_toque <= 0:
                self.elemento_pressionado = None
        if self.estado == EstadoJogo.DEMONSTRANDO:
            self._atualizar_demonstracao(dt)
        elif self.estado == EstadoJogo.FEEDBACK:
            self.temporizador_feedback -= dt
            if self.temporizador_feedback <= 0:
                self.pontuacao += 1
                self.sequencia.append(self.rng.choice(ELEMENTOS))
                self._iniciar_demonstracao()

    def _iniciar_demonstracao(self) -> None:
        self.estado = EstadoJogo.DEMONSTRANDO
        self.indice_demonstracao = 0
        self.fase_demonstracao = "destaque"
        self.temporizador = 0.0
        self.elemento_demonstrado = self.sequencia[0]
        self._notificar_som(self.elemento_demonstrado)

    def _atualizar_demonstracao(self, dt: float) -> None:
        self.temporizador += dt
        if self.fase_demonstracao == "destaque":
            if self.temporizador >= TEMPO_DESTAQUE_S:
                self.elemento_demonstrado = None
                self.temporizador = 0.0
                if self.indice_demonstracao < len(self.sequencia) - 1:
                    self.fase_demonstracao = "pausa"
                else:
                    self.estado = EstadoJogo.ENTRADA
                    self.indice_jogador = 0
        elif self.fase_demonstracao == "pausa":
            if self.temporizador >= INTERVALO_ENTRE_NOTAS_S:
                self.temporizador = 0.0
                self.indice_demonstracao += 1
                self.fase_demonstracao = "destaque"
                self.elemento_demonstrado = self.sequencia[self.indice_demonstracao]
                self._notificar_som(self.elemento_demonstrado)

    def _notificar_som(self, elemento: str) -> None:
        if self.on_tocar_som is not None:
            self.on_tocar_som(elemento)


class Interface:
    def __init__(self, tela: pygame.Surface, audio: Optional[Audio] = None) -> None:
        self.tela = tela
        self.audio = audio
        self.fonte_titulo = pygame.font.SysFont("dejavusans", 24, bold=True)
        self.fonte_cabecalho = pygame.font.SysFont("dejavusans", 17, bold=True)
        self.fonte_card = pygame.font.SysFont("dejavusans", 21, bold=True)
        self.fonte_tecla = pygame.font.SysFont("dejavusans", 13, bold=True)
        self.fonte_status = pygame.font.SysFont("dejavusans", 19, bold=True)
        self.fonte_botao = pygame.font.SysFont("dejavusans", 14, bold=True)
        self.fonte_pequena = pygame.font.SysFont("dejavusans", 12)
        self.retangulos = {
            "fogo": pygame.Rect(100, 104, 360, 206),
            "agua": pygame.Rect(500, 104, 360, 206),
            "terra": pygame.Rect(100, 334, 360, 206),
            "ar": pygame.Rect(500, 334, 360, 206),
        }
        self.btn_iniciar = pygame.Rect(150, 626, 190, 40)
        self.btn_pausa = pygame.Rect(385, 626, 190, 40)
        self.btn_som = pygame.Rect(620, 626, 190, 40)
        self.icones: Dict[str, pygame.Surface] = {}
        for elem, caminho in CAMINHOS_IMAGENS.items():
            try:
                img = pygame.image.load(str(caminho)).convert_alpha()
                self.icones[elem] = pygame.transform.smoothscale(img, (96, 96))
            except (pygame.error, FileNotFoundError) as erro:
                print(f"[Interface] {caminho}: {erro}")
                self.icones[elem] = pygame.Surface((96, 96), pygame.SRCALPHA)

    def hit_test(self, pos: Tuple[int, int]) -> Optional[str]:
        for elem, rect in self.retangulos.items():
            if rect.collidepoint(pos):
                return elem
        if self.btn_iniciar.collidepoint(pos):
            return "btn_iniciar"
        if self.btn_pausa.collidepoint(pos):
            return "btn_pausa"
        if self.btn_som.collidepoint(pos):
            return "btn_som"
        return None

    def desenhar(self, jogo: Jogo) -> None:
        self.tela.fill(FUNDO)
        pygame.draw.rect(self.tela, PAINEL, pygame.Rect(0, 0, LARGURA, 82))
        pygame.draw.line(self.tela, BORDA, (0, 82), (LARGURA, 82), 1)
        self.tela.blit(self.fonte_titulo.render("GENIUS MUSICAL", True, TEXTO), (60, 18))
        self.tela.blit(
            self.fonte_pequena.render("Memória Audiovisual · Acorde Dó Maior", True, TEXTO_SUAVE),
            (60, 48),
        )
        if self.audio is not None and not self.audio.disponivel:
            self.tela.blit(self.fonte_pequena.render("[SOM INDISPONÍVEL]", True, FOGO), (285, 23))
        txt_r = self.fonte_cabecalho.render(f"RODADA  {jogo.rodada:02d}", True, TEXTO)
        self.tela.blit(txt_r, txt_r.get_rect(topright=(LARGURA - 60, 18)))
        txt_p = self.fonte_pequena.render(f"PONTUAÇÃO: {jogo.pontuacao}", True, TEXTO_SUAVE)
        self.tela.blit(txt_p, txt_p.get_rect(topright=(LARGURA - 60, 46)))

        ativo = jogo.elemento_ativo
        for elem in ELEMENTOS:
            rect = self.retangulos[elem]
            esta_ativo = ativo == elem
            indisponivel = jogo.estado == EstadoJogo.DEMONSTRANDO and not esta_ativo
            if esta_ativo:
                cor, borda, lw = CORES_ATIVAS[elem], BORDA_DESTAQUE, 4
            elif indisponivel:
                cor, borda, lw = CORES_INDISPONIVEIS[elem], BORDA, 2
            else:
                cor, borda, lw = CORES_ELEMENTOS[elem], BORDA, 2
            pygame.draw.rect(self.tela, cor, rect, border_radius=16)
            pygame.draw.rect(self.tela, borda, rect, lw, border_radius=16)
            self.tela.blit(self.icones[elem], (rect.centerx - 48, rect.top + 22))
            rotulo = self.fonte_card.render(ROTULOS[elem], True, TEXTO_ESCURO)
            self.tela.blit(rotulo, rotulo.get_rect(center=(rect.centerx, rect.top + 154)))
            self.tela.blit(
                self.fonte_tecla.render(TECLAS_ROTULO[elem], True, TEXTO_ESCURO),
                (rect.left + 22, rect.top + 18),
            )

        if jogo.estado == EstadoJogo.FEEDBACK:
            cor_msg = TERRA
        elif jogo.estado == EstadoJogo.FIM:
            cor_msg = FOGO
        elif jogo.estado == EstadoJogo.PAUSADO:
            cor_msg = AR
        else:
            cor_msg = TEXTO
        msg = self.fonte_status.render(jogo.mensagem_status, True, cor_msg)
        self.tela.blit(msg, msg.get_rect(center=(LARGURA // 2, 578)))

        if jogo.estado == EstadoJogo.FIM:
            label_iniciar = "Reiniciar [Enter]"
        elif jogo.estado == EstadoJogo.PAUSADO:
            label_iniciar = "Retomar [Enter]"
        elif jogo.estado == EstadoJogo.MENU:
            label_iniciar = "Iniciar [Enter]"
        else:
            label_iniciar = "Partida Ativa"
        label_pausa = "Retomar [P]" if jogo.estado == EstadoJogo.PAUSADO else "Pausar [P]"
        if self.audio is not None and not self.audio.disponivel:
            label_som = "Som Indisponível"
        elif self.audio is not None and self.audio.mudo:
            label_som = "Som: Mudo [M]"
        else:
            label_som = "Som: Ligado [M]"
        for rect_btn, rotulo in (
            (self.btn_iniciar, label_iniciar),
            (self.btn_pausa, label_pausa),
            (self.btn_som, label_som),
        ):
            pygame.draw.rect(self.tela, PAINEL, rect_btn, border_radius=8)
            pygame.draw.rect(self.tela, BORDA, rect_btn, 1, border_radius=8)
            txt = self.fonte_botao.render(rotulo, True, TEXTO)
            self.tela.blit(txt, txt.get_rect(center=rect_btn.center))
        info = "Mouse · 1-4 · Enter · P/Esc · M"
        tip = self.fonte_pequena.render(info, True, TEXTO_SUAVE)
        self.tela.blit(tip, tip.get_rect(center=(LARGURA // 2, 695)))


def main() -> int:
    try:
        pygame.mixer.pre_init(FS, -16, 1, 512)
    except Exception as erro:
        print(f"[Aviso] pre_init: {erro}")
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Genius Musical — Parte 5: sincronização completa")
    audio = Audio()
    jogo = Jogo(on_tocar_som=audio.tocar)
    interface = Interface(tela, audio=audio)
    relogio = pygame.time.Clock()
    executando = True
    while executando:
        dt = min(relogio.tick(FPS) / 1000.0, MAX_DELTA_TIME)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                    jogo.pausar_ou_retomar()
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if jogo.estado == EstadoJogo.MENU:
                        jogo.iniciar()
                    elif jogo.estado == EstadoJogo.FIM:
                        jogo.reiniciar()
                    elif jogo.estado == EstadoJogo.PAUSADO:
                        jogo.pausar_ou_retomar()
                elif evento.key == pygame.K_m:
                    audio.alternar_mudo()
                elif evento.key in (pygame.K_1, pygame.K_KP1):
                    jogo.selecionar("fogo")
                elif evento.key in (pygame.K_2, pygame.K_KP2):
                    jogo.selecionar("agua")
                elif evento.key in (pygame.K_3, pygame.K_KP3):
                    jogo.selecionar("terra")
                elif evento.key in (pygame.K_4, pygame.K_KP4):
                    jogo.selecionar("ar")
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                alvo = interface.hit_test(evento.pos)
                if alvo in ELEMENTOS:
                    jogo.selecionar(alvo)
                elif alvo == "btn_iniciar":
                    if jogo.estado == EstadoJogo.MENU:
                        jogo.iniciar()
                    elif jogo.estado == EstadoJogo.FIM:
                        jogo.reiniciar()
                    elif jogo.estado == EstadoJogo.PAUSADO:
                        jogo.pausar_ou_retomar()
                elif alvo == "btn_pausa":
                    jogo.pausar_ou_retomar()
                elif alvo == "btn_som":
                    audio.alternar_mudo()
        jogo.atualizar(dt)
        interface.desenhar(jogo)
        pygame.display.flip()
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Módulo de interface gráfica do Genius Musical.

Renderiza a tela em estilo flat (minimalista, sem gradientes ou relevos 3D),
carrega sprites PNG com transparência, gerencia a grade 2×2 de cartões e
trata o teste de colisão para cliques de mouse (hit_test).
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import pygame

from audio import Audio
from configuracao import (
    ALTURA,
    AR,
    BORDA,
    BORDA_DESTAQUE,
    CAMINHOS_IMAGENS,
    CORES_ATIVAS,
    CORES_ELEMENTOS,
    CORES_INDISPONIVEIS,
    ELEMENTOS,
    FOGO,
    FUNDO,
    LARGURA,
    PAINEL,
    PAINEL_CARD,
    ROTULOS,
    TECLAS_ROTULO,
    TERRA,
    TEXTO,
    TEXTO_ESCURO,
    TEXTO_SUAVE,
)
from jogo import EstadoJogo, Jogo


class Interface:
    """Responsável pela apresentação visual e testes de impacto do mouse."""

    def __init__(self, tela: pygame.Surface, audio: Optional[Audio] = None) -> None:
        """Inicializa a interface gráfica, fontes e geometria dos componentes.

        Args:
            tela: Superfície principal de exibição (960×720).
            audio: Instância do controlador de áudio para consulta de status.
        """
        self.tela = tela
        self.audio = audio

        # ---------------------------------------------------------------------
        # Fontes tipográficas sem serifa
        # ---------------------------------------------------------------------
        self.fonte_titulo = pygame.font.SysFont("dejavusans", 24, bold=True)
        self.fonte_cabecalho = pygame.font.SysFont("dejavusans", 17, bold=True)
        self.fonte_card = pygame.font.SysFont("dejavusans", 21, bold=True)
        self.fonte_tecla = pygame.font.SysFont("dejavusans", 13, bold=True)
        self.fonte_status = pygame.font.SysFont("dejavusans", 19, bold=True)
        self.fonte_botao = pygame.font.SysFont("dejavusans", 14, bold=True)
        self.fonte_pequena = pygame.font.SysFont("dejavusans", 12)

        # ---------------------------------------------------------------------
        # Geometria dos Cartões da Grade 2×2 (Sem sobreposição)
        # ---------------------------------------------------------------------
        # Grade centralizada: cartões de 360×206 px com espaçamento consistente
        self.retangulos: Dict[str, pygame.Rect] = {
            "fogo": pygame.Rect(100, 104, 360, 206),   # Superior Esquerdo
            "agua": pygame.Rect(500, 104, 360, 206),   # Superior Direito
            "terra": pygame.Rect(100, 334, 360, 206),  # Inferior Esquerdo
            "ar": pygame.Rect(500, 334, 360, 206),     # Inferior Direito
        }

        # ---------------------------------------------------------------------
        # Geometria dos Botões Inferiores de Ação
        # ---------------------------------------------------------------------
        self.btn_iniciar = pygame.Rect(150, 626, 190, 40)
        self.btn_pausa = pygame.Rect(385, 626, 190, 40)
        self.btn_som = pygame.Rect(620, 626, 190, 40)

        # ---------------------------------------------------------------------
        # Carregamento e Escalonamento dos Sprites PNG Flat
        # ---------------------------------------------------------------------
        self.icones: Dict[str, pygame.Surface] = {}
        tamanho_icone = (96, 96)

        for elem, caminho in CAMINHOS_IMAGENS.items():
            try:
                img_bruta = pygame.image.load(str(caminho)).convert_alpha()
                self.icones[elem] = pygame.transform.smoothscale(img_bruta, tamanho_icone)
            except (pygame.error, FileNotFoundError) as erro:
                print(f"[Interface] Aviso: Não foi possível carregar imagem {caminho}: {erro}")
                # Superfície fallback transparente para testes
                surf = pygame.Surface(tamanho_icone, pygame.SRCALPHA)
                self.icones[elem] = surf

    def hit_test(self, pos: Tuple[int, int]) -> Optional[str]:
        """Identifica qual elemento ou botão clicável interceptou a coordenada do mouse.

        Garante que os testes sejam mutuamente exclusivos e livres de sobreposição.

        Args:
            pos: Coordenadas (x, y) do ponteiro do mouse.

        Returns:
            Identificador do elemento ("fogo", "agua", "terra", "ar"),
            identificador de botão ("btn_iniciar", "btn_pausa", "btn_som"),
            ou None caso o clique tenha ocorrido em área neutra.
        """
        # Checa os 4 cartões da grade
        for elem, rect in self.retangulos.items():
            if rect.collidepoint(pos):
                return elem

        # Checa os botões de controle
        if self.btn_iniciar.collidepoint(pos):
            return "btn_iniciar"
        if self.btn_pausa.collidepoint(pos):
            return "btn_pausa"
        if self.btn_som.collidepoint(pos):
            return "btn_som"

        return None

    def desenhar(self, jogo: Jogo) -> None:
        """Renderiza o quadro completo do jogo com composição visual flat."""
        # 1. Fundo uniforme escuro
        self.tela.fill(FUNDO)

        # 2. Cabeçalho
        self._desenhar_cabecalho(jogo)

        # 3. Grade 2×2 de Cartões
        self._desenhar_grade(jogo)

        # 4. Linha de Feedback e Instruções
        self._desenhar_feedback(jogo)

        # 5. Barra de Controles Inferiores
        self._desenhar_botoes(jogo)

    def _desenhar_cabecalho(self, jogo: Jogo) -> None:
        """Renderiza a barra superior de título e placar."""
        # Faixa sutil superior
        faixa = pygame.Rect(0, 0, LARGURA, 82)
        pygame.draw.rect(self.tela, PAINEL, faixa)
        pygame.draw.line(self.tela, BORDA, (0, 82), (LARGURA, 82), 1)

        # Título do jogo à esquerda
        txt_titulo = self.fonte_titulo.render("GENIUS MUSICAL", True, TEXTO)
        self.tela.blit(txt_titulo, (60, 18))

        # Indicador de modo / subtítulo
        txt_sub = self.fonte_pequena.render("Memória Audiovisual · Acorde Dó Maior", True, TEXTO_SUAVE)
        self.tela.blit(txt_sub, (60, 48))

        # Status do áudio ao lado do título
        if self.audio is not None and not self.audio.disponivel:
            badge_som = self.fonte_pequena.render("[SOM INDISPONÍVEL]", True, FOGO)
            self.tela.blit(badge_som, (285, 23))

        # Rodada e Pontuação à direita
        texto_rodada = f"RODADA  {jogo.rodada:02d}"
        txt_r = self.fonte_cabecalho.render(texto_rodada, True, TEXTO)
        rect_r = txt_r.get_rect(topright=(LARGURA - 60, 18))
        self.tela.blit(txt_r, rect_r)

        texto_pontos = f"PONTUAÇÃO: {jogo.pontuacao}"
        txt_p = self.fonte_pequena.render(texto_pontos, True, TEXTO_SUAVE)
        rect_p = txt_p.get_rect(topright=(LARGURA - 60, 46))
        self.tela.blit(txt_p, rect_p)

    def _desenhar_grade(self, jogo: Jogo) -> None:
        """Renderiza os quatro cartões com seus ícones, rótulos e estados visuais."""
        elem_ativo = jogo.elemento_ativo

        for elem in ELEMENTOS:
            rect = self.retangulos[elem]

            # Determina o estado visual flat do cartão
            esta_ativo = (elem_ativo == elem)
            esta_indisponivel = (jogo.estado == EstadoJogo.DEMONSTRANDO and not esta_ativo)

            if esta_ativo:
                cor_fundo = CORES_ATIVAS[elem]
                cor_borda = BORDA_DESTAQUE
                largura_borda = 4
            elif esta_indisponivel:
                cor_fundo = CORES_INDISPONIVEIS[elem]
                cor_borda = BORDA
                largura_borda = 2
            else:
                cor_fundo = CORES_ELEMENTOS[elem]
                cor_borda = BORDA
                largura_borda = 2

            # Desenha o cartão sólido com cantos arredondados
            pygame.draw.rect(self.tela, cor_fundo, rect, border_radius=16)
            pygame.draw.rect(self.tela, cor_borda, rect, largura_borda, border_radius=16)

            # Badge da Tecla de Atalho (canto superior esquerdo do cartão)
            rect_badge = pygame.Rect(rect.left + 16, rect.top + 14, 28, 24)
            cor_badge = (0, 0, 0, 70) if not esta_indisponivel else (0, 0, 0, 40)
            badge_surf = pygame.Surface(rect_badge.size, pygame.SRCALPHA)
            badge_surf.fill(cor_badge)
            self.tela.blit(badge_surf, rect_badge.topleft)
            pygame.draw.rect(self.tela, TEXTO_ESCURO, rect_badge, 1, border_radius=5)

            txt_tecla = self.fonte_tecla.render(TECLAS_ROTULO[elem], True, TEXTO_ESCURO)
            txt_tecla_rect = txt_tecla.get_rect(center=rect_badge.center)
            self.tela.blit(txt_tecla, txt_tecla_rect)

            # Sprite PNG do Ícone (centralizado na metade superior)
            icone = self.icones.get(elem)
            if icone is not None:
                # Se indisponível, aplica modulação de transparência leve
                pos_icone = (rect.centerx - icone.get_width() // 2, rect.top + 22)
                self.tela.blit(icone, pos_icone)

            # Rótulo em texto escuro de alto contraste
            rotulo_texto = ROTULOS[elem]
            txt_rotulo = self.fonte_card.render(rotulo_texto, True, TEXTO_ESCURO)
            txt_rotulo_rect = txt_rotulo.get_rect(center=(rect.centerx, rect.top + 154))
            self.tela.blit(txt_rotulo, txt_rotulo_rect)

    def _desenhar_feedback(self, jogo: Jogo) -> None:
        """Renderiza a mensagem de status e instrução para o jogador."""
        msg = jogo.mensagem_status

        # Seleciona cor semafórica para feedback contextual
        if jogo.estado == EstadoJogo.FEEDBACK:
            cor_msg = TERRA
        elif jogo.estado == EstadoJogo.FIM:
            cor_msg = FOGO
        elif jogo.estado == EstadoJogo.PAUSADO:
            cor_msg = AR
        else:
            cor_msg = TEXTO

        txt_msg = self.fonte_status.render(msg, True, cor_msg)
        rect_msg = txt_msg.get_rect(center=(LARGURA // 2, 578))
        self.tela.blit(txt_msg, rect_msg)

    def _desenhar_botoes(self, jogo: Jogo) -> None:
        """Renderiza os botões de ação e atalhos de controle no rodapé."""
        # 1. Botão Iniciar / Reiniciar
        if jogo.estado == EstadoJogo.FIM:
            label_iniciar = "Reiniciar [Enter]"
        elif jogo.estado == EstadoJogo.PAUSADO:
            label_iniciar = "Retomar [Enter]"
        elif jogo.estado == EstadoJogo.MENU:
            label_iniciar = "Iniciar [Enter]"
        else:
            label_iniciar = "Partida Ativa"

        # 2. Botão Pausa
        if jogo.estado == EstadoJogo.PAUSADO:
            label_pausa = "Retomar [P]"
        else:
            label_pausa = "Pausar [P]"

        # 3. Botão Som
        if self.audio is not None and not self.audio.disponivel:
            label_som = "Som Indisponível"
        elif self.audio is not None and self.audio.mudo:
            label_som = "Som: Mudo [M]"
        else:
            label_som = "Som: Ligado [M]"

        botoes = [
            (self.btn_iniciar, label_iniciar),
            (self.btn_pausa, label_pausa),
            (self.btn_som, label_som),
        ]

        for rect_btn, rotulo in botoes:
            pygame.draw.rect(self.tela, PAINEL, rect_btn, border_radius=8)
            pygame.draw.rect(self.tela, BORDA, rect_btn, 1, border_radius=8)
            txt_btn = self.fonte_botao.render(rotulo, True, TEXTO)
            rect_txt = txt_btn.get_rect(center=rect_btn.center)
            self.tela.blit(txt_btn, rect_txt)

        # Rodapé de apoio operacional
        info_rodape = "Mouse: Clique nos cartões · Teclado: 1-Fogo · 2-Água · 3-Terra · 4-Ar · Enter · P/Esc · M"
        txt_info = self.fonte_pequena.render(info_rodape, True, TEXTO_SUAVE)
        rect_info = txt_info.get_rect(center=(LARGURA // 2, 695))
        self.tela.blit(txt_info, rect_info)

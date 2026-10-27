# -*- coding: utf-8 -*-
"""Lógica central e máquina de estados do Genius Musical.

Módulo de lógica pura sem dependência de janela gráfica ou hardware de som,
permitindo execução e testes unitários totalmente headless.
"""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import Callable, List, Optional

from configuracao import (
    ELEMENTOS,
    FEEDBACK_TOQUE_S,
    INTERVALO_ENTRE_NOTAS_S,
    INTERVALO_PROXIMA_RODADA_S,
    TEMPO_DESTAQUE_S,
)


class EstadoJogo(Enum):
    """Estados possíveis da máquina de estados do Genius Musical."""

    MENU = auto()
    DEMONSTRANDO = auto()
    ENTRADA = auto()
    FEEDBACK = auto()
    FIM = auto()
    PAUSADO = auto()


class Jogo:
    """Controlador da mecânica, sequência de notas e temporização do jogo."""

    def __init__(
        self,
        on_tocar_som: Optional[Callable[[str], None]] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        """Inicializa a lógica do jogo.

        Args:
            on_tocar_som: Callback opcional invocado ao disparar o som de uma nota.
            rng: Instância de gerador aleatório para reprodutibilidade em testes.
        """
        self.on_tocar_som = on_tocar_som
        self.rng = rng if rng is not None else random.Random()

        self.estado: EstadoJogo = EstadoJogo.MENU
        self.estado_anterior: EstadoJogo = EstadoJogo.MENU

        self.sequencia: List[str] = []
        self.pontuacao: int = 0

        # Controle de demonstração da sequência
        self.indice_demonstracao: int = 0
        self.fase_demonstracao: str = "destaque"  # "destaque" ou "pausa"
        self.elemento_demonstrado: Optional[str] = None
        self.temporizador: float = 0.0

        # Controle da entrada do jogador
        self.indice_jogador: int = 0
        self.elemento_pressionado: Optional[str] = None
        self.temporizador_toque: float = 0.0

        # Feedback e encerramento
        self.temporizador_feedback: float = 0.0
        self.posicao_erro: Optional[int] = None
        self.elemento_esperado_erro: Optional[str] = None
        self.elemento_clicado_erro: Optional[str] = None

    # -------------------------------------------------------------------------
    # Propriedades de Leitura (Getters para a Interface)
    # -------------------------------------------------------------------------
    @property
    def rodada(self) -> int:
        """Número da rodada atual (1-indexed)."""
        return self.pontuacao + 1

    @property
    def tamanho_sequencia(self) -> int:
        """Quantidade de notas na sequência da rodada atual."""
        return len(self.sequencia)

    @property
    def progresso_jogador(self) -> int:
        """Número de notas já inseridas corretamente na rodada atual."""
        return self.indice_jogador

    @property
    def elemento_ativo(self) -> Optional[str]:
        """Retorna o elemento atualmente destacado/iluminado para a interface."""
        if self.estado == EstadoJogo.DEMONSTRANDO:
            return self.elemento_demonstrado
        if self.estado in (EstadoJogo.ENTRADA, EstadoJogo.FEEDBACK):
            return self.elemento_pressionado
        return None

    @property
    def mensagem_status(self) -> str:
        """Retorna o texto de instrução/feedback para o jogador."""
        if self.estado == EstadoJogo.MENU:
            return "Pressione Enter ou clique em Iniciar"
        if self.estado == EstadoJogo.DEMONSTRANDO:
            return "Observe a sequência"
        if self.estado == EstadoJogo.ENTRADA:
            return f"Sua vez — {self.indice_jogador} de {len(self.sequencia)}"
        if self.estado == EstadoJogo.FEEDBACK:
            return "Sequência correta!"
        if self.estado == EstadoJogo.FIM:
            if self.posicao_erro is not None:
                return f"Você errou na posição {self.posicao_erro}! Enter para reiniciar"
            return "Fim de jogo! Pressione Enter para reiniciar"
        if self.estado == EstadoJogo.PAUSADO:
            return "PAUSADO — Pressione P ou Esc para continuar"
        return ""

    # -------------------------------------------------------------------------
    # Ações e Comandos de Fluxo
    # -------------------------------------------------------------------------
    def iniciar(self) -> None:
        """Inicia uma nova partida a partir do menu inicial."""
        self.pontuacao = 0
        self.sequencia = [self.rng.choice(ELEMENTOS)]
        self.posicao_erro = None
        self.elemento_esperado_erro = None
        self.elemento_clicado_erro = None
        self.elemento_pressionado = None
        self.temporizador_toque = 0.0

        self._iniciar_demonstracao()

    def reiniciar(self) -> None:
        """Reinicia a partida após o fim de jogo ou a pedido do jogador."""
        self.iniciar()

    def pausar_ou_retomar(self) -> None:
        """Alterna entre o estado PAUSADO e o estado anterior da partida."""
        if self.estado == EstadoJogo.PAUSADO:
            self.estado = self.estado_anterior
        elif self.estado in (
            EstadoJogo.DEMONSTRANDO,
            EstadoJogo.ENTRADA,
            EstadoJogo.FEEDBACK,
        ):
            self.estado_anterior = self.estado
            self.estado = EstadoJogo.PAUSADO

    def selecionar(self, elemento: str) -> bool:
        """Processa a seleção de um elemento pelo jogador (via clique ou teclado).

        Args:
            elemento: Identificador do elemento ("fogo", "agua", "terra", "ar").

        Returns:
            True se a seleção foi válida e correta; False caso inválida ou errada.
        """
        # Entradas são terminantemente bloqueadas fora do turno do jogador
        if self.estado != EstadoJogo.ENTRADA:
            return False

        if elemento not in ELEMENTOS:
            return False

        # Ativa feedback visual de toque e reprodução sonora
        self.elemento_pressionado = elemento
        self.temporizador_toque = FEEDBACK_TOQUE_S
        self._notificar_som(elemento)

        esperado = self.sequencia[self.indice_jogador]

        if elemento == esperado:
            self.indice_jogador += 1
            # Jogador acertou todas as notas da rodada
            if self.indice_jogador == len(self.sequencia):
                self.estado = EstadoJogo.FEEDBACK
                self.temporizador_feedback = INTERVALO_PROXIMA_RODADA_S
            return True

        # Jogador cometeu um erro
        self.posicao_erro = self.indice_jogador + 1
        self.elemento_esperado_erro = esperado
        self.elemento_clicado_erro = elemento
        self.estado = EstadoJogo.FIM
        return False

    # -------------------------------------------------------------------------
    # Atualização de Temporização (Delta Time)
    # -------------------------------------------------------------------------
    def atualizar(self, dt: float) -> None:
        """Avança os temporizadores baseados no tempo real decorrido em segundos."""
        if self.estado == EstadoJogo.PAUSADO:
            return

        # Decaimento do feedback de toque do jogador
        if self.temporizador_toque > 0:
            self.temporizador_toque -= dt
            if self.temporizador_toque <= 0:
                self.elemento_pressionado = None

        if self.estado == EstadoJogo.DEMONSTRANDO:
            self._atualizar_demonstracao(dt)
        elif self.estado == EstadoJogo.FEEDBACK:
            self._atualizar_feedback(dt)

    def _iniciar_demonstracao(self) -> None:
        """Prepara e inicia o ciclo de demonstração da sequência atual."""
        self.estado = EstadoJogo.DEMONSTRANDO
        self.indice_demonstracao = 0
        self.fase_demonstracao = "destaque"
        self.temporizador = 0.0

        primeiro_elemento = self.sequencia[0]
        self.elemento_demonstrado = primeiro_elemento
        self._notificar_som(primeiro_elemento)

    def _atualizar_demonstracao(self, dt: float) -> None:
        """Executa a máquina de temporização durante a fase DEMONSTRANDO."""
        self.temporizador += dt

        if self.fase_demonstracao == "destaque":
            if self.temporizador >= TEMPO_DESTAQUE_S:
                self.elemento_demonstrado = None
                self.temporizador = 0.0

                # Se ainda há notas seguintes, entra em pausa entre notas
                if self.indice_demonstracao < len(self.sequencia) - 1:
                    self.fase_demonstracao = "pausa"
                else:
                    # Concluiu a demonstração da sequência inteira
                    self.estado = EstadoJogo.ENTRADA
                    self.indice_jogador = 0

        elif self.fase_demonstracao == "pausa":
            if self.temporizador >= INTERVALO_ENTRE_NOTAS_S:
                self.temporizador = 0.0
                self.indice_demonstracao += 1
                self.fase_demonstracao = "destaque"

                proximo = self.sequencia[self.indice_demonstracao]
                self.elemento_demonstrado = proximo
                self._notificar_som(proximo)

    def _atualizar_feedback(self, dt: float) -> None:
        """Aguarda o intervalo de confirmação e avança para a próxima rodada."""
        self.temporizador_feedback -= dt
        if self.temporizador_feedback <= 0:
            # Incrementa pontuação e adiciona exatamente 1 nova nota ao final
            self.pontuacao += 1
            self.sequencia.append(self.rng.choice(ELEMENTOS))
            self._iniciar_demonstracao()

    def _notificar_som(self, elemento: str) -> None:
        """Aciona o callback de reprodução sonora caso registrado."""
        if self.on_tocar_som is not None:
            self.on_tocar_som(elemento)

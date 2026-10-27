# -*- coding: utf-8 -*-
"""Testes automatizados da lógica pura do Genius Musical.

Valida a mecânica de jogo, máquina de estados, progressão e pontuação
de forma headless e determinística com pytest.
"""

from __future__ import annotations

import random
import pytest

from configuracao import (
    ELEMENTOS,
    INTERVALO_ENTRE_NOTAS_S,
    INTERVALO_PROXIMA_RODADA_S,
    TEMPO_DESTAQUE_S,
)
from jogo import EstadoJogo, Jogo


@pytest.fixture
def rng_fixo() -> random.Random:
    """Retorna um gerador com semente determinística para testes."""
    return random.Random(42)


def test_inicio_com_uma_nota(rng_fixo: random.Random) -> None:
    """Verifica se a partida inicia com exatamente uma nota e pontuação zero."""
    jogo = Jogo(rng=rng_fixo)
    assert jogo.estado == EstadoJogo.MENU

    jogo.iniciar()
    assert jogo.estado == EstadoJogo.DEMONSTRANDO
    assert len(jogo.sequencia) == 1
    assert jogo.sequencia[0] in ELEMENTOS
    assert jogo.pontuacao == 0
    assert jogo.rodada == 1
    assert jogo.tamanho_sequencia == 1
    assert jogo.posicao_erro is None


def test_demonstracao_avanca_para_entrada(rng_fixo: random.Random) -> None:
    """Verifica a transição automática de DEMONSTRANDO para ENTRADA via dt."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    assert jogo.estado == EstadoJogo.DEMONSTRANDO
    assert jogo.elemento_ativo == jogo.sequencia[0]

    # Avança o tempo além do período de destaque da nota única
    jogo.atualizar(TEMPO_DESTAQUE_S + 0.05)
    assert jogo.estado == EstadoJogo.ENTRADA
    assert jogo.indice_jogador == 0
    assert jogo.elemento_ativo is None


def test_crescimento_exatamente_mais_um_por_rodada(rng_fixo: random.Random) -> None:
    """Verifica que cada rodada vencida preserva o prefixo e adiciona +1 nota."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    primeira_nota = jogo.sequencia[0]

    # Avança para o turno do jogador
    jogo.atualizar(TEMPO_DESTAQUE_S + 0.05)
    assert jogo.estado == EstadoJogo.ENTRADA

    # Jogador acerta a nota
    sucesso = jogo.selecionar(primeira_nota)
    assert sucesso is True
    assert jogo.estado == EstadoJogo.FEEDBACK

    # Aguarda o intervalo de transição para a próxima rodada
    jogo.atualizar(INTERVALO_PROXIMA_RODADA_S + 0.05)
    assert jogo.estado == EstadoJogo.DEMONSTRANDO
    assert jogo.pontuacao == 1
    assert jogo.rodada == 2
    assert len(jogo.sequencia) == 2
    # Regra fundamental: o prefixo nunca é regenerado
    assert jogo.sequencia[0] == primeira_nota


def test_validacao_parcial_correta(rng_fixo: random.Random) -> None:
    """Verifica validação passo a passo de uma sequência longa."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    jogo.sequencia = ["fogo", "agua", "terra"]
    jogo.estado = EstadoJogo.ENTRADA
    jogo.indice_jogador = 0

    # 1º acerto parcial
    assert jogo.selecionar("fogo") is True
    assert jogo.indice_jogador == 1
    assert jogo.estado == EstadoJogo.ENTRADA
    assert jogo.pontuacao == 0

    # 2º acerto parcial
    assert jogo.selecionar("agua") is True
    assert jogo.indice_jogador == 2
    assert jogo.estado == EstadoJogo.ENTRADA
    assert jogo.pontuacao == 0

    # 3º acerto: conclusão da sequência
    assert jogo.selecionar("terra") is True
    assert jogo.indice_jogador == 3
    assert jogo.estado == EstadoJogo.FEEDBACK


def test_conclusao_de_rodada_sobe_pontuacao(rng_fixo: random.Random) -> None:
    """Garante que a pontuação só sobe após toda a sequência ser concluída."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    jogo.sequencia = ["fogo", "ar"]
    jogo.estado = EstadoJogo.ENTRADA
    jogo.indice_jogador = 0
    jogo.pontuacao = 4

    jogo.selecionar("fogo")
    assert jogo.pontuacao == 4  # Não sobe no acerto parcial

    jogo.selecionar("ar")
    assert jogo.estado == EstadoJogo.FEEDBACK
    assert jogo.pontuacao == 4  # Sobe ao término do temporizador de feedback

    jogo.atualizar(INTERVALO_PROXIMA_RODADA_S + 0.05)
    assert jogo.pontuacao == 5  # Pontuação atualizada com sucesso
    assert len(jogo.sequencia) == 3


def test_erro_na_primeira_posicao(rng_fixo: random.Random) -> None:
    """Verifica detecção e registro de erro na primeira posição."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    jogo.sequencia = ["fogo", "agua"]
    jogo.estado = EstadoJogo.ENTRADA
    jogo.indice_jogador = 0

    # Jogador pressiona elemento incorreto logo de início
    sucesso = jogo.selecionar("terra")
    assert sucesso is False
    assert jogo.estado == EstadoJogo.FIM
    assert jogo.posicao_erro == 1
    assert jogo.elemento_esperado_erro == "fogo"
    assert jogo.elemento_clicado_erro == "terra"


def test_erro_na_ultima_posicao(rng_fixo: random.Random) -> None:
    """Verifica detecção e registro de erro na última posição da sequência."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    jogo.sequencia = ["fogo", "agua", "terra"]
    jogo.estado = EstadoJogo.ENTRADA
    jogo.indice_jogador = 0

    assert jogo.selecionar("fogo") is True
    assert jogo.selecionar("agua") is True

    # Erro na 3ª posição
    sucesso = jogo.selecionar("ar")
    assert sucesso is False
    assert jogo.estado == EstadoJogo.FIM
    assert jogo.posicao_erro == 3
    assert jogo.elemento_esperado_erro == "terra"
    assert jogo.elemento_clicado_erro == "ar"


def test_selecao_bloqueada_em_estados_invalidos(rng_fixo: random.Random) -> None:
    """Garante que entradas do jogador sejam rigorosamente ignoradas fora de ENTRADA."""
    jogo = Jogo(rng=rng_fixo)

    # 1. Bloqueado em MENU
    assert jogo.estado == EstadoJogo.MENU
    assert jogo.selecionar("fogo") is False

    # 2. Bloqueado em DEMONSTRANDO
    jogo.iniciar()
    assert jogo.estado == EstadoJogo.DEMONSTRANDO
    assert jogo.selecionar("fogo") is False

    # 3. Bloqueado em FEEDBACK
    jogo.estado = EstadoJogo.FEEDBACK
    assert jogo.selecionar("fogo") is False

    # 4. Bloqueado em PAUSADO
    jogo.estado = EstadoJogo.PAUSADO
    assert jogo.selecionar("fogo") is False

    # 5. Bloqueado em FIM
    jogo.estado = EstadoJogo.FIM
    assert jogo.selecionar("fogo") is False


def test_pausar_e_retomar_preserva_indices_e_estado(rng_fixo: random.Random) -> None:
    """Verifica que a pausa congela temporizadores e preserva o progresso exato."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    jogo.sequencia = ["fogo", "agua", "ar"]
    jogo.estado = EstadoJogo.ENTRADA
    jogo.indice_jogador = 0

    # Responde 1ª nota
    jogo.selecionar("fogo")
    assert jogo.indice_jogador == 1

    # Pausa o jogo
    jogo.pausar_ou_retomar()
    assert jogo.estado == EstadoJogo.PAUSADO
    assert jogo.selecionar("agua") is False  # Não aceita entradas pausado

    # Simula passagem de tempo durante a pausa
    jogo.atualizar(2.5)
    assert jogo.estado == EstadoJogo.PAUSADO
    assert jogo.indice_jogador == 1

    # Retoma a partida
    jogo.pausar_ou_retomar()
    assert jogo.estado == EstadoJogo.ENTRADA
    assert jogo.indice_jogador == 1

    # Continua de onde parou
    assert jogo.selecionar("agua") is True
    assert jogo.indice_jogador == 2


def test_reiniciar_apos_fim(rng_fixo: random.Random) -> None:
    """Verifica se reiniciar restabelece o estado limpo para nova partida."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    jogo.estado = EstadoJogo.FIM
    jogo.pontuacao = 7
    jogo.posicao_erro = 4

    jogo.reiniciar()
    assert jogo.estado == EstadoJogo.DEMONSTRANDO
    assert jogo.pontuacao == 0
    assert jogo.rodada == 1
    assert len(jogo.sequencia) == 1
    assert jogo.posicao_erro is None


def test_mouse_e_teclado_mesma_api(rng_fixo: random.Random) -> None:
    """Garante coerência funcional: clique e tecla usam a mesma rotina selecionar()."""
    jogo = Jogo(rng=rng_fixo)
    jogo.iniciar()
    jogo.sequencia = ["agua"]
    jogo.estado = EstadoJogo.ENTRADA

    # Simulação da entrada
    resultado = jogo.selecionar("agua")
    assert resultado is True
    assert jogo.estado == EstadoJogo.FEEDBACK

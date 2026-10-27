#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script de smoke test headless automatizado do Genius Musical.

Simula 4 rodadas corretas em sequência, seguidas de uma rodada com erro induzido,
validando o ciclo completo de demonstração, entrada, feedback, pontuação e game over
sem necessidade de interface gráfica ou hardware de áudio físico.
"""

from __future__ import annotations

import os
import random
import sys

# Configura drivers dummy para execução headless limpa em CI/CD e servidores
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pathlib import Path
DIRETORIO_RAIZ = Path(__file__).resolve().parent.parent
if str(DIRETORIO_RAIZ) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_RAIZ))

import pygame

from audio import Audio
from configuracao import (
    ELEMENTOS,
    INTERVALO_ENTRE_NOTAS_S,
    INTERVALO_PROXIMA_RODADA_S,
    LARGURA,
    ALTURA,
    TEMPO_DESTAQUE_S,
)
from interface import Interface
from jogo import EstadoJogo, Jogo


def main() -> int:
    print("=== Iniciando Smoke Test Headless do Genius Musical ===")

    # 1. Inicialização segura com drivers dummy
    try:
        pygame.mixer.pre_init(44100, -16, 1, 512)
    except Exception as e:
        print(f"[Aviso] pre_init: {e}")

    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    audio = Audio()

    rng = random.Random(12345)
    jogo = Jogo(on_tocar_som=audio.tocar, rng=rng)
    interface = Interface(tela, audio=audio)

    print(f"Status do Áudio: {'Disponível' if audio.disponivel else 'Modo silencioso (fallback gracioso)'}")

    # 2. Inicia o jogo
    jogo.iniciar()
    assert jogo.estado == EstadoJogo.DEMONSTRANDO, "Deveria iniciar em DEMONSTRANDO"
    assert len(jogo.sequencia) == 1, "Deveria ter 1 nota inicial"
    print(f"Rodada 1 iniciada. Sequência: {jogo.sequencia}")

    # Simula 4 rodadas com respostas 100% corretas
    total_rodadas_sucesso = 4
    for r in range(1, total_rodadas_sucesso + 1):
        print(f"\n--- Simulando Rodada {r} (tamanho {len(jogo.sequencia)}) ---")

        # Fase de Demonstração: avança os timers até chegar a ENTRADA
        passos = 0
        while jogo.estado == EstadoJogo.DEMONSTRANDO and passos < 200:
            jogo.atualizar(0.05)
            interface.desenhar(jogo)
            passos += 1

        assert jogo.estado == EstadoJogo.ENTRADA, f"Rodada {r}: Deveria estar em ENTRADA, mas está em {jogo.estado}"
        print(f"Demonstração concluída em {passos * 0.05:.2f}s. Entrando no turno do jogador.")

        # Fase de Entrada: jogador responde exatamente a sequência esperada
        sequencia_alvo = list(jogo.sequencia)
        for i, nota_correta in enumerate(sequencia_alvo):
            assert jogo.indice_jogador == i, f"Índice esperado {i}, obtido {jogo.indice_jogador}"
            sucesso = jogo.selecionar(nota_correta)
            assert sucesso is True, f"Falha ao selecionar nota correta '{nota_correta}'"
            jogo.atualizar(0.03)
            interface.desenhar(jogo)

        # Ao completar a sequência, o jogo deve entrar em FEEDBACK
        assert jogo.estado == EstadoJogo.FEEDBACK, f"Rodada {r}: Deveria estar em FEEDBACK após acertar tudo"
        print(f"Rodada {r} completada com sucesso! Aguardando intervalo de feedback...")

        # Aguarda a transição de FEEDBACK para a próxima rodada
        passos_fb = 0
        while jogo.estado == EstadoJogo.FEEDBACK and passos_fb < 50:
            jogo.atualizar(0.05)
            interface.desenhar(jogo)
            passos_fb += 1

        assert jogo.pontuacao == r, f"Pontuação esperada {r}, obtida {jogo.pontuacao}"
        assert len(jogo.sequencia) == r + 1, f"Tamanho da sequência esperado {r+1}, obtido {len(jogo.sequencia)}"

    # 3. Na 5ª rodada, simula um erro intencional do jogador
    print(f"\n--- Simulando Rodada 5 com Erro Induzido ---")
    while jogo.estado == EstadoJogo.DEMONSTRANDO:
        jogo.atualizar(0.05)
        interface.desenhar(jogo)

    assert jogo.estado == EstadoJogo.ENTRADA
    nota_esperada = jogo.sequencia[0]
    # Sorteia uma nota propositalmente incorreta
    candidatos_errados = [elem for elem in ELEMENTOS if elem != nota_esperada]
    nota_errada = candidatos_errados[0]

    print(f"Nota esperada: '{nota_esperada}' | Inserindo intencionalmente erro: '{nota_errada}'")
    sucesso = jogo.selecionar(nota_errada)
    assert sucesso is False, "A nota errada não deveria ter sido aceita"
    assert jogo.estado == EstadoJogo.FIM, f"Estado deveria ser FIM, obtido {jogo.estado}"
    assert jogo.posicao_erro == 1, f"Posição do erro deveria ser 1, obtida {jogo.posicao_erro}"
    assert jogo.pontuacao == total_rodadas_sucesso, f"Pontuação final deveria ser {total_rodadas_sucesso}"

    # Renderiza o estado de FIM para validar desenho de Game Over
    interface.desenhar(jogo)
    pygame.display.flip()

    print(f"\n[OK] Smoke Test Concluído com Sucesso!")
    print(f"     Pontuação Final: {jogo.pontuacao}")
    print(f"     Status Final: {jogo.mensagem_status}")
    print(f"     Detecção de erro: Posição {jogo.posicao_erro} ({jogo.elemento_esperado_erro} != {jogo.elemento_clicado_erro})")

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())

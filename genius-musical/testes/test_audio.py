# -*- coding: utf-8 -*-
"""Testes automatizados do módulo de síntese e controle de áudio.

Valida a geração digital de senoides PCM mono 16-bit, envelopes de atenuação,
número de amostras e tolerância a falhas na ausência de dispositivo de áudio.
"""

from __future__ import annotations

from array import array

from audio import Audio, sintetizar_nota
from configuracao import (
    AMPLITUDE,
    DURACAO_NOTA_S,
    ELEMENTOS,
    FREQUENCIAS,
    FS,
)


def test_sintetizar_quatro_notas_genius() -> None:
    """Verifica se os quatro buffers das notas do jogo são gerados corretamente."""
    duracao_esperada_amostras = int(DURACAO_NOTA_S * FS)

    for elem in ELEMENTOS:
        freq = FREQUENCIAS[elem]
        buf = sintetizar_nota(freq, duracao=DURACAO_NOTA_S, fs=FS, amplitude=AMPLITUDE)

        assert isinstance(buf, array)
        assert buf.typecode == "h"
        assert len(buf) > 0
        assert len(buf) == duracao_esperada_amostras

        # Todas as amostras devem estar estritamente contidas nos limites int16
        for amostra in buf:
            assert -32768 <= amostra <= 32767

        # O sinal deve oscilar acima e abaixo do eixo zero
        assert max(buf) > 0
        assert min(buf) < 0


def test_numero_amostras_proporcional_a_duracao() -> None:
    """Garante que a quantidade de amostras geradas seja proporcional a T * Fs."""
    for duracao in (0.10, 0.25, 0.45, 0.70):
        buf = sintetizar_nota(440.0, duracao=duracao, fs=FS)
        esperado = int(duracao * FS)
        assert len(buf) == esperado


def test_limites_int16_com_amplitude_maxima() -> None:
    """Verifica que mesmo com amplitude máxima (32767), não ocorrem estouros (overflows)."""
    buf = sintetizar_nota(440.0, duracao=0.2, fs=FS, amplitude=32767)
    for amostra in buf:
        assert -32768 <= amostra <= 32767


def test_funcao_auxiliar_nota_a4_440hz() -> None:
    """Gera nota padrão de referência A4 (Lá 440 Hz) e valida integridade de sinal."""
    freq_a4 = 440.0
    buf_a4 = sintetizar_nota(freq_a4, duracao=0.5, fs=44100, amplitude=20000)

    assert len(buf_a4) == int(0.5 * 44100)
    assert max(buf_a4) > 10000
    assert min(buf_a4) < -10000
    assert all(-32768 <= x <= 32767 for x in buf_a4)


def test_envelope_linear_suaviza_extremidades() -> None:
    """Verifica se o envelope de ataque e liberação zera os estalos nas pontas."""
    buf = sintetizar_nota(440.0, duracao=0.4, fs=FS, amplitude=AMPLITUDE)

    # Primeira amostra inicia em 0 devido ao fade-in
    assert buf[0] == 0

    # Amostra final deve ser próxima de zero devido ao fade-out
    assert abs(buf[-1]) <= 200


def test_classe_audio_tolerante_a_falha_de_hardware() -> None:
    """Verifica que o controlador de áudio opera sem crash mesmo sem mixer ativo."""
    audio = Audio()
    # Se o mixer não estiver inicializado no ambiente de teste, deve desativar graciosamente
    if not audio.disponivel:
        assert audio.disponivel is False
        # Tocar não deve levantar exceção
        audio.tocar("fogo")

    # Mudo pode ser alternado livremente
    estado_mudo_inicial = audio.mudo
    novo_mudo = audio.alternar_mudo()
    assert novo_mudo != estado_mudo_inicial

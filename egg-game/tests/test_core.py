# -*- coding: utf-8 -*-
"""Testes automatizados (headless, sem Pygame) do núcleo do Egg Game (SPEC §5)."""

from __future__ import annotations

from pathlib import Path

from egg_game.core.constants import CENTER_X, FIXED_DT, START_WORLD_Y
from egg_game.core.generator import LevelGenerator, ReachabilityValidator
from egg_game.core.physics import WorldSimulation
from egg_game.core.platforms import Platform
from egg_game.core.score import GameSaveData, SaveRepository, compute_height_m
from egg_game.core.states import EggState


def test_ovo_viaja_com_a_cesta_e_nao_pula_sozinho() -> None:
    """
    Verifica que:
    1. O ovo começa pousado na cesta inicial e viaja horizontalmente com ela.
    2. Não ocorre pulo automático ao pousar (permanece acoplado até comando).
    """
    sim = WorldSimulation(seed=101)
    x_inicial = sim.player.x
    assert sim.player.is_grounded
    assert sim.player.state == EggState.IDLE

    # Avança 30 passos sem pedir pulo: ovo deve permanecer na cesta e acompanhar seu X
    for _ in range(30):
        sim.step_fixed(FIXED_DT)

    cesta = sim.get_platform_by_id(sim.player.attached_platform_id)
    assert cesta is not None
    assert sim.player.is_grounded
    assert sim.player.x == cesta.x
    assert sim.player.x != x_inicial
    assert sim.player.y == cesta.y


def test_pulo_so_sob_comando_e_x_estavel_no_ar() -> None:
    """
    Verifica que:
    1. `request_jump()` desacopla o ovo da cesta e aplica impulso vertical.
    2. Enquanto o ovo está no ar (ASCENDING/DESCENDING), seu X de mundo permanece
       estável no valor do momento do desacoplar, enquanto as cestas continuam se movendo.
    3. Não há pulo duplo no ar.
    """
    sim = WorldSimulation(seed=202)
    for _ in range(10):
        sim.step_fixed(FIXED_DT)

    x_no_momento_do_pulo = sim.player.x
    cesta_origem = sim.get_platform_by_id(sim.player.attached_platform_id)
    assert cesta_origem is not None

    pulou = sim.request_jump()
    assert pulou is True
    assert not sim.player.is_grounded
    assert sim.player.state == EggState.ASCENDING

    # Tentar pular novamente no ar deve retornar False (sem pulo duplo)
    assert sim.request_jump() is False

    # Avança 20 passos no ar (subida): X do ovo fica constante, cesta continua andando
    for _ in range(20):
        sim.step_fixed(FIXED_DT)

    assert sim.player.x == x_no_momento_do_pulo
    assert cesta_origem.x != x_no_momento_do_pulo
    assert sim.player.y < START_WORLD_Y


def test_colisao_one_way_so_na_descida() -> None:
    """
    Verifica que as cestas são plataformas one-way:
    - Atravessar uma cesta subindo (`vy < 0`) NÃO ativa pouso.
    - Cruzar o topo da cesta descendo (`vy > 0`) acopla o ovo à cesta.
    """
    sim = WorldSimulation(seed=303)
    cesta_alvo = Platform(
        id="alvo-teste",
        kind="slide",
        x=sim.player.x,
        y=sim.player.y - 110.0,
        width=150.0,
        speed=0.0,
    )
    sim.platforms = [sim.platforms[0], cesta_alvo]

    sim.request_jump()
    passou_subindo_sem_pousar = False
    pousou_na_descida = False

    for _ in range(120):
        sim.step_fixed(FIXED_DT)
        if sim.player.vy < 0 and sim.player.y < cesta_alvo.y:
            passou_subindo_sem_pousar = True
            assert not sim.player.is_grounded
        if sim.player.attached_platform_id == "alvo-teste":
            pousou_na_descida = True
            break

    assert passou_subindo_sem_pousar is True
    assert pousou_na_descida is True
    assert sim.player.y == cesta_alvo.y


def test_alcancabilidade_gerador_multiplas_seeds() -> None:
    """
    Verifica que todas as cestas geradas em sequência para diversas seeds
    possuem janela temporal de pouso válida secondo o `ReachabilityValidator`.
    """
    for seed in (1, 7, 42, 99, 2026, 20261027):
        gen = LevelGenerator(seed=seed)
        plataformas = [gen.create_start_platform(START_WORLD_Y)]
        gen.generate_up_to(plataformas, START_WORLD_Y - 2500.0)
        assert len(plataformas) >= 18

        for i in range(len(plataformas) - 1):
            ancora = plataformas[i]
            alvo = plataformas[i + 1]
            ok, janela_s, _ = ReachabilityValidator.compute_timing_window(ancora, alvo)
            assert ok is True, f"Transição inalcançável na seed={seed} entre {ancora.id} e {alvo.id}"
            assert janela_s > 0.10


def test_determinismo_mesma_seed() -> None:
    """Mesma seed deve gerar exatamente a mesma sequência de plataformas."""
    gen_a = LevelGenerator(seed=777)
    plats_a = gen_a.generate_up_to([], START_WORLD_Y - 3000.0)

    gen_b = LevelGenerator(seed=777)
    plats_b = gen_b.generate_up_to([], START_WORLD_Y - 3000.0)

    assert len(plats_a) == len(plats_b)
    for pa, pb in zip(plats_a, plats_b):
        assert pa.id == pb.id
        assert pa.kind == pb.kind
        assert pa.x == pb.x
        assert pa.y == pb.y
        assert pa.speed == pb.speed


def test_altura_metros_e_persistencia_recorde(tmp_path: Path) -> None:
    """
    Verifica o cálculo de `height_m` (100 px = 1 m), que a pontuação nunca
    diminui ao descer, e a persistência JSON com tratamento de corrupção.
    """
    assert compute_height_m(1000.0, 1000.0) == 0
    assert compute_height_m(1000.0, 901.0) == 0
    assert compute_height_m(1000.0, 900.0) == 1
    assert compute_height_m(1000.0, -11000.0) == 120

    sim = WorldSimulation(seed=555)
    sim.score.update(START_WORLD_Y - 450.0)
    assert sim.score.height_m == 4
    # Mesmo se o ovo cair para uma posição inferior, height_m não diminui
    sim.score.update(START_WORLD_Y - 120.0)
    assert sim.score.height_m == 4

    caminho_save = tmp_path / "save_test.json"
    repo = SaveRepository(path=caminho_save)
    dados = GameSaveData(adventure_record_m=78, music_enabled=False, sfx_enabled=True)
    repo.save(dados)

    lido = repo.load()
    assert lido.adventure_record_m == 78
    assert lido.music_enabled is False
    assert lido.sfx_enabled is True

    # Corrompe o arquivo e garante que load() recupera defaults sem crash
    caminho_save.write_text("{json_invalido", encoding="utf-8")
    recuperado = repo.load()
    assert recuperado.adventure_record_m == 0
    assert recuperado.music_enabled is True

# -*- coding: utf-8 -*-
"""Cálculo de altitude em metros lúdicos e persistência de recordes/opções."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from egg_game.core.constants import PIXELS_PER_METER, START_WORLD_Y


def compute_height_m(start_world_y: float, min_world_y_reached: float) -> int:
    """
    Calcula a altura em metros lúdicos conforme PRD §10.2:
    `max_height_px = max(0, start_world_y - min_world_y_reached)`
    `height_m = floor(max_height_px / 100)`
    """
    max_height_px = max(0.0, start_world_y - min_world_y_reached)
    return int(math.floor(max_height_px / PIXELS_PER_METER))


@dataclass
class ScoreTracker:
    """Rastreia a maior altitude atingida na tentativa atual (nunca diminui ao cair)."""

    start_world_y: float = START_WORLD_Y
    min_world_y_reached: float = START_WORLD_Y
    height_m: int = 0

    def reset(self, start_world_y: float = START_WORLD_Y) -> None:
        self.start_world_y = start_world_y
        self.min_world_y_reached = start_world_y
        self.height_m = 0

    def update(self, current_world_y: float) -> int:
        if current_world_y < self.min_world_y_reached:
            self.min_world_y_reached = current_world_y
            self.height_m = compute_height_m(self.start_world_y, self.min_world_y_reached)
        return self.height_m


@dataclass
class GameSaveData:
    """Estrutura de dados persistida em JSON (PRD §17)."""

    schema_version: int = 1
    adventure_record_m: int = 0
    music_enabled: bool = True
    sfx_enabled: bool = True
    reduced_motion: bool = False
    tutorial_seen: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "records": {"adventure_height": int(self.adventure_record_m)},
            "settings": {
                "music_enabled": bool(self.music_enabled),
                "sfx_enabled": bool(self.sfx_enabled),
                "reduced_motion": bool(self.reduced_motion),
            },
            "tutorial_seen": bool(self.tutorial_seen),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameSaveData":
        records = data.get("records", {}) if isinstance(data.get("records"), dict) else {}
        settings = data.get("settings", {}) if isinstance(data.get("settings"), dict) else {}
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            adventure_record_m=max(0, int(records.get("adventure_height", 0))),
            music_enabled=bool(settings.get("music_enabled", True)),
            sfx_enabled=bool(settings.get("sfx_enabled", True)),
            reduced_motion=bool(settings.get("reduced_motion", False)),
            tutorial_seen=bool(data.get("tutorial_seen", False)),
        )


@dataclass
class SaveRepository:
    """Persiste recordes e configurações em arquivo JSON com escrita atômica."""

    path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "save_data.json"
    )

    def load(self) -> GameSaveData:
        try:
            if self.path.exists():
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    return GameSaveData.from_dict(raw)
        except Exception:
            pass
        return GameSaveData()

    def save(self, data: GameSaveData) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.path.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(data.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp_path.replace(self.path)
        except Exception:
            pass

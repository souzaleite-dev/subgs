"""
Gerador de dataset sintetico de imagens orbitais (estilo Sentinel-2 RGB).

Como o objetivo e uma POC reproduzivel e 100% offline, geramos
proceduralmente patches que imitam tres condicoes de cobertura do solo:

  - floresta_saudavel : verde dominante, textura densa
  - desmatamento      : solo exposto (marrom/bege), clareiras geometricas
  - queimada          : tons escuros + brasas (vermelho/laranja)

O pipeline de treino (train.py) tambem aceita um dataset REAL: basta
substituir as imagens em data/dataset/<classe>/ por recortes reais
(ex.: Sentinel-2 / Landsat) mantendo os mesmos nomes de classe.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import CLASSES, DATASET_DIR, IMAGES_PER_CLASS, IMG_SIZE, ensure_dirs


def _noise(size: int, scale: float = 1.0) -> np.ndarray:
    """Ruido suavizado para dar textura organica."""
    base = np.random.rand(size, size)
    # suavizacao simples por media de vizinhos (sem dependencia de scipy)
    k = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=float)
    k /= k.sum()
    pad = np.pad(base, 1, mode="edge")
    out = np.zeros_like(base)
    for i in range(3):
        for j in range(3):
            out += k[i, j] * pad[i:i + size, j:j + size]
    return np.clip(out * scale, 0, 1)


def _floresta(size: int) -> np.ndarray:
    g = 0.45 + 0.4 * _noise(size)            # verde forte e variado
    r = 0.10 + 0.20 * _noise(size)
    b = 0.10 + 0.18 * _noise(size)
    return np.stack([r, g, b], axis=-1)


def _desmatamento(size: int) -> np.ndarray:
    # base de solo exposto (marrom/bege)
    r = 0.55 + 0.30 * _noise(size)
    g = 0.40 + 0.25 * _noise(size)
    b = 0.25 + 0.20 * _noise(size)
    img = np.stack([r, g, b], axis=-1)
    # clareiras geometricas (retangulos de solo bem claro) e restos de verde
    for _ in range(np.random.randint(1, 4)):
        x, y = np.random.randint(0, size - 12, 2)
        w, h = np.random.randint(8, 22, 2)
        img[y:y + h, x:x + w, 0] = np.clip(img[y:y + h, x:x + w, 0] + 0.2, 0, 1)
        img[y:y + h, x:x + w, 1] = np.clip(img[y:y + h, x:x + w, 1] - 0.05, 0, 1)
    return img


def _agua(size: int) -> np.ndarray:
    # corpos d'agua: azul/esverdeado escuro, textura suave
    b = 0.35 + 0.30 * _noise(size)
    g = 0.20 + 0.22 * _noise(size)
    r = 0.06 + 0.12 * _noise(size)
    img = np.stack([r, g, b], axis=-1)
    # reflexos claros esparsos
    refl = _noise(size, 1.3) > 0.82
    img[refl] = np.clip(img[refl] + 0.18, 0, 1)
    return img


GENERATORS = {
    "floresta": _floresta,
    "desmatamento": _desmatamento,
    "agua": _agua,
}


def make_image(classe: str, size: int = IMG_SIZE) -> Image.Image:
    arr = GENERATORS[classe](size)
    arr = (np.clip(arr, 0, 1) * 255).astype("uint8")
    return Image.fromarray(arr, "RGB")


def generate(per_class: int = IMAGES_PER_CLASS) -> Path:
    """Gera o dataset completo em data/dataset/<classe>/."""
    ensure_dirs()
    for classe in CLASSES:
        out_dir = DATASET_DIR / classe
        out_dir.mkdir(parents=True, exist_ok=True)
        for i in range(per_class):
            make_image(classe).save(out_dir / f"{classe}_{i:04d}.png")
        print(f"  {classe}: {per_class} imagens -> {out_dir}")
    print(f"Dataset gerado em: {DATASET_DIR}")
    return DATASET_DIR


if __name__ == "__main__":
    np.random.seed(42)
    generate()

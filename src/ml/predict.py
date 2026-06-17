"""
Inferencia da CNN: classifica uma imagem orbital em uma das 3 classes.

Uso programatico:
    from src.ml.predict import predict_image
    resultado = predict_image("caminho/para/imagem.png")

Uso CLI:
    python -m src.ml.predict caminho/para/imagem.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import CLASSES, CLASSES_PATH, IMG_SIZE, MODEL_PATH

_model = None
_class_names = None


def _load():
    global _model, _class_names
    if _model is None:
        import tensorflow as tf
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo nao encontrado em {MODEL_PATH}. "
                "Execute primeiro: python -m src.ml.train"
            )
        _model = tf.keras.models.load_model(MODEL_PATH)
        if CLASSES_PATH.exists():
            _class_names = json.loads(CLASSES_PATH.read_text())
        else:
            _class_names = CLASSES
    return _model, _class_names


def predict_image(path: str | Path) -> dict:
    """Retorna classe, confianca e probabilidades por classe."""
    model, class_names = _load()
    img = Image.open(path).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    arr = np.expand_dims(np.array(img), axis=0).astype("float32")
    probs = model.predict(arr, verbose=0)[0]
    idx = int(np.argmax(probs))
    prob_map = {c: float(p) for c, p in zip(class_names, probs)}
    return {
        "imagem": str(path),
        "classe": class_names[idx],
        "confianca": float(probs[idx]),
        "prob_floresta": prob_map.get("floresta"),
        "prob_desmate": prob_map.get("desmatamento"),
        "prob_agua": prob_map.get("agua"),
        "probabilidades": prob_map,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m src.ml.predict <caminho_imagem>")
        sys.exit(1)
    r = predict_image(sys.argv[1])
    print(json.dumps(r, ensure_ascii=False, indent=2))

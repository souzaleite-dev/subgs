"""
Treino da CNN de classificacao de cobertura do solo (visao computacional).

Usa TRANSFER LEARNING com MobileNetV2 (pre-treinada na ImageNet) sobre o
dataset REAL EuroSAT (recortes Sentinel-2). Se o dataset real nao existir,
cai para o dataset sintetico (offline). Se os pesos ImageNet nao puderem ser
baixados, usa uma CNN compacta treinada do zero.

Classes (config.CLASSES): floresta, desmatamento, agua.

Gera artefatos para o relatorio/PDF em assets/:
  - assets/treino_historico.png    (curvas de acuracia/perda)
  - assets/matriz_confusao.png     (matriz de confusao na validacao)
  - assets/amostras_predicao.png   (exemplos classificados)
E salva o modelo em src/ml/model/sentinela_cnn.keras
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import (
    ASSETS_DIR, CLASSES, CLASSES_PATH, DATASET_DIR, DATASET_REAL_DIR, IMG_SIZE,
    MODEL_DIR, MODEL_PATH, ensure_dirs,
)


def _build_transfer(n_classes: int):
    """MobileNetV2 (ImageNet) congelada + cabeca densa. Retorna (model, nome)."""
    import tensorflow as tf
    from tensorflow.keras import layers, models
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    base = MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                       include_top=False, weights="imagenet")
    base.trainable = False
    inputs = layers.Input((IMG_SIZE, IMG_SIZE, 3))
    x = layers.RandomFlip("horizontal")(inputs)
    x = layers.RandomRotation(0.1)(x)
    x = preprocess_input(x)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    out = layers.Dense(n_classes, activation="softmax")(x)
    model = models.Model(inputs, out)
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    return model, "MobileNetV2 (transfer learning, ImageNet)"


def _build_simple(n_classes: int):
    """CNN compacta treinada do zero (fallback sem internet)."""
    import tensorflow as tf
    from tensorflow.keras import layers, models
    model = models.Sequential([
        layers.Input((IMG_SIZE, IMG_SIZE, 3)),
        layers.Rescaling(1.0 / 255),
        layers.Conv2D(16, 3, activation="relu", padding="same"),
        layers.MaxPooling2D(),
        layers.Conv2D(32, 3, activation="relu", padding="same"),
        layers.MaxPooling2D(),
        layers.Conv2D(64, 3, activation="relu", padding="same"),
        layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(64, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(n_classes, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    return model, "CNN compacta (do zero)"


def _plot_history(history, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h = history.history
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(h["accuracy"], label="treino")
    ax[0].plot(h.get("val_accuracy", []), label="validacao")
    ax[0].set_title("Acuracia"); ax[0].set_xlabel("epoca"); ax[0].legend()
    ax[1].plot(h["loss"], label="treino")
    ax[1].plot(h.get("val_loss", []), label="validacao")
    ax[1].set_title("Perda"); ax[1].set_xlabel("epoca"); ax[1].legend()
    fig.suptitle("SENTINELA ORBITAL - Treino da CNN (EuroSAT / Sentinel-2)")
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def _plot_confusion(model, val_ds, class_names, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix
    y_true, y_pred = [], []
    for imgs, labels in val_ds:
        preds = model.predict(imgs, verbose=0)
        y_pred.extend(np.argmax(preds, axis=1)); y_true.extend(labels.numpy())
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5.5, 5))
    im = ax.imshow(cm, cmap="YlOrRd")
    ax.set_xticks(range(len(class_names))); ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=30, ha="right"); ax.set_yticklabels(class_names)
    ax.set_xlabel("Predito"); ax.set_ylabel("Real"); ax.set_title("Matriz de Confusao (validacao)")
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            ax.text(j, i, cm[i, j], ha="center", va="center")
    fig.colorbar(im, fraction=0.046); fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)
    return float(np.trace(cm) / cm.sum())


def _plot_samples(model, val_ds, class_names, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    imgs, labels = next(iter(val_ds))
    preds = model.predict(imgs, verbose=0)
    n = min(9, len(imgs))
    fig, axes = plt.subplots(3, 3, figsize=(7, 7))
    for k, ax in enumerate(axes.flat):
        if k >= n:
            ax.axis("off"); continue
        ax.imshow(imgs[k].numpy().astype("uint8"))
        p = int(np.argmax(preds[k])); ok = (p == int(labels[k]))
        ax.set_title(f"{class_names[p]}\n{preds[k][p]*100:.0f}%",
                     color=("green" if ok else "red"), fontsize=8)
        ax.axis("off")
    fig.suptitle("Exemplos de classificacao (validacao)")
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def _dataset_dir():
    """Prefere o dataset REAL (EuroSAT); senao gera o sintetico."""
    if any(DATASET_REAL_DIR.glob("*/*.jpg")) or any(DATASET_REAL_DIR.glob("*/*.png")):
        print(f"Usando dataset REAL (EuroSAT/Sentinel-2): {DATASET_REAL_DIR}")
        return DATASET_REAL_DIR
    print("Dataset real ausente. Gerando dataset sintetico (fallback)...")
    from src.ml import dataset as ds
    np.random.seed(42)
    ds.generate()
    return DATASET_DIR


def train(epochs: int = 8, batch_size: int = 32, seed: int = 42):
    import tensorflow as tf
    ensure_dirs()
    data_dir = _dataset_dir()
    tf.random.set_seed(seed)

    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="training", seed=seed,
        image_size=(IMG_SIZE, IMG_SIZE), batch_size=batch_size, class_names=CLASSES)
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="validation", seed=seed,
        image_size=(IMG_SIZE, IMG_SIZE), batch_size=batch_size, class_names=CLASSES)
    class_names = train_ds.class_names
    print("Classes:", class_names)

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(800).prefetch(AUTOTUNE)
    val_ds = val_ds.cache().prefetch(AUTOTUNE)

    try:
        model, arq = _build_transfer(len(class_names))
    except Exception as e:
        print(f"Transfer learning indisponivel ({e}). Usando CNN compacta.")
        model, arq = _build_simple(len(class_names))
    print("Arquitetura:", arq)

    history = model.fit(train_ds, validation_data=val_ds, epochs=epochs)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_PATH)
    CLASSES_PATH.write_text(json.dumps(class_names, ensure_ascii=False, indent=2))
    print(f"Modelo salvo em: {MODEL_PATH}")

    _plot_history(history, ASSETS_DIR / "treino_historico.png")
    acc = _plot_confusion(model, val_ds, class_names, ASSETS_DIR / "matriz_confusao.png")
    _plot_samples(model, val_ds, class_names, ASSETS_DIR / "amostras_predicao.png")
    print(f"Acuracia de validacao (matriz): {acc*100:.2f}%")
    return model


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Treino da CNN SENTINELA ORBITAL")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()
    train(epochs=args.epochs, batch_size=args.batch)

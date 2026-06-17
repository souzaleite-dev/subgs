"""
Gera o diagrama de arquitetura da solucao em assets/arquitetura.png
(usado no README e no PDF de entrega).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from config.config import ASSETS_DIR, ensure_dirs


def caixa(ax, x, y, w, h, texto, cor):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                linewidth=1.5, edgecolor="#333",
                                facecolor=cor, alpha=0.92))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center",
            fontsize=9, weight="bold", wrap=True)


def seta(ax, p1, p2):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=16,
                                 linewidth=1.6, color="#444"))


def gerar():
    ensure_dirs()
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 9); ax.axis("off")
    ax.set_title("SENTINELA ORBITAL — Arquitetura da Solucao",
                 fontsize=14, weight="bold")

    # Fontes de dados (3)
    caixa(ax, 0.3, 6.7, 2.7, 1.4, "Imagem Sentinel-2\n(EuroSAT - real)", "#aed6f1")
    caixa(ax, 0.3, 3.9, 2.7, 1.4, "NASA EONET + GIBS\n(fogo/imagem reais)", "#f1948a")
    caixa(ax, 0.3, 1.1, 2.7, 1.4, "Open-Meteo + ESP32\n(solo real)", "#abebc6")

    # Processamento
    caixa(ax, 3.7, 6.7, 2.8, 1.4, "CNN MobileNetV2\n(desmatamento)", "#5dade2")
    caixa(ax, 3.7, 3.9, 2.8, 1.4, "Risco de fogo real\n(focos proximos)", "#ec7063")
    caixa(ax, 3.7, 1.1, 2.8, 1.4, "Indice de risco\n(solo)", "#58d68d")

    # Fusao
    caixa(ax, 7.2, 3.85, 2.5, 1.5, "PIPELINE\nFusao 3 fontes\n(risco da area)", "#f5b041")

    # Persistencia + Nuvem + Saida
    caixa(ax, 10.1, 6.4, 1.7, 1.5, "AWS S3+Dynamo\nLambda", "#f1948a")
    caixa(ax, 10.1, 3.95, 1.7, 1.3, "SQLite", "#d7bde2")
    caixa(ax, 10.1, 1.2, 1.7, 1.4, "Dashboard\nStreamlit", "#f7dc6f")

    # Setas fonte -> processamento
    seta(ax, (3.0, 7.4), (3.7, 7.4))
    seta(ax, (3.0, 4.6), (3.7, 4.6))
    seta(ax, (3.0, 1.8), (3.7, 1.8))
    # processamento -> fusao (convergencia)
    seta(ax, (6.5, 7.4), (7.4, 5.2))
    seta(ax, (6.5, 4.6), (7.2, 4.6))
    seta(ax, (6.5, 1.8), (7.4, 4.0))
    # fusao -> saidas
    seta(ax, (9.7, 5.1), (10.1, 7.0))
    seta(ax, (9.7, 4.6), (10.1, 4.6))
    seta(ax, (9.7, 4.1), (10.1, 1.9))

    fig.tight_layout()
    out = ASSETS_DIR / "arquitetura.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"Diagrama salvo em: {out}")


if __name__ == "__main__":
    gerar()

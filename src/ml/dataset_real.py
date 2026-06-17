"""
Dataset REAL de imagens de satelite (EuroSAT - recortes Sentinel-2).

Baixa o EuroSAT (RGB) de um mirror publico (sem autenticacao), extrai e
monta um dataset balanceado de 3 classes do projeto a partir do mapeamento
em config.EUROSAT_MAP:

  floresta     <- Forest
  desmatamento <- AnnualCrop, Pasture, PermanentCrop   (uso antropico/agro)
  agua         <- River, SeaLake

Resultado em data/dataset_real/<classe>/. Se o download falhar, o treino
cai automaticamente para o dataset sintetico (src/ml/dataset.py).
"""
from __future__ import annotations

import random
import shutil
import ssl
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import (
    DATA_DIR, DATASET_REAL_DIR, EUROSAT_MAP, EUROSAT_POR_CLASSE, EUROSAT_URL,
    ensure_dirs,
)

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

ZIP_PATH = DATA_DIR / "EuroSAT.zip"
EXTRACT_DIR = DATA_DIR / "_eurosat_raw"


def baixar(url: str = EUROSAT_URL, destino: Path = ZIP_PATH) -> bool:
    if destino.exists() and destino.stat().st_size > 1_000_000:
        print(f"  zip ja existe ({destino.stat().st_size/1e6:.0f} MB)")
        return True
    ensure_dirs()
    print(f"  baixando EuroSAT de {url} ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SentinelaOrbital/1.0"})
        with urllib.request.urlopen(req, timeout=60, context=_CTX) as r, \
                open(destino, "wb") as f:
            baixado = 0
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                baixado += len(chunk)
                if baixado % (10 << 20) < (1 << 20):
                    print(f"    {baixado/1e6:.0f} MB")
        print(f"  download concluido ({baixado/1e6:.0f} MB)")
        return True
    except Exception as e:
        print(f"  FALHA no download: {e}")
        if destino.exists():
            destino.unlink(missing_ok=True)
        return False


def _achar_classe(raiz: Path, nome: str) -> Path | None:
    for p in raiz.rglob(nome):
        if p.is_dir() and any(p.glob("*.jpg")):
            return p
    return None


def montar(por_classe: int = EUROSAT_POR_CLASSE, seed: int = 42) -> Path | None:
    if not baixar():
        return None
    print("  extraindo...")
    if EXTRACT_DIR.exists():
        shutil.rmtree(EXTRACT_DIR, ignore_errors=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(ZIP_PATH) as z:
            z.extractall(EXTRACT_DIR)
    except Exception as e:
        print(f"  FALHA ao extrair: {e}")
        return None

    rng = random.Random(seed)
    if DATASET_REAL_DIR.exists():
        shutil.rmtree(DATASET_REAL_DIR, ignore_errors=True)

    for classe, fontes in EUROSAT_MAP.items():
        out_dir = DATASET_REAL_DIR / classe
        out_dir.mkdir(parents=True, exist_ok=True)
        # coleta imagens das subclasses EuroSAT mapeadas
        arquivos = []
        for fonte in fontes:
            pasta = _achar_classe(EXTRACT_DIR, fonte)
            if pasta:
                arquivos.append(list(pasta.glob("*.jpg")))
            else:
                print(f"    aviso: classe EuroSAT '{fonte}' nao encontrada")
        # amostragem balanceada entre as fontes
        por_fonte = max(1, por_classe // max(1, len(arquivos)))
        selecionados = []
        for lista in arquivos:
            rng.shuffle(lista)
            selecionados += lista[:por_fonte]
        rng.shuffle(selecionados)
        for i, src in enumerate(selecionados[:por_classe]):
            shutil.copy(src, out_dir / f"{classe}_{i:04d}.jpg")
        print(f"  {classe}: {len(list(out_dir.glob('*.jpg')))} imagens reais")

    shutil.rmtree(EXTRACT_DIR, ignore_errors=True)
    print(f"Dataset real montado em: {DATASET_REAL_DIR}")
    return DATASET_REAL_DIR


if __name__ == "__main__":
    montar()

"""
Popula o banco com dados de demonstracao para o dashboard e o relatorio:
  - leituras de sensores (cenario normal + critico);
  - deteccoes de imagem usando imagens REAIS do EuroSAT (se o modelo existir);
  - executa a fusao (sensor + desmatamento + fogo real NASA) e gera alertas.
"""
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import CLASSES, DATASET_REAL_DIR, MODEL_PATH
from src.db.database import init_db, insert_detection
from src.iot import sensor_simulator as sim
from src.pipeline import pipeline


def main():
    init_db()
    print("Lendo sensores de solo REAIS (Open-Meteo)...")
    from config.config import AREA_LAT, AREA_LON
    from src.data.open_meteo import ler_solo
    leituras, og = ler_solo(AREA_LAT, AREA_LON, serie=True)
    for r in leituras:
        sim.insert_sensor_reading(r)
    print(f"  {len(leituras)} leituras de solo [{og}]")

    if MODEL_PATH.exists():
        print("Modelo encontrado. Classificando imagens reais (EuroSAT)...")
        from src.ml.predict import predict_image
        # desmatamento por ultimo -> vira a deteccao "atual" no dashboard
        for classe in ["floresta", "agua", "desmatamento"]:
            reais = list((DATASET_REAL_DIR / classe).glob("*.jpg"))
            tmp = ROOT / "data" / f"demo_{classe}.png"
            if reais:
                shutil.copy(random.choice(reais), tmp)
            else:
                from src.ml.dataset import make_image
                make_image(classe).save(tmp)
            r = predict_image(tmp)
            insert_detection(r)
            print(f"  {classe:13s} -> {r['classe']} ({r['confianca']*100:.1f}%)")
    else:
        print("Modelo nao treinado (pulei deteccoes). Rode: python -m src.ml.train")

    print("Executando fusao (sensor + desmatamento + fogo real)...")
    a = pipeline.executar(persistir=True, nuvem=False)
    print(f"Alerta: nivel={a['nivel']} risco_total={a['risco_total']} "
          f"(solo={a['risco_sensor']} desmat={a['risco_imagem']} fogo={a['risco_fogo']})")
    print("Demo populada com sucesso.")


if __name__ == "__main__":
    main()

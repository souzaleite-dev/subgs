"""
Pipeline de fusao de dados do SENTINELA ORBITAL.

Combina TRES fontes independentes para decidir o risco da area:

  1. RISCO DO SENSOR  (ESP32 simulado/real)        -> condicoes no solo
  2. RISCO DA IMAGEM  (CNN sobre Sentinel-2/EuroSAT) -> desmatamento
  3. RISCO DE FOGO    (NASA EONET, queimadas reais)  -> focos ativos proximos

Fusao ponderada (pesos renormalizados sobre as fontes disponiveis):
    risco_total = (Ws*sensor + Wi*imagem + Wf*fogo) / (Ws+Wi+Wf)

O resultado vira um ALERTA persistido no banco e (opcionalmente) enviado
para a nuvem (S3 + DynamoDB / fallback local).
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import (
    AREA_LAT, AREA_LON, PESO_FOGO, PESO_IMAGEM, PESO_SENSOR,
    RISCO_SENSOR_LIMIARES,
)
from src.db.database import init_db, insert_alert, latest_detection, latest_sensor


def classificar_nivel(risco: float) -> str:
    if risco < RISCO_SENSOR_LIMIARES["BAIXO"]:
        return "BAIXO"
    if risco < RISCO_SENSOR_LIMIARES["MODERADO"]:
        return "MODERADO"
    if risco < RISCO_SENSOR_LIMIARES["ALTO"]:
        return "ALTO"
    return "CRITICO"


def risco_da_imagem(deteccao: dict | None) -> float:
    """Probabilidade de desmatamento (CNN) convertida em risco 0-100."""
    if not deteccao:
        return 0.0
    return round(100.0 * (deteccao.get("prob_desmate") or 0.0), 1)


def fundir(sensor: dict | None, deteccao: dict | None,
           fogo: dict | None = None) -> dict:
    """Funde sensor + imagem (desmatamento) + fogo real em um alerta."""
    risco_sensor = (sensor or {}).get("risco_sensor", 0.0) or 0.0
    risco_img = risco_da_imagem(deteccao)
    risco_fogo = (fogo or {}).get("score", 0.0) or 0.0

    partes = []
    if sensor:
        partes.append((PESO_SENSOR, risco_sensor))
    if deteccao:
        partes.append((PESO_IMAGEM, risco_img))
    if fogo:
        partes.append((PESO_FOGO, risco_fogo))
    if partes:
        soma_p = sum(w for w, _ in partes)
        risco_total = round(sum(w * v for w, v in partes) / soma_p, 1)
    else:
        risco_total = 0.0
    nivel = classificar_nivel(risco_total)

    classe_img = (deteccao or {}).get("classe", "n/d")
    nfogo = (fogo or {}).get("dentro", 0)
    msg = (f"Fusao -> solo={risco_sensor:.0f} | desmatamento={risco_img:.0f} "
           f"(classe='{classe_img}') | fogo_real={risco_fogo:.0f} "
           f"({nfogo} focos no raio) => risco_total={risco_total:.0f} [{nivel}]")

    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "estacao": (sensor or {}).get("estacao", "n/d"),
        "risco_sensor": round(risco_sensor, 1),
        "risco_imagem": risco_img,
        "risco_fogo": round(risco_fogo, 1),
        "risco_total": risco_total,
        "nivel": nivel,
        "fogo": fogo or {},
        "origem": "fusao_3_fontes",
        "mensagem": msg,
    }


def _fogo_da_area(lat: float = AREA_LAT, lon: float = AREA_LON) -> dict:
    """Busca queimadas reais (NASA) e calcula o risco de fogo para a area."""
    try:
        from src.data.nasa import fetch_wildfires, fire_score
        eventos, origem = fetch_wildfires()
        fs = fire_score(lat, lon, eventos)
        fs["origem"] = origem
        return fs
    except Exception as e:
        print(f"[fogo real indisponivel: {e}]")
        return {"score": 0.0, "dentro": 0, "nearest_km": None, "total": 0}


def executar(persistir: bool = True, nuvem: bool = False,
             lat: float = AREA_LAT, lon: float = AREA_LON) -> dict:
    """Le ultimas leituras + fogo real, funde e gera o alerta."""
    init_db()
    sensor = latest_sensor()
    deteccao = latest_detection()
    fogo = _fogo_da_area(lat, lon)
    alerta = fundir(sensor, deteccao, fogo)

    if persistir:
        insert_alert({
            "ts": alerta["ts"], "estacao": alerta["estacao"],
            "risco_total": alerta["risco_total"], "nivel": alerta["nivel"],
            "origem": alerta["origem"], "mensagem": alerta["mensagem"],
        })
    if nuvem:
        from src.cloud.aws_integration import enviar_para_nuvem
        img = (deteccao or {}).get("imagem")
        alerta["nuvem"] = enviar_para_nuvem(alerta, img)
    return alerta


if __name__ == "__main__":
    import json
    print(json.dumps(executar(persistir=True, nuvem=False), ensure_ascii=False, indent=2))

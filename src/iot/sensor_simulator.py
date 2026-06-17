"""
Simulador de estacao de sensores de solo (ESP32) para deteccao de risco
de incendio florestal.

Sensores emulados (equivalentes ao firmware real em esp32_firmware.ino):
  - DHT22  : temperatura e umidade do ar
  - Sonda  : temperatura e umidade do solo
  - MQ-2   : concentracao de fumaca/gases (ppm)

A partir das leituras calculamos um INDICE DE RISCO DE FOGO (0-100),
inspirado na logica do Fire Weather Index: calor alto + ar/solo secos +
fumaca elevada => risco alto.

As leituras sao gravadas no SQLite e podem, opcionalmente, ser publicadas
via MQTT (paho-mqtt) imitando o envio real do ESP32 para a nuvem.
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import AREA_NOME, RISCO_SENSOR_LIMIARES
from src.db.database import init_db, insert_sensor_reading


def calcular_risco(temp_ar, umid_ar, temp_solo, umid_solo, fumaca_ppm) -> float:
    """Combina as leituras em um indice de risco de fogo (0 a 100)."""
    # Cada componente normalizado para 0..1 (1 = pior caso)
    f_temp = max(0.0, min(1.0, (temp_ar - 20) / 25))        # 20C->0 , 45C->1
    f_seca_ar = max(0.0, min(1.0, (60 - umid_ar) / 60))      # ar seco aumenta risco
    f_seca_solo = max(0.0, min(1.0, (50 - umid_solo) / 50))  # solo seco aumenta risco
    f_fumaca = max(0.0, min(1.0, fumaca_ppm / 800))          # 800ppm -> saturado
    f_temp_solo = max(0.0, min(1.0, (temp_solo - 18) / 30))

    risco = (
        0.28 * f_temp + 0.22 * f_seca_ar + 0.18 * f_seca_solo
        + 0.24 * f_fumaca + 0.08 * f_temp_solo
    ) * 100
    return round(risco, 1)


def classificar_nivel(risco: float) -> str:
    if risco < RISCO_SENSOR_LIMIARES["BAIXO"]:
        return "BAIXO"
    if risco < RISCO_SENSOR_LIMIARES["MODERADO"]:
        return "MODERADO"
    if risco < RISCO_SENSOR_LIMIARES["ALTO"]:
        return "ALTO"
    return "CRITICO"


def gerar_leitura(cenario: str = "aleatorio") -> dict:
    """
    Gera uma leitura. cenario:
      - 'normal'  : floresta umida e fresca (risco baixo)
      - 'critico' : seca + calor + fumaca (risco alto)
      - 'aleatorio': mistura realista
    """
    if cenario == "normal":
        temp_ar = random.uniform(22, 28); umid_ar = random.uniform(65, 90)
        umid_solo = random.uniform(55, 80); fumaca = random.uniform(20, 120)
    elif cenario == "critico":
        temp_ar = random.uniform(36, 44); umid_ar = random.uniform(12, 30)
        umid_solo = random.uniform(8, 25); fumaca = random.uniform(450, 780)
    else:  # aleatorio
        temp_ar = random.uniform(24, 42); umid_ar = random.uniform(20, 85)
        umid_solo = random.uniform(15, 70); fumaca = random.uniform(40, 600)

    temp_solo = temp_ar - random.uniform(1, 5)
    risco = calcular_risco(temp_ar, umid_ar, temp_solo, umid_solo, fumaca)
    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "estacao": AREA_NOME,
        "temp_ar": round(temp_ar, 1),
        "umid_ar": round(umid_ar, 1),
        "temp_solo": round(temp_solo, 1),
        "umid_solo": round(umid_solo, 1),
        "fumaca_ppm": round(fumaca, 1),
        "risco_sensor": risco,
        "nivel": classificar_nivel(risco),
    }


def publicar_mqtt(leitura: dict, broker: str = "test.mosquitto.org",
                  topico: str = "sentinela/sensor") -> bool:
    """Publica a leitura via MQTT (opcional). Retorna True se conseguiu."""
    try:
        import paho.mqtt.publish as publish
        publish.single(topico, json.dumps(leitura), hostname=broker)
        return True
    except Exception as e:  # broker offline / lib ausente -> nao quebra a POC
        print(f"  [MQTT indisponivel: {e}]")
        return False


def rodar(n: int = 10, intervalo: float = 1.0, cenario: str = "aleatorio",
          mqtt: bool = False) -> None:
    init_db()
    print(f"Simulando estacao ESP32 ({cenario}) - {n} leituras\n")
    for i in range(n):
        leitura = gerar_leitura(cenario)
        insert_sensor_reading(leitura)
        if mqtt:
            publicar_mqtt(leitura)
        print(f"[{i+1:02d}] risco={leitura['risco_sensor']:5.1f} "
              f"({leitura['nivel']:8s}) temp={leitura['temp_ar']}C "
              f"umid_solo={leitura['umid_solo']}% fumaca={leitura['fumaca_ppm']}ppm")
        if i < n - 1 and intervalo > 0:
            time.sleep(intervalo)
    print("\nLeituras gravadas no banco.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Simulador de sensores ESP32")
    ap.add_argument("-n", type=int, default=10, help="numero de leituras")
    ap.add_argument("--intervalo", type=float, default=0.5, help="segundos entre leituras")
    ap.add_argument("--cenario", choices=["normal", "critico", "aleatorio"],
                    default="aleatorio")
    ap.add_argument("--mqtt", action="store_true", help="publicar via MQTT")
    args = ap.parse_args()
    rodar(args.n, args.intervalo, args.cenario, args.mqtt)

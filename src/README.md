# src/

Código-fonte do SENTINELA ORBITAL, organizado por responsabilidade.

| Módulo | Conteúdo |
|--------|----------|
| `ml/` | `dataset_real.py` (EuroSAT/Sentinel-2), `dataset.py` (sintético fallback), `train.py` (MobileNetV2 transfer learning), `predict.py` (inferência) |
| `data/` | `nasa.py` — EONET (queimadas reais) + GIBS (imagem de satélite real) |
| `iot/` | `sensor_simulator.py` (ESP32 simulado), `esp32_firmware.ino` (firmware real) |
| `cloud/` | `aws_integration.py` (S3/DynamoDB + fallback), `lambda_function.py` (serverless) |
| `pipeline/` | `pipeline.py` (fusão das 3 fontes -> alerta) |
| `db/` | `database.py` (esquema e acesso ao SQLite) |
| `dashboard/` | `app.py` (dashboard Streamlit) |

## Fluxo de dados

```
imagem Sentinel-2 ─► ml/predict.py (CNN) ─┐
NASA EONET/GIBS  ─► data/nasa.py        ─┼─► pipeline/pipeline.py ─► db (SQLite) ─► dashboard
sensores ESP32   ─► iot/...             ─┘                       └─► cloud (AWS/local)
```

Os módulos são executáveis individualmente (`python -m src.<modulo>.<arquivo>`), o que facilita testes e a demonstração no vídeo.

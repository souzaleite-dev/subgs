# 🛰️ SENTINELA ORBITAL

Monitoramento inteligente de **desmatamento e queimadas** que funde **três fontes**: visão computacional sobre **imagens reais de satélite (Sentinel-2)**, **dados reais da NASA** (queimadas EONET + imagens GIBS) e **sensores de solo (IoT/ESP32)**.

> **FIAP — Graduação em Inteligência Artificial · Sub Global Solution 2026.1**
> Tema: *Como a IA e as tecnologias digitais podem transformar a nova economia espacial e gerar impacto positivo na Terra?*

---

## 👤 Autor

| Nome | RM |
|------|----|
| Bruno de Souza Leite | RM567213 |

## 👩‍🏫 Professores

- **Tutor(a):** _<nome do tutor>_
- **Coordenador(a):** _<nome do coordenador>_

---

## 📌 Descrição

O **SENTINELA ORBITAL** combina três sinais independentes em um **pipeline de fusão de risco**:

1. **Imagem orbital (Sentinel-2)** → uma **CNN MobileNetV2 (transfer learning)**, treinada no dataset **EuroSAT** de recortes reais do satélite Sentinel-2, classifica a cobertura do solo em `floresta` / `desmatamento` / `agua` (**~96,7% de acurácia**).
2. **Dados reais da NASA** → **EONET** fornece queimadas ativas **reais** (coordenadas) e **GIBS** fornece **imagens de satélite reais** (MODIS true-color) da área — ambos abertos, sem chave de API.
3. **Sensores de solo (Open-Meteo)** → temperatura/umidade do **solo** e do ar e CO **reais** (Open-Meteo, sem chave) geram um **índice de risco**; firmware **ESP32** para hardware físico, simulador como *fallback*.

O pipeline funde os três riscos (pesos 0,30 / 0,30 / 0,40), classifica o nível (**BAIXO / MODERADO / ALTO / CRÍTICO**), persiste no **SQLite** e envia para a **AWS** (S3 + DynamoDB via Lambda, com *fallback* local). Tudo é visualizado em um **dashboard Streamlit** "mission control".

> Robustez: se faltar internet, há *fallback* automático (dataset sintético, cache/amostra de queimadas, *fallback* local da nuvem) — a POC nunca quebra.

### Arquitetura

![Arquitetura](assets/arquitetura.png)

---

## 🧰 Tecnologias

| Área | Tecnologia |
|------|-----------|
| Deep Learning / Visão Computacional | TensorFlow/Keras, **MobileNetV2 (transfer learning, ImageNet)** |
| Dados reais de satélite | **EuroSAT (Sentinel-2)**, **NASA EONET**, **NASA GIBS (MODIS)** |
| Dados reais de solo/ar | **Open-Meteo** (temp/umidade do solo, CO/qualidade do ar) |
| IoT / Sensores | ESP32 (firmware C/Arduino) para hardware físico, simulador *fallback* |
| Nuvem | AWS S3, DynamoDB, Lambda (boto3) + *fallback* local |
| Dados | SQLite, Pandas |
| Dashboard | Streamlit + Plotly |
| Relatório / análise | Matplotlib, scikit-learn, fpdf2 |

---

## 📁 Estrutura

```
SUBGS/
├── assets/        # diagramas e figuras (arquitetura, treino, satélite real)
├── config/        # config.py: caminhos, classes, limiares, pesos, NASA
├── document/      # relatório e PDF de entrega
├── scripts/       # diagramas, dados de demo, PDF, screenshot
├── src/
│   ├── ml/        # dataset sintético, dataset_real (EuroSAT), treino, inferência
│   ├── data/      # nasa.py (EONET/GIBS) + open_meteo.py (solo/ar reais)
│   ├── iot/       # simulador de sensores + firmware ESP32
│   ├── cloud/     # integração AWS (S3/DynamoDB) e função Lambda
│   ├── pipeline/  # fusão das 3 fontes -> alerta
│   ├── db/        # camada SQLite
│   └── dashboard/ # app Streamlit
├── requirements.txt
└── README.md
```

---

## ▶️ Como executar

```bash
# 1. Dependências (Python 3.10+; testado em 3.12)
pip install -r requirements.txt

# 2. Baixar dataset REAL EuroSAT (Sentinel-2) — ~94 MB
python -m src.ml.dataset_real

# 3. Treinar a CNN (transfer learning MobileNetV2)
python -m src.ml.train

# 4. Popular o banco (classifica imagens reais + busca fogo real da NASA)
python scripts/gerar_dados_demo.py

# 5. Abrir o dashboard
streamlit run src/dashboard/app.py
```

### Outros comandos
```bash
python -m src.data.nasa                # testa EONET (fogo real) + GIBS (imagem real)
python -m src.data.open_meteo          # testa leitura REAL de solo/ar (Open-Meteo)
python -m src.iot.sensor_simulator --cenario critico -n 10
python -m src.pipeline.pipeline        # roda a fusão das 3 fontes
python scripts/gerar_pdf.py            # gera o PDF de entrega
python scripts/screenshot_dash.py      # captura screenshot do dashboard (precisa playwright)
```

> Se o dataset real não for baixado, o treino cai automaticamente para um dataset **sintético** offline.

---

## ☁️ Dados reais e fallback

- **NASA EONET / GIBS**: abertos, **sem chave de API**. Se não houver internet, usa cache e amostra embutida.
- **Open-Meteo** (solo/ar/CO reais): **sem chave**; *fallback* para o simulador ESP32 se offline.
- **AWS**: roda **100% offline** por padrão; com `aws configure` válido, grava em S3/DynamoDB reais.
- **EuroSAT**: baixado de mirror público; *fallback* sintético se indisponível.

---

## 🎥 Vídeo demonstrativo

**YouTube (Não Listado):** https://youtu.be/e5dnb7D5-fM

## 📄 Licença

Projeto acadêmico — FIAP 2026. Uso educacional.

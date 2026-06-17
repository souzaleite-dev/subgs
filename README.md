# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href="https://www.fiap.com.br/"><img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Administração Paulista" border="0" width="40%" height="40%"></a>
</p>

<br>

# 🛰️ SENTINELA ORBITAL

## Sub Global Solution 2026.1 — Nova Economia Espacial

Monitoramento inteligente de **desmatamento e queimadas** que funde **três fontes reais**: visão computacional sobre **imagens reais de satélite (Sentinel-2)**, **dados reais da NASA** (queimadas EONET + imagens GIBS) e **sensores de solo (IoT/ESP32)**.

## 👨‍🎓 Integrante

- **Bruno de Souza Leite** — RM567213

## 👩‍🏫 Professores

### Tutor(a)
- _A preencher_

### Coordenador(a)
- _A preencher_

---

## 📜 Descrição

O **SENTINELA ORBITAL** é uma Prova de Conceito (POC) que responde à pergunta da Sub GS 2026.1 — *como a Inteligência Artificial e as tecnologias digitais podem transformar a nova economia espacial e gerar impacto positivo na Terra?* — combinando **três sinais independentes e reais** em um **pipeline de fusão de risco**:

1. **Imagem orbital (Sentinel-2)** → uma **CNN MobileNetV2 (transfer learning)**, treinada no dataset **EuroSAT** de recortes reais do satélite Sentinel-2, classifica a cobertura do solo em `floresta` / `desmatamento` / `agua` (**~96,7% de acurácia**).
2. **Dados reais da NASA** → **EONET** fornece queimadas ativas **reais** (coordenadas) e **GIBS** fornece **imagens de satélite reais** (MODIS true-color) da área — ambos abertos, sem chave de API.
3. **Sensores de solo (Open-Meteo)** → temperatura/umidade do **solo** e do ar e CO **reais** geram um **índice de risco**; firmware **ESP32** para hardware físico, simulador como *fallback*.

O pipeline funde os três riscos (pesos 0,30 / 0,30 / 0,40), classifica o nível (**BAIXO / MODERADO / ALTO / CRÍTICO**), persiste no **SQLite** e envia para a **AWS** (S3 + DynamoDB via Lambda, com *fallback* local). Tudo é visualizado em um **dashboard Streamlit** "mission control".

> Robustez: se faltar internet, há *fallback* automático (dataset sintético, cache/amostra de queimadas, *fallback* local da nuvem) — a POC nunca quebra.

### Arquitetura

![Arquitetura](assets/arquitetura.png)

### 🧰 Tecnologias

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

## 📁 Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

- **docs**: documentação textual do projeto — relatório técnico (`RELATORIO.md`) e o **PDF único de entrega** (`Sentinela_Orbital_Entrega.pdf`).
- **src**: todo o código-fonte — `ml/` (CNN, dataset, treino, inferência), `data/` (NASA EONET/GIBS + Open-Meteo), `iot/` (simulador + firmware ESP32), `cloud/` (AWS S3/DynamoDB/Lambda), `pipeline/` (fusão das 3 fontes), `db/` (SQLite), `dashboard/` (app Streamlit).
- **data**: dados utilizados/gerados em runtime (dataset EuroSAT, banco SQLite, cache da NASA) — *gerado localmente, fora do versionamento*.
- **assets**: diagramas e figuras (arquitetura, treino, matriz de confusão, dashboard, satélite real) e o `logo-fiap.png`.
- **config**: `config.py` central — caminhos, classes, limiares, pesos da fusão e endpoints da NASA/Open-Meteo.
- **scripts**: utilitários — geração de diagramas, dados de demonstração, capa e do PDF de entrega.
- **README.md**: este guia geral do projeto.

```
SUBGS/
├── assets/        # diagramas, figuras e logo-fiap.png
├── config/        # config.py (caminhos, classes, limiares, pesos, NASA)
├── data/          # dados/artefatos de runtime (fora do versionamento)
├── docs/          # RELATORIO.md + PDF de entrega
├── scripts/       # diagramas, dados de demo, capa, PDF
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

## 📎 Links e Observações

- **Repositório:** https://github.com/souzaleite-dev/subgs
- **Vídeo demonstrativo (YouTube, Não Listado):** https://youtu.be/e5dnb7D5-fM
- **PDF de entrega:** [`docs/Sentinela_Orbital_Entrega.pdf`](docs/Sentinela_Orbital_Entrega.pdf)
- **Decisões técnicas:** três fontes **reais e independentes** para reduzir falso alarme; **transfer learning** (MobileNetV2) para alta acurácia com pouco dado; **fallback offline** em todas as fontes (a POC nunca quebra); **fusão ponderada** renormalizada quando uma fonte falta.
- **Competição:** esta **SUB GS não possui pódio/premiação**, conforme enunciado — não se aplica aceite de participação.

---

## 🔧 Como executar o código

Pré-requisitos: **Python 3.10+** (testado em 3.12) e `pip`.

```bash
# 1. Dependências
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
python -m src.data.nasa            # testa EONET (fogo real) + GIBS (imagem real)
python -m src.data.open_meteo      # testa leitura REAL de solo/ar (Open-Meteo)
python -m src.pipeline.pipeline    # roda a fusão das 3 fontes
python scripts/gerar_pdf.py        # gera o PDF de entrega
python scripts/gerar_capa.py       # gera a capa do projeto
```

> Sem internet, o treino cai automaticamente para um dataset **sintético** offline, e as fontes da NASA/Open-Meteo usam cache/amostra — garantindo a demonstração.

---

## 🗃 Histórico de lançamentos

* **1.0.0 — 16/06/2026**
    * Entrega da Sub Global Solution 2026.1.
    * Fusão das 3 fontes reais (Sentinel-2/CNN + NASA EONET/GIBS + IoT/Open-Meteo).
    * Dashboard Streamlit, persistência SQLite + AWS (fallback local), PDF de entrega.

---

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/souzaleite-dev/subgs">SENTINELA ORBITAL</a> por Bruno de Souza Leite está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>

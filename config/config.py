"""
Configuracoes centrais do projeto SENTINELA ORBITAL.

Todos os caminhos sao resolvidos a partir da raiz do projeto, de forma que
qualquer modulo possa importar daqui sem depender do diretorio de execucao.
"""
from pathlib import Path

# Raiz do projeto (config/ fica diretamente sob a raiz)
ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Diretorios de dados / artefatos
# ---------------------------------------------------------------------------
DATA_DIR = ROOT / "data"
DATASET_DIR = DATA_DIR / "dataset"          # imagens sinteticas de treino
DB_PATH = DATA_DIR / "sentinela.db"         # banco SQLite
LOCAL_CLOUD_DIR = DATA_DIR / "cloud_local"  # fallback local da "nuvem"

MODEL_DIR = ROOT / "src" / "ml" / "model"
MODEL_PATH = MODEL_DIR / "sentinela_cnn.keras"
CLASSES_PATH = MODEL_DIR / "classes.json"

ASSETS_DIR = ROOT / "assets"

# ---------------------------------------------------------------------------
# Visao computacional
# ---------------------------------------------------------------------------
IMG_SIZE = 96                               # imagens IMG_SIZE x IMG_SIZE (MobileNetV2)
CLASSES = ["floresta", "desmatamento", "agua"]
IMAGES_PER_CLASS = 320                      # dataset sintetico (fallback offline)

# Dataset REAL (EuroSAT - imagens Sentinel-2). Mirror publico sem autenticacao.
DATASET_REAL_DIR = DATA_DIR / "dataset_real"
EUROSAT_URL = "https://madm.dfki.de/files/sentinel/EuroSAT.zip"
EUROSAT_POR_CLASSE = 1200                   # imagens por classe do projeto
# Mapeamento EuroSAT -> classes do projeto
# (desmatamento = uso antropico/agropecuaria, principal vetor de desmatamento)
EUROSAT_MAP = {
    "floresta": ["Forest"],
    "desmatamento": ["AnnualCrop", "Pasture", "PermanentCrop"],
    "agua": ["River", "SeaLake"],
}

# ---------------------------------------------------------------------------
# Sensores (ESP32 simulado) e fusao de risco
# ---------------------------------------------------------------------------
# Coordenadas da area monitorada (exemplo: arco do desmatamento, Amazonia)
AREA_NOME = "Estacao Floresta-01 (Amazonia Legal)"
AREA_LAT = -9.97
AREA_LON = -67.81

# Caixa (bbox) para imagem de satelite real via NASA GIBS: [oeste, sul, leste, norte]
AREA_BBOX = (AREA_LON - 2.0, AREA_LAT - 2.0, AREA_LON + 2.0, AREA_LAT + 2.0)

# NASA - dados REAIS (sem chave de API)
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"   # eventos naturais (queimadas)
GIBS_WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
GIBS_LAYER = "MODIS_Terra_CorrectedReflectance_TrueColor"
FOGO_RAIO_KM = 800        # raio (km) p/ considerar focos reais no risco da area

# Open-Meteo - leituras REAIS de solo/ar e qualidade do ar (sem chave de API)
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIRQ = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Limiares do indice de risco de fogo derivado dos sensores (0 a 100)
RISCO_SENSOR_LIMIARES = {
    "BAIXO": 25,
    "MODERADO": 50,
    "ALTO": 75,
    # acima de ALTO -> CRITICO
}

# Pesos da fusao de 3 fontes (somam 1.0): solo (sensor) + imagem orbital
# (CNN/desmatamento) + fogo real (NASA EONET)
PESO_SENSOR = 0.30
PESO_IMAGEM = 0.30
PESO_FOGO = 0.40

# ---------------------------------------------------------------------------
# AWS (opcional - ha fallback local quando nao houver credenciais)
# ---------------------------------------------------------------------------
AWS_REGION = "us-east-1"
S3_BUCKET = "sentinela-orbital-poc"
DYNAMO_TABLE = "sentinela_alertas"


def ensure_dirs():
    """Cria os diretorios de runtime caso ainda nao existam."""
    for d in (DATA_DIR, DATASET_DIR, DATASET_REAL_DIR, LOCAL_CLOUD_DIR,
              MODEL_DIR, ASSETS_DIR):
        d.mkdir(parents=True, exist_ok=True)

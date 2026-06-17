"""
Dashboard SENTINELA ORBITAL (Streamlit) — UI "mission control" com dados reais.

Fontes:
  - CNN (MobileNetV2 + EuroSAT/Sentinel-2 reais): cobertura do solo / desmatamento
  - NASA EONET (queimadas reais) + NASA GIBS (imagem de satelite real)
  - ESP32 simulado: sensores de solo

Resultado primeiro (risco da area por fusao das 3 fontes), evidencias depois.

Executar:
    streamlit run src/dashboard/app.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import (
    AREA_LAT, AREA_LON, AREA_NOME, ASSETS_DIR, DATA_DIR, DATASET_REAL_DIR, MODEL_PATH,
)
from src.data.nasa import fetch_wildfires, fire_score, fetch_gibs
from src.db.database import (
    fetch_recent, init_db, insert_detection, latest_detection, latest_sensor,
)
from src.iot import sensor_simulator as sim
from src.pipeline import pipeline

st.set_page_config(page_title="Sentinela Orbital", page_icon="🛰️", layout="wide")

COR = {"BAIXO": "#34D399", "MODERADO": "#FACC15", "ALTO": "#FB923C", "CRITICO": "#F43F5E"}
MENSAGEM = {
    "BAIXO": "Situacao sob controle. Sem indicios de fogo ou desmatamento.",
    "MODERADO": "Atencao. Condicoes favoraveis a risco — manter monitoramento.",
    "ALTO": "Risco elevado. Possivel foco na area — verificar imediatamente.",
    "CRITICO": "Alerta critico! Acionar resposta e equipes de combate agora.",
}
CLASSE_LABEL = {"floresta": "Floresta", "desmatamento": "Desmatamento",
                "agua": "Agua", "n/d": "Sem leitura"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
:root{
  --bg:#060912; --bg2:#0F1626; --bg3:#16203360;
  --txt:#EAF1FB; --txt2:#7E8BA3; --border:rgba(255,255,255,.07); --accent:#38E1D9;
  --display:'Chakra Petch',sans-serif;
  --font:'IBM Plex Sans',-apple-system,Segoe UI,Roboto,sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
}
html, body, .stApp, p, span, div, label, input, button{ font-family:var(--font); }
#MainMenu, footer {visibility:hidden;}
header[data-testid="stHeader"]{background:transparent; height:0;}
[data-testid="stToolbar"], [data-testid="stDecoration"]{display:none;}
.stApp{
  background:
    radial-gradient(1100px 640px at 8% -8%, rgba(56,225,217,.10), transparent 60%),
    radial-gradient(900px 760px at 102% 112%, rgba(124,140,255,.09), transparent 55%),
    var(--bg);
}
.stApp::before{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:
    linear-gradient(rgba(255,255,255,.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.028) 1px, transparent 1px);
  background-size: 46px 46px;
  -webkit-mask-image: radial-gradient(circle at 50% 22%, #000 0%, transparent 78%);
          mask-image: radial-gradient(circle at 50% 22%, #000 0%, transparent 78%); }
.stApp::after{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.45;
  mix-blend-mode:soft-light;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
.block-container{ position:relative; z-index:1;
  padding-top:1.3rem !important; padding-bottom:2.4rem !important; max-width:1480px;
  animation: soReveal .55s cubic-bezier(.22,.61,.36,1) both; }
@keyframes soReveal{ from{ opacity:0; transform:translateY(10px);} to{ opacity:1; transform:none;} }
h1,h2,h3{ font-family:var(--display) !important; }
h1{ font-size:1.65rem !important; font-weight:600 !important; letter-spacing:.04em; margin:0 !important; }
h2{ font-size:1.15rem !important; font-weight:600 !important; }
h3{ font-size:.98rem !important; font-weight:600 !important; letter-spacing:.02em; }
.so-brand{ font-family:var(--display); font-size:1.55rem; font-weight:600;
  letter-spacing:.16em; text-transform:uppercase; color:var(--txt); display:flex; align-items:center; gap:.55rem; }
.so-brand .dot{ width:9px;height:9px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 14px var(--accent); animation:soPulse 2.4s ease-in-out infinite; }
.so-sub{ color:var(--txt2); font-size:.82rem; margin-top:.25rem; letter-spacing:.02em; }
.so-mono{ font-family:var(--mono); }
.so-kicker{ font-family:var(--mono); font-size:.72rem; letter-spacing:.18em; text-transform:uppercase; color:var(--txt2); }
[data-testid="stVerticalBlockBorderWrapper"]{ position:relative;
  background:linear-gradient(180deg, rgba(20,28,46,.72), rgba(10,14,24,.72));
  border:1px solid var(--border) !important; border-radius:16px !important; padding:1.15rem 1.3rem !important;
  -webkit-backdrop-filter:blur(7px); backdrop-filter:blur(7px);
  box-shadow:0 1px 0 rgba(255,255,255,.04) inset, 0 26px 60px -34px rgba(0,0,0,.9);
  transition:border-color .25s ease, transform .25s ease, box-shadow .25s ease; }
[data-testid="stVerticalBlockBorderWrapper"]:hover{ border-color:rgba(56,225,217,.22) !important; transform:translateY(-2px); }
[data-testid="stVerticalBlockBorderWrapper"]::before,
[data-testid="stVerticalBlockBorderWrapper"]::after{ content:""; position:absolute; width:13px; height:13px;
  pointer-events:none; border:0 solid rgba(56,225,217,.45); }
[data-testid="stVerticalBlockBorderWrapper"]::before{ top:9px; left:9px; border-top-width:1.5px; border-left-width:1.5px; }
[data-testid="stVerticalBlockBorderWrapper"]::after{ bottom:9px; right:9px; border-bottom-width:1.5px; border-right-width:1.5px; }
[data-testid="stMetric"]{ background:rgba(255,255,255,.02); border:1px solid var(--border); border-radius:14px;
  padding:.85rem 1.05rem; transition:border-color .25s ease, transform .25s ease; }
[data-testid="stMetric"]:hover{ border-color:rgba(56,225,217,.2); transform:translateY(-1px); }
[data-testid="stMetricLabel"]{ font-family:var(--display) !important; color:var(--txt2) !important;
  font-size:.72rem !important; font-weight:500 !important; letter-spacing:.12em; text-transform:uppercase; }
[data-testid="stMetricValue"]{ font-family:var(--mono) !important; color:var(--txt) !important;
  font-size:1.6rem !important; font-weight:600 !important; letter-spacing:-.01em; }
[data-testid="stMetricDelta"]{ font-size:.78rem !important; }
.so-pill{ display:inline-flex; align-items:center; gap:.5rem; padding:.32rem .85rem; border-radius:999px;
  font-family:var(--display); font-size:.78rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; border:1px solid transparent; }
.so-pill::before{ content:""; width:8px; height:8px; border-radius:50%; background:currentColor;
  box-shadow:0 0 0 0 currentColor; animation:soPulse 2s ease-in-out infinite; }
.so-pill.lg{ font-size:1.15rem; padding:.5rem 1.25rem; letter-spacing:.14em; }
.so-live{ color:var(--accent); background:rgba(56,225,217,.10); border-color:rgba(56,225,217,.32); }
@keyframes soPulse{ 0%,100%{ box-shadow:0 0 0 0 rgba(56,225,217,.45);} 50%{ box-shadow:0 0 0 6px rgba(56,225,217,0);} }
.so-section{ display:flex; align-items:center; gap:.7rem; margin:.3rem 0 .9rem 0; }
.so-section .idx{ font-family:var(--mono); font-size:.72rem; letter-spacing:.14em; color:var(--accent); opacity:.85; }
.so-section .bar{ width:26px; height:1px; background:linear-gradient(90deg,var(--accent),transparent); }
.so-section .title{ font-family:var(--display); font-size:1.02rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--txt); }
.so-section .sub{ font-size:.76rem; color:var(--txt2); margin-left:auto; letter-spacing:.04em; }
.so-bar-track{ background:rgba(255,255,255,.06); border-radius:999px; height:8px; width:100%; overflow:hidden; margin-top:.35rem; }
.so-bar-fill{ height:8px; border-radius:999px; transition:width .6s cubic-bezier(.22,.61,.36,1); }
[data-testid="stTabs"] [data-baseweb="tab-list"]{ gap:.4rem; border-bottom:1px solid var(--border); }
[data-testid="stTabs"] [data-baseweb="tab"]{ font-family:var(--display); letter-spacing:.04em; color:var(--txt2); }
[data-testid="stTabs"] [aria-selected="true"]{ color:var(--accent) !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{ background:var(--accent) !important; }
[data-testid="stDataFrame"]{ border:1px solid var(--border); border-radius:14px; overflow:hidden; }
hr{ border-color:var(--border); margin:1.1rem 0; }
[data-testid="stSidebar"]{ background:linear-gradient(180deg,#0A0F1B,#070A12); border-right:1px solid var(--border); }
[data-testid="stSidebar"] h3{ letter-spacing:.08em; text-transform:uppercase; }
.stButton>button{ font-family:var(--display); border-radius:11px; font-weight:600; letter-spacing:.04em;
  border:1px solid rgba(56,225,217,.30); background:rgba(56,225,217,.08); color:var(--txt); transition:all .2s ease; }
.stButton>button:hover{ border-color:var(--accent); background:rgba(56,225,217,.16); transform:translateY(-1px); }
</style>
"""


# ---------------------------------------------------------------------------
# Componentes
# ---------------------------------------------------------------------------
def pill(nivel: str, lg: bool = False) -> str:
    return (f'<span class="so-pill {"lg " if lg else ""}" '
            f'style="color:{COR[nivel]};background:{COR[nivel]}1f;'
            f'border-color:{COR[nivel]}55;">{nivel}</span>')


def section(idx: str, title: str, sub: str = "") -> str:
    s = f'<span class="sub">{sub}</span>' if sub else ""
    return (f'<div class="so-section"><span class="idx">{idx}</span>'
            f'<span class="bar"></span><span class="title">{title}</span>{s}</div>')


def fonte_bar(label: str, valor: float, cor: str) -> str:
    v = max(0, min(100, valor))
    return f"""
    <div style="margin:.7rem 0;">
      <div style="display:flex;justify-content:space-between;font-size:.8rem;">
        <span style="color:var(--txt2);letter-spacing:.02em;">{label}</span>
        <span class="so-mono" style="color:var(--txt);font-weight:600;">{valor:.0f}<span style="color:var(--txt2)">/100</span></span>
      </div>
      <div class="so-bar-track"><div class="so-bar-fill" style="width:{v}%;background:linear-gradient(90deg,{cor}aa,{cor});box-shadow:0 0 12px {cor}88;"></div></div>
    </div>"""


def gauge(score: float, cor: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(score, 1),
        number={"font": {"size": 52, "color": cor, "family": "IBM Plex Mono, monospace"},
                "suffix": "<span style='font-size:15px;color:#7E8BA3'> /100</span>"},
        gauge={"axis": {"range": [0, 100], "tickcolor": "#465068",
                        "tickfont": {"color": "#7E8BA3", "size": 10, "family": "IBM Plex Mono"}},
               "bar": {"color": "rgba(234,241,251,0.95)", "thickness": 0.14},
               "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
               "steps": [{"range": [0, 25], "color": "rgba(52,211,153,0.22)"},
                         {"range": [25, 50], "color": "rgba(250,204,21,0.22)"},
                         {"range": [50, 75], "color": "rgba(251,146,60,0.26)"},
                         {"range": [75, 100], "color": "rgba(244,63,94,0.30)"}],
               "threshold": {"line": {"color": cor, "width": 4}, "thickness": 0.82, "value": score}}))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"color": "#EAF1FB"}, height=258, margin=dict(l=26, r=26, t=16, b=6))
    return fig


def mapa_fogo(eventos, area_lat, area_lon, cor) -> go.Figure:
    """Mapa-mundi (Plotly Scattergeo) com queimadas reais + area monitorada."""
    fig = go.Figure()
    if eventos:
        fig.add_trace(go.Scattergeo(
            lon=[e["lon"] for e in eventos], lat=[e["lat"] for e in eventos],
            mode="markers", name="Queimada real (NASA)",
            marker=dict(size=6, color="#FB923C", opacity=0.85, line=dict(width=0)),
            customdata=[[e["lat"], e["lon"], e.get("titulo", "")] for e in eventos],
            text=[e.get("titulo", "") for e in eventos], hoverinfo="text"))
    fig.add_trace(go.Scattergeo(
        lon=[area_lon], lat=[area_lat], mode="markers", name="Area monitorada",
        marker=dict(size=15, color=cor, line=dict(width=2, color="#EAF1FB")),
        customdata=[[area_lat, area_lon, "Area monitorada"]],
        text=["Area monitorada"], hoverinfo="text"))
    fig.update_geos(
        bgcolor="rgba(0,0,0,0)", showland=True, landcolor="#0F1626",
        showocean=True, oceancolor="#0A0E17", showlakes=False,
        showcountries=True, countrycolor="#232C40", coastlinecolor="#232C40",
        showframe=False, projection_type="natural earth")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", height=380, margin=dict(l=0, r=0, t=0, b=0),
        font=dict(color="#EAF1FB"), geo=dict(bgcolor="rgba(0,0,0,0)"),
        legend=dict(orientation="h", y=0, font=dict(color="#7E8BA3", size=10),
                    bgcolor="rgba(0,0,0,0)"))
    return fig


@st.cache_data(ttl=600, show_spinner=False)
def get_fires():
    return fetch_wildfires()


@st.cache_data(ttl=3600, show_spinner=False)
def get_gibs(bbox):
    out = DATA_DIR / "gibs_view.png"
    r = fetch_gibs(out, bbox=bbox)
    return str(out) if r.get("ok") else None


# ---------------------------------------------------------------------------
init_db()
st.markdown(CSS, unsafe_allow_html=True)
eventos, origem_fogo = get_fires()

# ---- Sidebar ----
with st.sidebar:
    st.markdown('<div class="so-kicker">Sentinela // Sistema</div>', unsafe_allow_html=True)
    st.markdown("### Controles da demo")

    st.markdown('<span class="so-kicker">Area monitorada</span>', unsafe_allow_html=True)
    modo_area = st.radio("Area", ["Amazonia Legal (fixa)", "Seguir foco real mais proximo"],
                         label_visibility="collapsed")
    _sel_lat = st.session_state.get("sel_lat")
    if _sel_lat is not None:
        area_lat = _sel_lat
        area_lon = st.session_state["sel_lon"]
        area_label = st.session_state.get("sel_nome", "ponto selecionado")
        st.caption(f"📍 {area_label} (escolhido no mapa)")
        if st.button("↩️ Voltar para area padrao", width="stretch"):
            for k in ("sel_lat", "sel_lon", "sel_nome"):
                st.session_state.pop(k, None)
            st.rerun()
    elif modo_area.startswith("Seguir") and eventos:
        from src.data.nasa import haversine
        nearest = min(eventos, key=lambda e: haversine(AREA_LAT, AREA_LON, e["lat"], e["lon"]))
        area_lat, area_lon, area_label = nearest["lat"], nearest["lon"], nearest["titulo"]
        st.caption(f"📍 {area_label}")
    else:
        area_lat, area_lon, area_label = AREA_LAT, AREA_LON, AREA_NOME

    st.markdown('<span class="so-kicker">01 · Sensores de solo</span>', unsafe_allow_html=True)
    fonte_solo = st.radio("Fonte do solo", ["Real (Open-Meteo)", "Simulado (ESP32)"],
                          label_visibility="collapsed")
    if fonte_solo.startswith("Real"):
        if st.button("📡 Ler solo real (Open-Meteo)", width="stretch"):
            from src.data.open_meteo import ler_solo
            leituras, og = ler_solo(area_lat, area_lon, serie=True)
            for r in leituras:
                sim.insert_sensor_reading(r)
            st.toast(f"{len(leituras)} leituras reais de solo [{og}].")
    else:
        cenario = st.selectbox("Cenario", ["aleatorio", "normal", "critico"],
                               label_visibility="collapsed")
        n_leituras = st.slider("Leituras a gerar", 1, 30, 8)
        if st.button("📡 Gerar leituras simuladas", width="stretch"):
            for _ in range(n_leituras):
                sim.insert_sensor_reading(sim.gerar_leitura(cenario))
            st.toast(f"{n_leituras} leituras simuladas ({cenario}).")

    st.markdown('<span class="so-kicker">02 · Imagem orbital</span>', unsafe_allow_html=True)
    st.caption("Classifique na aba *Satelite*.")

    st.markdown('<span class="so-kicker">03 · Fusao</span>', unsafe_allow_html=True)
    enviar_nuvem = st.checkbox("Enviar alerta a nuvem (AWS)", value=False)
    if st.button("🔀 Rodar fusao e registrar alerta", width="stretch"):
        st.session_state["alerta"] = pipeline.executar(persistir=True, nuvem=enviar_nuvem,
                                                        lat=area_lat, lon=area_lon)
        st.toast("Fusao executada e alerta registrado.")

    st.divider()
    ok_modelo = MODEL_PATH.exists()
    st.caption(f"Modelo CNN: {'🟢 carregado' if ok_modelo else '🔴 treine: python -m src.ml.train'}")
    st.caption(f"🔥 Queimadas NASA: {len(eventos)} ativas [{origem_fogo}]")

# ---- Estado atual ----
sensor = latest_sensor()
deteccao = latest_detection()
fogo = fire_score(area_lat, area_lon, eventos)
alerta = st.session_state.get("alerta") or pipeline.fundir(sensor, deteccao, fogo)
nivel = alerta.get("nivel", "BAIXO")
cor = COR[nivel]

# ---- Top bar ----
top_l, top_r = st.columns([3, 1.4])
with top_l:
    st.markdown('<div class="so-brand"><span class="dot"></span>SENTINELA ORBITAL</div>'
                '<div class="so-sub">Risco de fogo e desmatamento por fusao de satelite '
                '(Sentinel-2 + NASA) e sensores de solo</div>', unsafe_allow_html=True)
with top_r:
    st.markdown(f'<div style="text-align:right;margin-top:.35rem;">'
                f'<span class="so-pill so-live">AO VIVO</span><br>'
                f'<span class="so-sub so-mono">{datetime.now():%d/%m/%Y · %H:%M:%S}</span></div>',
                unsafe_allow_html=True)
st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

# ---- HERO ----
hero_l, hero_r = st.columns([1.25, 1])
with hero_l:
    with st.container(border=True):
        st.markdown(section("01", "Risco da area", "fusao de 3 fontes"), unsafe_allow_html=True)
        st.plotly_chart(gauge(alerta.get("risco_total", 0), cor), width="stretch",
                        config={"displayModeBar": False})
with hero_r:
    with st.container(border=True):
        st.markdown(section("02", "Status operacional"), unsafe_allow_html=True)
        st.markdown(pill(nivel, lg=True), unsafe_allow_html=True)
        st.markdown(f"<div style='margin:.8rem 0 .2rem 0;font-size:1.0rem;color:var(--txt);"
                    f"line-height:1.4;'>{MENSAGEM[nivel]}</div>", unsafe_allow_html=True)
        st.markdown('<div class="so-kicker" style="margin-top:.7rem;">Como chegamos a esse risco</div>',
                    unsafe_allow_html=True)
        st.markdown(fonte_bar("Solo (sensor ESP32)", alerta.get("risco_sensor", 0), "#38E1D9"),
                    unsafe_allow_html=True)
        st.markdown(fonte_bar("Desmatamento (CNN/Sentinel-2)", alerta.get("risco_imagem", 0), "#A78BFA"),
                    unsafe_allow_html=True)
        st.markdown(fonte_bar("Fogo real (NASA EONET)", alerta.get("risco_fogo", 0), "#FB923C"),
                    unsafe_allow_html=True)
        with st.expander("Detalhes tecnicos da fusao"):
            st.code(alerta.get("mensagem", ""), language="text")

st.divider()

# ---- EVIDENCIAS ----
st.markdown(section("03", "Evidencias", "o que sustenta o status"), unsafe_allow_html=True)
tab_sat, tab_real, tab_sensor = st.tabs(
    ["🛰️  Classificacao (CNN)", "🌎  Satelite real (NASA)", "🌡️  Sensores de solo"])

with tab_sat:
    if not ok_modelo:
        st.info("Modelo nao treinado. Rode `python -m src.ml.train` e recarregue.")
    else:
        c_img, c_res = st.columns([1, 1.1])
        with c_img:
            origem = st.radio("Origem da imagem", ["Gerar amostra sintetica", "Upload"], horizontal=True)
            img_path = None
            if origem == "Upload":
                up = st.file_uploader("Recorte de imagem orbital (PNG/JPG)", type=["png", "jpg", "jpeg"])
                if up:
                    img_path = ROOT / "data" / "upload_tmp.png"
                    img_path.write_bytes(up.read())
            else:
                classe = st.selectbox("Classe (amostra real EuroSAT)",
                                      ["floresta", "desmatamento", "agua"])
                if st.button("Sortear imagem real e classificar"):
                    import random
                    import shutil
                    reais = list((DATASET_REAL_DIR / classe).glob("*.jpg"))
                    img_path = ROOT / "data" / "amostra_tmp.png"
                    if reais:
                        shutil.copy(random.choice(reais), img_path)
                    else:
                        from src.ml.dataset import make_image
                        make_image(classe).save(img_path)
            if img_path and Path(img_path).exists():
                st.session_state["img_path"] = str(img_path)
            ip = st.session_state.get("img_path")
            if ip and Path(ip).exists():
                st.image(ip, caption="Imagem analisada", width=210)
        with c_res:
            ip = st.session_state.get("img_path")
            if ip and Path(ip).exists():
                from src.ml.predict import predict_image
                r = predict_image(ip)
                insert_detection(r)
                st.metric("Classe detectada", CLASSE_LABEL.get(r["classe"], r["classe"]),
                          f"{r['confianca']*100:.1f}% de confianca")
                probs = pd.DataFrame({"classe": [CLASSE_LABEL.get(c, c) for c in r["probabilidades"]],
                                      "probabilidade": list(r["probabilidades"].values())}).set_index("classe")
                st.bar_chart(probs, color="#38E1D9", height=220)
            else:
                st.caption("Gere ou envie uma imagem para ver a classificacao.")

with tab_real:
    st.caption(f"Imagem MODIS true-color (NASA GIBS) de: **{area_label}** "
               f"({area_lat:.2f}, {area_lon:.2f}). Clique num ponto no mapa (secao 04) "
               f"para mudar o local de TODO o monitoramento (solo + fogo + imagem).")
    cg1, cg2 = st.columns([1, 1])
    with cg1:
        bbox = (area_lon - 2, area_lat - 2, area_lon + 2, area_lat + 2)
        if st.button("🔄 Baixar imagem de satelite atual"):
            get_gibs.clear()
        path_gibs = get_gibs(bbox)
        if path_gibs and Path(path_gibs).exists():
            st.image(path_gibs, caption=f"NASA GIBS · {area_lat:.1f}, {area_lon:.1f}", width=320)
        else:
            st.info("Imagem indisponivel (sem internet). Tente novamente.")
    with cg2:
        st.metric("Foco real mais proximo", f"{fogo['nearest_km']} km" if fogo['nearest_km'] is not None else "-")
        st.caption(f"🔥 {fogo.get('nearest') or '-'}")
        st.metric("Focos no raio monitorado", f"{fogo['dentro']}")
        st.metric("Queimadas ativas (global)", f"{fogo['total']}")

with tab_sensor:
    st.caption(f"Solo monitorado em: **{area_label}** ({area_lat:.2f}, {area_lon:.2f}). "
               f"Apos mudar o local, clique 'Ler solo real' na barra lateral.")
    if not sensor:
        st.info("Sem leituras. Use **01 · Sensores de solo** na barra lateral.")
    else:
        cs1, cs2, cs3 = st.columns([1, 1, 1.4])
        cs1.metric("Risco do solo", f"{sensor['risco_sensor']:.0f}", "indice 0-100")
        cs2.markdown("<div class='so-kicker' style='margin-bottom:.4rem'>Nivel do sensor</div>", unsafe_allow_html=True)
        cs2.markdown(pill(sensor["nivel"]), unsafe_allow_html=True)
        cs3.metric("Fumaca detectada", f"{sensor['fumaca_ppm']:.0f} ppm")
        hist = fetch_recent("sensor_readings", 50)
        if len(hist) > 1:
            df = pd.DataFrame(hist)[::-1]
            st.markdown("<div class='so-kicker' style='margin-top:.5rem'>Tendencia do risco do solo</div>", unsafe_allow_html=True)
            st.line_chart(df.set_index("ts")[["risco_sensor"]], color="#FB923C", height=200)
        with st.expander("Telemetria detalhada (todos os sensores)"):
            d1, d2, d3 = st.columns(3)
            d1.metric("Temp. ar", f"{sensor['temp_ar']} C")
            d2.metric("Umid. ar", f"{sensor['umid_ar']} %")
            d3.metric("Temp. solo", f"{sensor['temp_solo']} C")
            d1.metric("Umid. solo", f"{sensor['umid_solo']} %")
            d2.metric("Fumaca", f"{sensor['fumaca_ppm']} ppm")
            d3.metric("Risco", f"{sensor['risco_sensor']}")

st.divider()

# ---- MAPA (focos reais) + HISTORICO ----
st.markdown(section("04", "Mapa de queimadas reais (NASA)", f"{len(eventos)} focos ativos"),
            unsafe_allow_html=True)
m_col, h_col = st.columns([1.5, 1])
with m_col:
    ev = st.plotly_chart(mapa_fogo(eventos, area_lat, area_lon, cor),
                         width="stretch", config={"displayModeBar": False},
                         on_select="rerun", selection_mode="points", key="mapafogo")
    sel = []
    try:
        sel = ev["selection"]["points"]
    except Exception:
        sel = getattr(getattr(ev, "selection", None), "points", []) or []
    if sel:
        cd = sel[0].get("customdata")
        if cd and (st.session_state.get("sel_lat") != float(cd[0])
                   or st.session_state.get("sel_lon") != float(cd[1])):
            st.session_state["sel_lat"] = float(cd[0])
            st.session_state["sel_lon"] = float(cd[1])
            st.session_state["sel_nome"] = cd[2]
            st.rerun()
    st.caption("Laranja = foco real (NASA EONET) · circulo = area monitorada. "
               "Clique num ponto para monitorar esse local (solo + fogo + imagem); "
               "depois use 'Ler solo real' na barra lateral.")
with h_col:
    alertas = fetch_recent("alerts", 12)
    if alertas:
        df = pd.DataFrame(alertas)[["ts", "nivel", "risco_total"]]
        df.columns = ["Horario", "Nivel", "Risco"]
        st.dataframe(df, width="stretch", height=260, hide_index=True)
    else:
        st.caption("Nenhum alerta registrado. Rode a fusao na barra lateral.")

# ---- Rodape ----
st.divider()
with st.expander("Sobre o projeto"):
    st.markdown(
        "**SENTINELA ORBITAL** — POC da FIAP Sub Global Solution 2026.1. Funde 3 fontes: "
        "**CNN MobileNetV2** treinada em **EuroSAT (Sentinel-2 real)** para desmatamento, "
        "**NASA EONET/GIBS** (queimadas e imagens de satelite REAIS) e **IoT/ESP32** "
        "(sensores de solo). Persistencia em SQLite e nuvem AWS (S3/DynamoDB/Lambda).")
st.caption(f"Atualizado em {datetime.now():%d/%m/%Y %H:%M:%S}")

"""
Gera o PDF unico de entrega (FIAP Sub GS 2026.1) a partir do relatorio.

Estrutura conforme exigido pela atividade:
  - Capa com NOME COMPLETO e RM;
  - Introducao, Desenvolvimento, Resultados Esperados, Conclusoes;
  - Codigos principais EM TEXTO (nao screenshot);
  - Imagens/diagramas (arquitetura, treino, matriz de confusao);
  - Links do repositorio e do video ao final.

>>> ANTES DE GERAR, EDITE as constantes NOME, RM, VIDEO_URL e REPO_URL abaixo.

Uso:
    pip install fpdf2
    python scripts/gerar_pdf.py
"""
import sys
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from config.config import ASSETS_DIR

# ==== EDITE AQUI ============================================================
NOME = "Bruno de Souza Leite"
RM = "RM567213"
VIDEO_URL = "https://youtu.be/e5dnb7D5-fM"
REPO_URL = "https://github.com/souzaleite-dev/subgs"
# ===========================================================================

PROJETO = "SENTINELA ORBITAL"
SUBTITULO = ("Monitoramento de desmatamento e queimadas com dados REAIS de "
             "satelite (Sentinel-2 / NASA), Visao Computacional, IoT (ESP32) "
             "e Computacao em Nuvem (AWS)")

OUT_PDF = ROOT / "docs" / "Sentinela_Orbital_Entrega.pdf"


def s(txt: str) -> str:
    """Sanitiza para latin-1 (fontes core do fpdf)."""
    repl = {"—": "-", "–": "-", "→": "->", "•": "-",
            "“": '"', "”": '"', "‘": "'", "’": "'",
            "º": "o", "ª": "a", "﻿": ""}
    for k, v in repl.items():
        txt = txt.replace(k, v)
    return txt.encode("latin-1", "replace").decode("latin-1")


class PDF(FPDF):
    def multi_cell(self, w=0, h=5, text="", **kw):
        # Garante que cada bloco comece na margem esquerda e use a largura util,
        # evitando o erro "Not enough horizontal space" apos textos centralizados.
        kw.setdefault("new_x", XPos.LMARGIN)
        kw.setdefault("new_y", YPos.NEXT)
        self.set_x(self.l_margin)
        if w == 0:
            w = self.epw
        return super().multi_cell(w, h, text, **kw)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120)
        self.cell(0, 8, s(f"{PROJETO} - FIAP Sub GS 2026.1"), align="R")
        self.ln(10)
        self.set_text_color(0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120)
        self.cell(0, 8, f"Pagina {self.page_no()}", align="C")
        self.set_text_color(0)

    def titulo(self, txt):
        self.ln(2)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 60, 110)
        self.multi_cell(0, 8, s(txt))
        self.set_text_color(0)
        self.ln(1)

    def subtitulo(self, txt):
        self.set_font("Helvetica", "B", 11)
        self.multi_cell(0, 6, s(txt))
        self.ln(0.5)

    def paragrafo(self, txt):
        self.set_font("Helvetica", "", 10.5)
        self.multi_cell(0, 5.4, s(txt))
        self.ln(1.5)

    def lista(self, itens):
        self.set_font("Helvetica", "", 10.5)
        for it in itens:
            self.multi_cell(0, 5.4, s("  - " + it))
        self.ln(1.5)

    def codigo(self, caminho, max_linhas=46, titulo=None):
        p = ROOT / caminho
        if not p.exists():
            return
        if titulo:
            self.set_font("Helvetica", "B", 9.5)
            self.multi_cell(0, 5, s(titulo))
        linhas = p.read_text(encoding="utf-8").splitlines()[:max_linhas]
        self.set_font("Courier", "", 7.2)
        self.set_fill_color(244, 244, 244)
        for ln in linhas:
            self.multi_cell(0, 3.5, s(ln if ln else " "), fill=True)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(120)
        self.multi_cell(0, 4, s(f"(trecho de {caminho})"))
        self.set_text_color(0)
        self.ln(2)

    def imagem(self, nome, legenda, w=160):
        p = ASSETS_DIR / nome
        if not p.exists():
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(150)
            self.multi_cell(0, 5, s(f"[imagem '{nome}' sera gerada ao rodar o projeto]"))
            self.set_text_color(0)
            self.ln(2)
            return
        x = (self.w - w) / 2
        self.image(str(p), x=x, w=w)
        self.set_font("Helvetica", "I", 8.5)
        self.set_text_color(110)
        self.multi_cell(0, 4.5, s(legenda), align="C")
        self.set_text_color(0)
        self.ln(3)


def build():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ---------------- CAPA ----------------
    pdf.add_page()
    logo = ASSETS_DIR / "logo-fiap.png"
    if logo.exists():
        pdf.image(str(logo), x=(pdf.w - 40) / 2, y=20, w=40)
        pdf.ln(40)
    else:
        pdf.ln(30)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 60, 110)
    pdf.multi_cell(0, 11, s(PROJETO), align="C")
    pdf.set_text_color(0)
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 6.5, s(SUBTITULO), align="C")
    pdf.ln(14)
    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(0, 8, s(f"Nome: {NOME}"), align="C")
    pdf.multi_cell(0, 8, s(f"RM: {RM}"), align="C")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, s("FIAP - Graduacao em Inteligencia Artificial"), align="C")
    pdf.multi_cell(0, 6, s("Sub Global Solution 2026.1 - Nova Economia Espacial"), align="C")
    pdf.multi_cell(0, 6, s(f"Data: {datetime.now():%d/%m/%Y}"), align="C")

    # ---------------- INTRODUCAO ----------------
    pdf.add_page()
    pdf.titulo("1. Introducao")
    pdf.paragrafo(
        "A economia espacial deixou de ser apenas cientifica e tornou-se uma das "
        "maiores oportunidades tecnologicas e estrategicas da atualidade. Satelites "
        "de observacao da Terra (como a constelacao Sentinel, do programa Copernicus) "
        "produzem diariamente um volume imenso de imagens que podem ser usadas para "
        "monitorar o clima, a agricultura e, em especial, a integridade das florestas.")
    pdf.paragrafo(
        "O desmatamento e as queimadas estao entre os problemas ambientais mais "
        "criticos do Brasil e do mundo. Detecta-los cedo - combinando o que os "
        "satelites veem do espaco com o que sensores medem no solo - permite respostas "
        "rapidas que reduzem perdas ambientais e economicas.")
    pdf.paragrafo(
        "Este projeto, batizado de SENTINELA ORBITAL, e uma Prova de Conceito (POC) "
        "que responde a pergunta da Sub GS 2026.1: como a Inteligencia Artificial e as "
        "tecnologias digitais podem transformar a nova economia espacial e gerar "
        "impacto positivo na Terra? A resposta proposta integra Visao Computacional "
        "sobre imagens orbitais, Internet das Coisas (ESP32) e Computacao em Nuvem (AWS) "
        "em um unico painel de decisao.")
    pdf.subtitulo("Objetivo")
    pdf.paragrafo(
        "Construir um sistema que classifica automaticamente a cobertura do solo a "
        "partir de imagens orbitais (floresta saudavel, desmatamento ou queimada), "
        "combine esse resultado com a telemetria de sensores de solo e gere alertas "
        "de risco de incendio/desmatamento em tempo real.")

    # ---------------- DESENVOLVIMENTO ----------------
    pdf.add_page()
    pdf.titulo("2. Desenvolvimento")
    pdf.subtitulo("2.1 Arquitetura da solucao")
    pdf.paragrafo(
        "A solucao combina TRES fontes de dados independentes em um pipeline de fusao. "
        "(1) Imagem orbital: uma CNN (MobileNetV2, transfer learning) treinada com o "
        "dataset EuroSAT de recortes reais do satelite Sentinel-2 classifica a cobertura "
        "do solo (floresta, desmatamento, agua). (2) Fogo real: a API publica da NASA "
        "EONET fornece queimadas ativas reais, e o GIBS fornece imagens de satelite "
        "reais (MODIS true-color) da area. (3) Sensores de solo (ESP32): temperatura, "
        "umidade do ar/solo e fumaca, derivando um indice de risco. O pipeline funde os "
        "tres riscos com pesos, classifica o nivel de alerta e persiste o resultado no "
        "banco e na nuvem. Tudo e visualizado em um dashboard. As tres fontes usam DADOS "
        "REAIS: imagens Sentinel-2 (treino), NASA (fogo/imagem) e Open-Meteo (solo).")
    pdf.imagem("arquitetura.png", "Figura 1 - Arquitetura geral do SENTINELA ORBITAL.")

    pdf.subtitulo("2.2 Tecnologias utilizadas")
    pdf.lista([
        "Python 3.12 como linguagem principal.",
        "TensorFlow/Keras + MobileNetV2 (transfer learning, ImageNet) - CNN de visao computacional.",
        "EuroSAT (recortes reais do satelite Sentinel-2) - dataset de treino real.",
        "NASA EONET (queimadas reais) e NASA GIBS (imagens de satelite reais) - dados abertos, sem chave.",
        "Open-Meteo (temperatura/umidade do SOLO e qualidade do ar REAIS) - sensor de solo sem chave.",
        "ESP32 (firmware C/Arduino) para hardware fisico de sensores; simulador como fallback.",
        "AWS S3, DynamoDB e Lambda (boto3) - computacao em nuvem serverless.",
        "SQLite - persistencia das leituras, deteccoes e alertas.",
        "Streamlit + Plotly - dashboard interativo de monitoramento.",
        "Matplotlib e scikit-learn - graficos e matriz de confusao.",
    ])

    pdf.subtitulo("2.3 Visao Computacional (CNN com dados reais)")
    pdf.paragrafo(
        "A classificacao usa TRANSFER LEARNING: a MobileNetV2 pre-treinada na ImageNet "
        "tem sua base congelada e ganha uma cabeca densa para 3 classes (floresta, "
        "desmatamento, agua). O treino usa o EuroSAT - recortes RGB reais do satelite "
        "Sentinel-2 (programa Copernicus) - mapeados para o contexto do projeto: "
        "desmatamento equivale a uso antropico/agropecuaria (AnnualCrop, Pasture, "
        "PermanentCrop), o principal vetor de desmatamento. A acuracia de validacao "
        "obtida foi de ~96,7%. Caso nao haja internet, um gerador sintetico mantem a "
        "POC funcional offline.")
    pdf.codigo("src/ml/train.py", max_linhas=58,
               titulo="Codigo 1 - Modelo MobileNetV2 (transfer learning) em src/ml/train.py")

    pdf.subtitulo("2.4 Camada IoT - sensores de solo (dados reais)")
    pdf.paragrafo(
        "As leituras de solo sao REAIS: o modulo src/data/open_meteo.py consome o "
        "Open-Meteo (aberto, sem chave) e obtem temperatura/umidade do solo, "
        "temperatura/umidade do ar e qualidade do ar (CO) para as coordenadas da area. "
        "O mesmo indice de risco de fogo (0 a 100), inspirado no Fire Weather Index, e "
        "calculado sobre esses dados reais e tambem no firmware ESP32 (esp32_firmware.ino) "
        "para hardware fisico; ha simulador como fallback offline.")
    pdf.codigo("src/iot/sensor_simulator.py", max_linhas=30,
               titulo="Codigo 2 - Calculo do indice de risco (src/iot/sensor_simulator.py)")

    pdf.subtitulo("2.5 Pipeline de fusao (3 fontes)")
    pdf.paragrafo(
        "O pipeline combina tres riscos 0-100: solo (sensor), desmatamento (probabilidade "
        "da CNN) e fogo real (proximidade/densidade das queimadas reais da NASA). Aplica "
        "uma media ponderada (pesos 0,30 / 0,30 / 0,40, renormalizados quando uma fonte "
        "falta), classifica em BAIXO/MODERADO/ALTO/CRITICO e gera o alerta.")
    pdf.codigo("src/pipeline/pipeline.py", max_linhas=34,
               titulo="Codigo 3 - Fusao de risco de 3 fontes (src/pipeline/pipeline.py)")

    pdf.subtitulo("2.6 Computacao em nuvem (AWS)")
    pdf.paragrafo(
        "A integracao com a AWS envia a imagem analisada para o S3 e grava o alerta no "
        "DynamoDB; uma funcao Lambda (acionada por API Gateway) processa as leituras "
        "enviadas pelo ESP32. Para permitir a demonstracao sem custo, ha um fallback "
        "local automatico que simula esses servicos quando nao ha credenciais AWS.")
    pdf.codigo("src/cloud/lambda_function.py", max_linhas=34,
               titulo="Codigo 4 - Handler AWS Lambda (src/cloud/lambda_function.py)")

    pdf.subtitulo("2.7 Dados REAIS da NASA (sem chave de API)")
    pdf.paragrafo(
        "O modulo src/data/nasa.py consome dois servicos abertos da NASA, sem "
        "autenticacao: a EONET (Earth Observatory Natural Event Tracker), que lista "
        "queimadas/incendios ativos REAIS com coordenadas, e o GIBS, que entrega imagens "
        "de satelite REAIS (MODIS true-color) via WMS. A partir das queimadas reais e da "
        "distancia ate a area, calcula-se um risco de fogo 0-100. Ha cache e amostra de "
        "fallback para garantir funcionamento mesmo sem internet.")
    pdf.codigo("src/data/nasa.py", max_linhas=48,
               titulo="Codigo 5 - Integracao com dados reais da NASA (src/data/nasa.py)")

    # ---------------- RESULTADOS ----------------
    pdf.add_page()
    pdf.titulo("3. Resultados Esperados")
    pdf.paragrafo(
        "Treinada por transfer learning (MobileNetV2) sobre o EuroSAT (3.600 recortes "
        "reais do Sentinel-2, 1.200 por classe), a CNN atingiu ~96,7% de acuracia de "
        "validacao - resultado realista para imagens de satelite reais. As figuras "
        "abaixo, geradas automaticamente pelo treino, documentam o desempenho.")
    pdf.imagem("treino_historico.png", "Figura 2 - Curvas de acuracia e perda (treino x validacao).")
    pdf.imagem("matriz_confusao.png", "Figura 3 - Matriz de confusao no conjunto de validacao.", w=110)
    pdf.imagem("amostras_predicao.png", "Figura 4 - Exemplos de classificacao da CNN.", w=120)
    pdf.paragrafo(
        "No dashboard, o operador acompanha em tempo real: a classificacao da imagem "
        "orbital, a telemetria dos sensores, o risco total da fusao, o nivel de alerta "
        "(com codigo de cores), o historico de alertas e o mapa da area monitorada. "
        "Quando o risco do solo (seca + fumaca) coincide com a deteccao visual de "
        "queimada/desmatamento, o sistema eleva o alerta para CRITICO.")
    pdf.imagem("dashboard.png", "Figura 5 - Dashboard de monitoramento (Streamlit) com dados reais.")
    pdf.paragrafo(
        "O mapa do dashboard plota as queimadas reais ativas da NASA (EONET) e a area "
        "monitorada; o painel 'Satelite real' exibe a imagem MODIS (NASA GIBS) da regiao. "
        "No modo 'seguir foco real mais proximo', o risco de fogo sobe com base em uma "
        "queimada real, elevando o alerta para CRITICO.")
    pdf.imagem("satelite_real.png",
               "Figura 6 - Imagem de satelite REAL (NASA GIBS / MODIS true-color) da area.",
               w=90)

    # ---------------- CONCLUSOES ----------------
    pdf.add_page()
    pdf.titulo("4. Conclusoes")
    pdf.paragrafo(
        "O SENTINELA ORBITAL demonstra, de ponta a ponta, como tecnologias derivadas e "
        "conectadas a economia espacial podem gerar impacto positivo direto na Terra. "
        "Ao unir o olhar do satelite (visao computacional) com a percepcao do solo "
        "(IoT) e o poder de escala da nuvem, a POC entrega uma ferramenta de apoio a "
        "decisao para prevencao de incendios e combate ao desmatamento.")
    pdf.paragrafo(
        "A arquitetura e modular: o dataset sintetico pode ser trocado por imagens "
        "Sentinel-2 reais, o simulador pode ser substituido pelo ESP32 fisico e o "
        "fallback local pode ser promovido a infraestrutura AWS real, tudo sem reescrever "
        "o nucleo do sistema. Isso evidencia a aplicabilidade pratica e a escalabilidade "
        "da solucao.")
    pdf.subtitulo("Evolucoes futuras")
    pdf.lista([
        "Fine-tuning da CNN e datasets adicionais (FLAME, INPE/PRODES) alem do EuroSAT.",
        "Segmentacao (U-Net) para delimitar a area exata do desmatamento/queimada.",
        "Ingestao de focos reais da NASA FIRMS (VIIRS) e alertas via AWS SNS.",
        "Telemetria via MQTT real e ingestao com AWS IoT Core.",
    ])

    # ---------------- LINKS ----------------
    pdf.add_page()
    pdf.titulo("5. Links da entrega")
    pdf.subtitulo("Repositorio do projeto (GitHub)")
    pdf.paragrafo(REPO_URL)
    pdf.subtitulo("Video demonstrativo (YouTube - Nao Listado)")
    pdf.paragrafo(VIDEO_URL)
    pdf.subtitulo("Como executar (resumo)")
    pdf.lista([
        "pip install -r requirements.txt",
        "python -m src.ml.dataset_real      (baixa EuroSAT / Sentinel-2 real)",
        "python -m src.ml.train             (treina a CNN - transfer learning)",
        "python scripts/gerar_dados_demo.py (popula o banco + fogo real NASA)",
        "streamlit run src/dashboard/app.py (abre o dashboard)",
    ])

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PDF))
    print(f"PDF gerado em: {OUT_PDF}")
    if NOME.startswith("<<") or VIDEO_URL.startswith("<<"):
        print("\n>>> ATENCAO: edite NOME, RM, VIDEO_URL e REPO_URL no topo deste "
              "script e gere novamente o PDF.")


if __name__ == "__main__":
    build()

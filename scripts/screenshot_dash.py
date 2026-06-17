"""
Captura um screenshot do dashboard em execucao e salva em assets/dashboard.png
(para incluir no PDF de entrega).

Pre-requisitos:
    pip install playwright
    python -m playwright install chromium
    streamlit run src/dashboard/app.py   (deve estar rodando em :8501)

Uso:
    python scripts/screenshot_dash.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from config.config import ASSETS_DIR, ensure_dirs

URL = "http://localhost:8501"


def main():
    from playwright.sync_api import sync_playwright

    ensure_dirs()
    out = ASSETS_DIR / "dashboard.png"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1100},
                                device_scale_factor=2)
        # networkidle nao serve: o websocket do Streamlit fica sempre aberto.
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_selector("text=SENTINELA ORBITAL", timeout=40000)
        except Exception:
            pass
        page.wait_for_timeout(4000)
        # Seleciona "seguir foco real mais proximo" para demonstrar risco com dado real
        try:
            page.get_by_text("Seguir foco real mais proximo").click()
            page.wait_for_timeout(4000)
        except Exception as e:
            print("aviso: nao selecionou foco real:", e)
        page.wait_for_timeout(4000)  # fontes + animacao + render do plotly
        page.screenshot(path=str(out), full_page=True)
        browser.close()
    print(f"Screenshot salvo em: {out}")


if __name__ == "__main__":
    main()

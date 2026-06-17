# scripts/

Utilitários de apoio (não fazem parte do núcleo, mas geram artefatos do projeto).

| Script | O que faz |
|--------|-----------|
| `gerar_diagramas.py` | Gera `assets/arquitetura.png` (diagrama da arquitetura) |
| `gerar_dados_demo.py` | Popula o banco com leituras, detecções e alertas para a demo |
| `gerar_pdf.py` | Gera o PDF único de entrega em `docs/` (edite NOME/RM/links antes) |
| `gerar_capa.py` | Gera a capa do projeto em `assets/capa_sentinela_orbital.png` |
| `screenshot_dash.py` | Captura screenshot do dashboard (requer playwright) |

Execute a partir da raiz do projeto, por exemplo:

```bash
python scripts/gerar_dados_demo.py
```

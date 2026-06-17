# scripts/

Utilitários de apoio (não fazem parte do núcleo, mas geram artefatos do projeto).

| Script | O que faz |
|--------|-----------|
| `gerar_diagramas.py` | Gera `assets/arquitetura.png` (diagrama da arquitetura) |
| `gerar_dados_demo.py` | Popula o banco com leituras, detecções e alertas para a demo |
| `gerar_pdf.py` | Gera o PDF único de entrega em `document/` (edite NOME/RM/links antes) |

Execute a partir da raiz do projeto, por exemplo:

```bash
python scripts/gerar_dados_demo.py
```

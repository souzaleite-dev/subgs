# docs/

Documentação textual e entrega final.

| Arquivo | Descrição |
|---------|-----------|
| `RELATORIO.md` | Relatório completo em Markdown (versão legível para leitura/edição) |
| `Sentinela_Orbital_Entrega.pdf` | **PDF único de entrega** (gerado por `python scripts/gerar_pdf.py`) |

## Como gerar o PDF de entrega

1. Edite as constantes no topo de `scripts/gerar_pdf.py`:
   - `NOME`, `RM`, `VIDEO_URL`, `REPO_URL`.
2. (Opcional) Coloque um print do dashboard em `assets/dashboard.png` e a `assets/logo-fiap.png`.
3. Rode:
   ```bash
   python scripts/gerar_pdf.py
   ```

O PDF segue a estrutura exigida pela atividade: **capa com nome + RM**, **Introdução**, **Desenvolvimento**, **Resultados Esperados**, **Conclusões**, **códigos em texto** (não screenshots), **imagens/diagramas** e **links do repositório e do vídeo**.

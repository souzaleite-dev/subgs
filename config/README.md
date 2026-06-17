# config/

Configuração central do projeto.

- **`config.py`** — ponto único de verdade para:
  - caminhos (banco SQLite, modelo, dataset, assets);
  - parâmetros de visão computacional (`IMG_SIZE`, `CLASSES`, tamanho do dataset);
  - coordenadas da área monitorada e limiares do índice de risco;
  - pesos da fusão (`PESO_SENSOR`, `PESO_IMAGEM`);
  - configurações da AWS (região, bucket S3, tabela DynamoDB).

Todos os módulos importam daqui via `from config.config import ...`, garantindo que os caminhos funcionem independentemente do diretório de execução.

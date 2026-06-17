"""
Integracao com a AWS (computacao em nuvem).

Funcoes:
  - upload_imagem_s3  : envia a imagem orbital analisada para o S3
  - salvar_alerta_dynamo : grava o alerta no DynamoDB
  - enviar_para_nuvem : orquestra o envio (imagem + alerta)

IMPORTANTE: a POC roda 100% offline. Se nao houver credenciais AWS ou a
biblioteca boto3 falhar, tudo cai em um FALLBACK LOCAL que escreve em
data/cloud_local/ (simulando os servicos S3/DynamoDB). Assim a solucao e
demonstravel sem custo, mas o codigo de producao ja esta pronto para a AWS.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import (
    AWS_REGION, DYNAMO_TABLE, LOCAL_CLOUD_DIR, S3_BUCKET, ensure_dirs,
)


def _boto3():
    try:
        import boto3
        return boto3
    except Exception:
        return None


def _credenciais_ok(boto3) -> bool:
    try:
        sts = boto3.client("sts", region_name=AWS_REGION)
        sts.get_caller_identity()
        return True
    except Exception:
        return False


def upload_imagem_s3(caminho_imagem: str | Path) -> dict:
    """Envia imagem ao S3 (ou ao fallback local)."""
    ensure_dirs()
    caminho_imagem = Path(caminho_imagem)
    key = f"imagens/{datetime.now():%Y%m%d_%H%M%S}_{caminho_imagem.name}"
    boto3 = _boto3()

    if boto3 and _credenciais_ok(boto3):
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.upload_file(str(caminho_imagem), S3_BUCKET, key)
        return {"destino": "s3", "uri": f"s3://{S3_BUCKET}/{key}"}

    # fallback local
    dest = LOCAL_CLOUD_DIR / "s3" / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    if caminho_imagem.exists():
        shutil.copy(caminho_imagem, dest)
    return {"destino": "local", "uri": str(dest)}


def salvar_alerta_dynamo(alerta: dict) -> dict:
    """Grava o alerta no DynamoDB (ou no fallback local)."""
    ensure_dirs()
    item = {**alerta, "id": f"{datetime.now():%Y%m%d%H%M%S%f}"}
    boto3 = _boto3()

    if boto3 and _credenciais_ok(boto3):
        ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
        ddb.Table(DYNAMO_TABLE).put_item(Item=item)
        return {"destino": "dynamodb", "id": item["id"]}

    # fallback local (append em JSON Lines)
    arq = LOCAL_CLOUD_DIR / "dynamodb_alertas.jsonl"
    with arq.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return {"destino": "local", "id": item["id"], "arquivo": str(arq)}


def enviar_para_nuvem(alerta: dict, caminho_imagem: str | Path | None = None) -> dict:
    """Orquestra upload da imagem + gravacao do alerta."""
    resultado = {"alerta": salvar_alerta_dynamo(alerta)}
    if caminho_imagem:
        resultado["imagem"] = upload_imagem_s3(caminho_imagem)
    return resultado


if __name__ == "__main__":
    demo = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "estacao": "Estacao Floresta-01",
        "risco_total": 82.5,
        "nivel": "CRITICO",
        "origem": "fusao_sensor_imagem",
        "mensagem": "Alerta de teste de integracao com a nuvem.",
    }
    print(json.dumps(enviar_para_nuvem(demo), ensure_ascii=False, indent=2))

"""
AWS Lambda (computacao serverless) - SENTINELA ORBITAL.

Recebe um evento (leitura de sensor enviada pelo ESP32 via API Gateway,
ou resultado de classificacao da imagem) e:
  1. calcula/normaliza o risco;
  2. decide o nivel de alerta;
  3. persiste o alerta no DynamoDB;
  4. retorna a resposta HTTP.

Deploy resumido:
  - Runtime: Python 3.12
  - Handler: lambda_function.lambda_handler
  - Trigger: API Gateway (POST /sensor)
  - Permissao: dynamodb:PutItem na tabela 'sentinela_alertas'

Este arquivo e autossuficiente (nao importa o resto do projeto), como
exigido por um pacote de deploy Lambda.
"""
import json
import os
from datetime import datetime, timezone

DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE", "sentinela_alertas")


def classificar_nivel(risco: float) -> str:
    if risco < 25:
        return "BAIXO"
    if risco < 50:
        return "MODERADO"
    if risco < 75:
        return "ALTO"
    return "CRITICO"


def _persistir(item: dict) -> str:
    """Grava no DynamoDB se boto3/credenciais existirem; senao apenas loga."""
    try:
        import boto3
        boto3.resource("dynamodb").Table(DYNAMO_TABLE).put_item(Item=item)
        return "dynamodb"
    except Exception as e:
        print(f"[fallback log] {item} ({e})")
        return "log"


def lambda_handler(event, context=None):
    # API Gateway entrega o corpo como string JSON em event["body"]
    body = event.get("body", event) if isinstance(event, dict) else event
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {}

    risco = float(body.get("risco_sensor", body.get("risco_total", 0)))
    nivel = body.get("nivel") or classificar_nivel(risco)

    agora = datetime.now(timezone.utc)
    alerta = {
        "id": f"{agora:%Y%m%d%H%M%S%f}",
        "ts": agora.isoformat(timespec="seconds"),
        "estacao": body.get("estacao", "desconhecida"),
        "risco_total": risco,
        "nivel": nivel,
        "origem": "lambda_api",
        "mensagem": f"Leitura recebida. Nivel de risco: {nivel}.",
    }
    destino = _persistir(alerta)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"ok": True, "destino": destino, "alerta": alerta},
                           ensure_ascii=False),
    }


if __name__ == "__main__":
    # Teste local do handler
    evento = {"body": json.dumps({
        "estacao": "Estacao Floresta-01",
        "temp_ar": 41.0, "umid_ar": 18.0, "umid_solo": 12.0,
        "fumaca_ppm": 620.0, "risco_sensor": 81.3, "nivel": "CRITICO",
    })}
    print(lambda_handler(evento))

import argparse
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta la variable obligatoria: {name}")
    return value


def mcp_server(label: str, url_name: str, token_name: str, allowed_name: str) -> dict:
    url = os.getenv(url_name, "").strip() or os.getenv("COMPOSIO_MCP_URL", "").strip()
    if not url:
        raise RuntimeError(f"Falta {url_name} (o COMPOSIO_MCP_URL)")
    server = {"type": "mcp", "server_label": label, "server_url": url, "require_approval": "never"}
    token = os.getenv(token_name, "").strip()
    composio_key = os.getenv("COMPOSIO_MCP_API_KEY", "").strip()
    if label == "exa" and token:
        server["headers"] = {"x-api-key": token}
    elif label in {"notion", "gmail"} and composio_key and not os.getenv(url_name, "").strip():
        server["headers"] = {"x-consumer-api-key": composio_key}
    elif token:
        server["authorization"] = token
    allowed = [x.strip() for x in os.getenv(allowed_name, "").split(",") if x.strip()]
    if allowed:
        server["allowed_tools"] = allowed
    return server


def run_agent() -> str:
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)
    local_now = now.astimezone(ZoneInfo(os.getenv("TIMEZONE", "America/Mexico_City")))
    destination = required("DESTINATION_EMAIL")
    gmail_account = os.getenv("COMPOSIO_GMAIL_ACCOUNT_ALIAS", "rfeg1980").strip()
    notion_parent = os.getenv("NOTION_PARENT_PAGE_ID", "").strip()
    parent_instruction = (
        f"Crea la página dentro del parent page de Notion con ID {notion_parent}."
        if notion_parent
        else "Crea la página en el espacio de Notion al que tenga acceso la conexión."
    )

    client = OpenAI(api_key=required("OPENAI_API_KEY"))
    tools = [
        mcp_server("exa", "EXA_MCP_URL", "EXA_MCP_TOKEN", "EXA_ALLOWED_TOOLS"),
        mcp_server("notion", "NOTION_MCP_URL", "NOTION_MCP_TOKEN", "NOTION_ALLOWED_TOOLS"),
        mcp_server("gmail", "GMAIL_MCP_URL", "GMAIL_MCP_TOKEN", "GMAIL_ALLOWED_TOOLS"),
    ]

    prompt = f"""
Ejecuta el boletín diario de noticias de inteligencia artificial.

Fecha/hora actual local: {local_now.isoformat()}.
Ventana exacta de búsqueda: desde {start.isoformat()} hasta {now.isoformat()} (últimas 24 horas).
Destinatario del correo: {destination}.
Cuenta Gmail remitente de Composio: usa exclusivamente la conexión identificada como "{gmail_account}".

Proceso obligatorio:
1. Usa el servidor MCP de Exa para buscar noticias reales, relevantes y publicadas dentro de esa ventana. Prioriza anuncios, investigación, modelos, regulación y productos con impacto amplio. No inventes ni rellenes noticias si hay menos de cinco resultados válidos.
2. Selecciona como máximo 5 noticias distintas. Para cada una redacta en español un resumen de 2-3 frases y conserva título, fuente, fecha de publicación y URL original.
3. Usa el servidor MCP de Notion para crear una página titulada "Noticias de IA — {local_now.strftime('%Y-%m-%d')}". {parent_instruction} Incluye fecha de generación, una introducción corta y una sección numerada con cada noticia y su enlace.
4. Usa el servidor MCP de Gmail para enviar (no solo guardar como borrador) un correo a {destination}. El asunto debe ser "Noticias de IA — {local_now.strftime('%Y-%m-%d')}". Incluye el resumen completo y el enlace clicable a la página de Notion.

Reglas: todo el contenido debe ser verificable; usa únicamente URLs devueltas por Exa; no envíes el correo hasta haber creado la página de Notion; si Notion devuelve una URL, úsala literalmente en el correo.

Al final responde únicamente JSON válido con esta forma:
{{"notion_url":"https://...","email_sent":true,"news_count":0,"titles":["..."]}}
"""

    response = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-5"), tools=tools, input=prompt)
    logging.info("Resultado del agente: %s", response.output_text)
    return response.output_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecuta el boletín diario de noticias de IA")
    parser.add_argument("--once", action="store_true", help="Ejecuta una sola vez; el horario lo gestiona Windows Task Scheduler")
    args = parser.parse_args()
    if not args.once:
        parser.error("Usa --once; programa este comando con el Programador de tareas de Windows")
    try:
        output = run_agent()
        try:
            json.loads(output)
        except json.JSONDecodeError:
            logging.warning("El modelo no devolvió JSON estricto; conserva el resultado en el log.")
    except Exception:
        logging.exception("Falló la ejecución del boletín")
        raise

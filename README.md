# Agente diario de noticias de IA

Este proyecto ejecuta un flujo diario a las 07:00 (zona horaria configurable):

1. Consulta Exa mediante MCP por las noticias más relevantes sobre inteligencia artificial de las últimas 24 horas.
2. Selecciona como máximo 5 y redacta un resumen breve en español, conservando título, fuente, fecha y enlace.
3. Crea una página en Notion con el resumen y los enlaces.
4. Envía un correo a `DESTINATION_EMAIL` con el resumen y el enlace de Notion.

El flujo usa la Responses API de OpenAI con servidores MCP remotos. Los servidores, tokens y nombres de herramientas se configuran en `.env`; no se guardan secretos en el repositorio.

## Requisitos

- Python 3.11+
- Una API key de OpenAI.
- Un endpoint MCP de Exa.
- Un endpoint MCP de Notion y otro de Gmail, normalmente creados desde Composio, o un endpoint MCP que exponga ambos servicios.
- Las autorizaciones de Exa, Notion y Gmail configuradas en esos endpoints.

## Instalación

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Completa `.env` y prueba manualmente:

```powershell
python agent.py --once
```

Si usas un único servidor MCP de Composio para Notion y Gmail, coloca en `.env` la URL `https://connect.composio.dev/mcp` y la API key de Composio en `COMPOSIO_MCP_API_KEY`. El agente la envía mediante el encabezado `x-consumer-api-key`; no la compartas en el chat ni la guardes en Git.

## Ejecución autónoma en la nube (recomendado)

El archivo `.github/workflows/daily-ai-news.yml` ejecuta el agente todos los días a las 07:00 de Ciudad de México en GitHub Actions. La computadora local no necesita estar encendida.

En el repositorio de GitHub, ve a `Settings → Secrets and variables → Actions` y crea estos secretos:

- `OPENAI_API_KEY`
- `EXA_MCP_TOKEN`
- `COMPOSIO_MCP_API_KEY`

Después de publicar el proyecto, puedes lanzar una prueba desde `Actions → Boletín diario de noticias de IA → Run workflow`.

GitHub Actions puede iniciar el job con algunos minutos de retraso; si necesitas una hora exacta con garantías operativas, migraremos el mismo agente a un servicio con cron dedicado.

## Ejecución local opcional

La ejecución local solo sirve para pruebas manuales o como respaldo.

Ejecuta PowerShell como tu usuario y registra la tarea:

```powershell
$project = (Get-Location).Path
$python = Join-Path $project '.venv\Scripts\python.exe'
schtasks /Create /SC DAILY /ST 07:00 /TN "Agente noticias IA" /TR "`"$python`" `"$project\agent.py`" --once" /F
```

La hora debe corresponder a `TIMEZONE` (por defecto `America/Mexico_City`). Si el equipo está apagado a esa hora, activa en el Programador de tareas la opción de ejecutar al iniciar cuando se perdió el horario.

## Seguridad y operación

- La acción de Gmail es de envío, no solo de borrador; usa una cuenta de correo autorizada específicamente para este agente.
- Antes de producción, prueba con `DESTINATION_EMAIL` apuntando a ti mismo.
- El agente no inventa enlaces: solo usa URLs devueltas por Exa.
- Los servidores MCP son terceros y reciben los datos necesarios para realizar cada operación; revisa sus políticas de retención y permisos.

## Nombres de herramientas MCP

Por defecto el modelo descubre las herramientas disponibles. Si quieres restringirlas, llena `EXA_ALLOWED_TOOLS`, `NOTION_ALLOWED_TOOLS` y `GMAIL_ALLOWED_TOOLS` con nombres separados por comas. Esto es recomendable en producción.

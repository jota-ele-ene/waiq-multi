"""
Envío de emails por SMTP.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List

logger = logging.getLogger("waiq-radar.email")


def send_radar_email(
    news: List[dict],
    opinion: dict,
    angles: List[str],
    config: dict,
    date_str: str,
    tool_log: list,
) -> bool:
    """Compone y envía el email principal del radar."""
    subject = f"WAIQ Radar {date_str} - {' / '.join(angles)}"
    body = _compose_main_body(news, opinion, angles, date_str)

    success = _send_smtp(
        to=config["email"]["to"],
        subject=subject,
        body=body,
        config=config,
    )

    tool_log.append({
        "step": len(tool_log) + 1,
        "tool": "send_email (SMTP)",
        "model": "N/A",
        "action": f"Enviar radar a {config['email']['to']}",
        "result": "OK" if success else "ERROR",
    })

    return success


def send_diagnostic_email(
    tool_log: list,
    config: dict,
    date_str: str,
    news_count: int,
    image_stats: dict,
    files_created: int,
) -> bool:
    """Envía el email de diagnóstico con el log completo de ejecución."""
    if not config["email"].get("send_diagnostic", False):
        return True

    subject = f"WAIQ Radar {date_str} - Diagnóstico de ejecución"
    body = _compose_diagnostic_body(
        tool_log, date_str, news_count, image_stats, files_created
    )

    success = _send_smtp(
        to=config["email"]["to"],
        subject=subject,
        body=body,
        config=config,
    )

    return success


def _compose_main_body(
    news: List[dict],
    opinion: dict,
    angles: List[str],
    date_str: str,
) -> str:
    """Compone el body del email principal en texto plano."""
    lines = []
    lines.append(f"WAIQ RADAR TECNOLÓGICO - {date_str}")
    lines.append("=" * 50)
    lines.append("")
    lines.append("NOTICIAS RELEVANTES")
    lines.append("-" * 30)
    lines.append("")

    for i, item in enumerate(news):
        lines.append(f"{i+1}. {item.get('title_es', '')}")
        lines.append(f"   Fuente: {item.get('source', '')}")
        lines.append(f"   Enlace: {item.get('url', '')}")
        lines.append(f"   {item.get('description_es', '')}")
        angles_str = ", ".join(item.get("angles", []))
        lines.append(f"   Ángulo WAIQ: {angles_str}")
        lines.append("")

    lines.append("")
    lines.append("-" * 50)
    lines.append("")
    lines.append("PROPUESTA DE ARTÍCULO DE OPINIÓN")
    lines.append("-" * 40)
    lines.append("")
    lines.append(f"Título: \"{opinion.get('title_es', '')}\"")
    lines.append(f"Ángulo editorial: {' / '.join(angles)}")
    lines.append("")
    lines.append(opinion.get("body_es", ""))
    lines.append("")
    lines.append("-" * 50)
    lines.append("Radar generado automáticamente para waiq.technology")

    return "\n".join(lines)


def _compose_diagnostic_body(
    tool_log: list,
    date_str: str,
    news_count: int,
    image_stats: dict,
    files_created: int,
) -> str:
    """Compone el body del email de diagnóstico."""
    search_calls = sum(1 for t in tool_log if "search" in t["tool"].lower())
    llm_calls = sum(1 for t in tool_log if "llm" in t["tool"].lower())
    email_calls = sum(1 for t in tool_log if "email" in t["tool"].lower())
    errors = [t for t in tool_log if "ERROR" in t.get("result", "")]

    lines = []
    lines.append(f"WAIQ RADAR - DIAGNÓSTICO DE EJECUCIÓN")
    lines.append("=" * 50)
    lines.append(f"Fecha: {date_str}")
    lines.append("")
    lines.append("RESUMEN")
    lines.append("-" * 20)
    lines.append(f"Total de llamadas a herramientas: {len(tool_log)}")
    lines.append(f"  - Búsquedas web: {search_calls}")
    lines.append(f"  - Llamadas LLM: {llm_calls}")
    lines.append(f"  - Emails enviados: {email_calls}")
    lines.append(f"Noticias seleccionadas: {news_count}")
    lines.append(f"Archivos creados en GitHub: {files_created}")
    lines.append(f"Imágenes: {image_stats.get('ok', 0)} descargadas / {image_stats.get('total', 0)} intentadas")
    lines.append("")
    lines.append("DETALLE DE LLAMADAS")
    lines.append("-" * 30)
    lines.append("")

    for entry in tool_log:
        lines.append(f"#{entry['step']} - {entry['tool']}")
        lines.append(f"     Modelo: {entry.get('model', 'N/A')}")
        lines.append(f"     Acción: {entry.get('action', '')}")
        lines.append(f"     Resultado: {entry.get('result', '')}")
        lines.append("")

    lines.append("ERRORES O INCIDENCIAS")
    lines.append("-" * 30)
    if errors:
        for e in errors:
            lines.append(f"  - #{e['step']} {e['tool']}: {e['result']}")
    else:
        lines.append("  Ninguna incidencia.")

    lines.append("")
    lines.append("-" * 50)
    lines.append("Diagnóstico generado automáticamente")

    return "\n".join(lines)


def _send_smtp(to: str, subject: str, body: str, config: dict) -> bool:
    """Envía un email por SMTP con trazas detalladas de configuración."""
    smtp_conf = config["email"]["smtp"]
    from_name = config["email"].get("from_name", "WAIQ Radar")
    from_addr = smtp_conf["username"]

    # ── Trazas de configuración leída ─────────────────────────────────────
    host     = smtp_conf.get("host", "")
    port     = smtp_conf.get("port", "")
    username = smtp_conf.get("username", "")
    password = smtp_conf.get("password", "")

    # Mostrar contraseña enmascarada: primeros 2 + últimos 2 chars, resto '*'
    if password and len(password) >= 4:
        masked = password[:2] + "*" * (len(password) - 4) + password[-2:]
    elif password:
        masked = "*" * len(password)
    else:
        masked = "(vacía)"

    logger.info("─── SMTP config ────────────────────────────────")
    logger.info(f"  host     : {host!r}")
    logger.info(f"  port     : {port!r}")
    logger.info(f"  username : {username!r}")
    logger.info(f"  password : {masked}  (len={len(password)})")
    logger.info(f"  from     : {from_name} <{from_addr}>")
    logger.info(f"  to       : {to!r}")
    logger.info(f"  subject  : {subject!r}")
    logger.info("────────────────────────────────────────────────")

    # Advertencias sobre valores vacíos o sospechosos
    if not host:
        logger.error("[smtp] 'host' está vacío en config.yaml")
    if not username:
        logger.error("[smtp] 'username' está vacío en config.yaml")
    if not password:
        logger.error("[smtp] 'password' está vacío — necesitas una App Password de Google")
    elif " " in password:
        logger.warning(
            "[smtp] La contraseña contiene espacios. "
            "Las App Passwords de Google se muestran con espacios pero deben "
            "pegarse SIN espacios en config.yaml."
        )
    elif len(password) != 16:
        logger.warning(
            f"[smtp] La contraseña tiene {len(password)} chars. "
            "Las App Passwords de Google tienen exactamente 16 chars sin espacios. "
            "Comprueba que la has copiado completa y sin espacios."
        )
    # ─────────────────────────────────────────────────────────────────────

    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        logger.info(f"[smtp] Conectando a {host}:{port}...")
        with smtplib.SMTP(smtp_conf["host"], smtp_conf["port"]) as server:
            server.set_debuglevel(1)  # muestra diálogo SMTP completo en stderr

            logger.info("[smtp] Iniciando STARTTLS...")
            server.starttls()

            logger.info(f"[smtp] Autenticando como {username!r}...")
            server.login(smtp_conf["username"], smtp_conf["password"])

            logger.info(f"[smtp] Enviando mensaje a {to!r}...")
            server.send_message(msg)

        logger.info(f"[smtp] ✓ Email enviado correctamente: {subject!r}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(
            f"[smtp] Error de autenticación (535): usuario o contraseña incorrectos.\n"
            f"  · Comprueba que {username!r} es tu cuenta Gmail correcta.\n"
            f"  · La contraseña debe ser una App Password (16 chars, sin espacios),\n"
            f"    NO tu contraseña normal de Google.\n"
            f"  · Genera una en: https://myaccount.google.com/apppasswords\n"
            f"    (requiere verificación en 2 pasos activa)\n"
            f"  Detalle: {e}"
        )
        return False

    except smtplib.SMTPConnectError as e:
        logger.error(
            f"[smtp] No se pudo conectar a {host}:{port}. "
            f"Comprueba host/port en config.yaml. Detalle: {e}"
        )
        return False

    except smtplib.SMTPException as e:
        logger.error(f"[smtp] Error SMTP inesperado: {e}")
        return False

    except Exception as e:
        logger.error(f"[smtp] Error genérico enviando email: {e}")
        return False
"""
Publicación en GitHub: genera archivos .md Hugo, descarga imágenes y hace commit+push.
"""

import os
import re
import logging
import subprocess
import httpx
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger("waiq-radar.publisher")


def _mask(value: str, visible: int = 4) -> str:
    """Enmascara un string sensible mostrando solo los primeros `visible` chars."""
    if not value:
        return "(vacío)"
    if len(value) <= visible:
        return "*" * len(value)
    return value[:visible] + "*" * (len(value) - visible)


def _check_token(token: str, repo: str) -> None:
    """
    Verifica el token contra la GitHub API antes de intentar el clone/push.
    Loguea: identidad autenticada, scopes del token y permisos sobre el repo.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    logger.info("─── GitHub token check ─────────────────────────")
    logger.info(f"  token (masked) : {_mask(token, 8)}")
    logger.info(f"  len(token)     : {len(token)}")

    # 1. Identidad del token
    try:
        r = httpx.get("https://api.github.com/user",
                      headers=headers, timeout=10)
        scopes = r.headers.get("x-oauth-scopes", "(no scopes header)")
        token_type = r.headers.get("x-oauth-client-id", "(no client-id)")
        if r.status_code == 200:
            login = r.json().get("login", "?")
            logger.info(f"  autenticado como : {login!r}")
        elif r.status_code == 401:
            logger.error("  token inválido o expirado (HTTP 401)")
        else:
            logger.warning(f"  /user → HTTP {r.status_code}: {r.text[:200]}")
        logger.info(f"  x-oauth-scopes   : {scopes}")
        logger.info(f"  x-oauth-client-id: {token_type}")
    except Exception as e:
        logger.warning(f"  No se pudo verificar identidad: {e}")

    # 2. Permisos sobre el repo concreto
    try:
        r = httpx.get(
            f"https://api.github.com/repos/{repo}",
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            perms = data.get("permissions", {})
            logger.info(f"  repo '{repo}' encontrado")
            logger.info(f"  permissions.push  : {perms.get('push', '?')}")
            logger.info(f"  permissions.admin : {perms.get('admin', '?')}")
            if not perms.get("push"):
                logger.error(
                    "  ✗ El token NO tiene permiso de push sobre este repo. "
                    "Genera un nuevo token con scope 'repo' (clásico) "
                    "o permisos 'Contents: Read & Write' (fine-grained)."
                )
            else:
                logger.info("  ✓ El token tiene permiso de push")
        elif r.status_code == 404:
            logger.error(
                f"  Repo '{repo}' no encontrado (404). "
                "¿El nombre es correcto? ¿El token puede verlo?"
            )
        elif r.status_code == 403:
            logger.error(
                f"  Acceso denegado al repo (403). "
                "El token existe pero no tiene permisos suficientes."
            )
        else:
            logger.warning(
                f"  /repos/{repo} → HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.warning(f"  No se pudo verificar permisos del repo: {e}")

    logger.info("────────────────────────────────────────────────")


def publish_to_github(
    news: List[dict],
    opinion: dict,
    config: dict,
    date_str: str,
    date_iso: str,
    tool_log: list,
) -> dict:
    """
    Clona el repo, genera archivos, descarga imágenes y hace push.
    Retorna estadísticas {files_created, images_ok, images_total}.
    """
    gh_conf = config["github"]
    token = gh_conf.get("token", "")
    repo = gh_conf["repo"]
    branch = gh_conf["branch"]

    # ── Trazas de configuración GitHub ───────────────────────────────────
    logger.info("─── GitHub config ──────────────────────────────")
    logger.info(f"  repo   : {repo!r}")
    logger.info(f"  branch : {branch!r}")
    logger.info(f"  token  : {_mask(token, 8)}  (len={len(token)})")
    if not token:
        logger.error(
            "  'token' está vacío en config.yaml → github.token. "
            "Genera un Personal Access Token en "
            "https://github.com/settings/tokens con scope 'repo'."
        )
    elif len(token) < 20:
        logger.warning(
            f"  El token parece demasiado corto ({len(token)} chars). ¿Está completo?")
    elif token.startswith("ghp_"):
        logger.info("  tipo: Classic PAT (ghp_...)")
    elif token.startswith("github_pat_"):
        logger.info("  tipo: Fine-grained PAT (github_pat_...)")
    else:
        logger.warning(
            f"  tipo: desconocido (no empieza por ghp_ ni github_pat_)")
    logger.info("────────────────────────────────────────────────")

    # Verificar token contra la API antes de clonar
    if token:
        _check_token(token, repo)
    # ─────────────────────────────────────────────────────────────────────

    repo_url = f"https://x-access-token:{token}@github.com/{repo}.git"
    work_dir = Path("/tmp/waiq-radar-publish")

    stats = {"files_created": 0, "images_ok": 0, "images_total": 0}

    # 1. Clonar repo
    logger.info(f"Clonando {repo}...")
    if work_dir.exists():
        subprocess.run(["rm", "-rf", str(work_dir)], check=True)

    # Loguear URL de clone con token enmascarado
    safe_url = f"https://x-access-token:{_mask(token, 8)}@github.com/{repo}.git"
    logger.info(f"  git clone URL (masked): {safe_url}")

    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(work_dir)],
        capture_output=True, text=True,
    )
    logger.info(f"  git clone returncode: {result.returncode}")
    if result.stdout.strip():
        logger.info(f"  git clone stdout: {result.stdout.strip()[:300]}")
    if result.stderr.strip():
        logger.info(f"  git clone stderr: {result.stderr.strip()[:300]}")

    if result.returncode != 0:
        logger.error(f"Error clonando: {result.stderr}")
        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "git clone",
            "model": "N/A",
            "action": f"Clonar {repo}",
            "result": f"ERROR — {result.stderr[:200]}",
        })
        return stats

    tool_log.append({
        "step": len(tool_log) + 1,
        "tool": "git clone",
        "model": "N/A",
        "action": f"Clonar {repo}",
        "result": "OK",
    })

    # Configurar git
    subprocess.run(["git", "config", "user.email", "hi@jln.bz"], cwd=work_dir)
    subprocess.run(["git", "config", "user.name", "WAIQ Radar"], cwd=work_dir)

    es_dir = work_dir / gh_conf["paths"]["article_es"]
    en_dir = work_dir / gh_conf["paths"]["article_en"]
    img_dir = work_dir / gh_conf["paths"]["images"]
    es_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    # 2. Generar archivos de noticias
    for item in news:
        slug = _slugify(item.get("title_en", item.get("title_es", "untitled")))
        filename = f"{date_iso}-{slug}.md"

        # Descargar imagen
        img_path = _download_og_image(
            item.get("url", ""), slug, date_iso, img_dir, tool_log)
        if img_path:
            stats["images_ok"] += 1
        stats["images_total"] += 1

        image_ref = f"/images/upload/{img_path.name}" if img_path else None
        item["image"] = image_ref

        # ES
        _write_article(
            path=es_dir / filename,
            title=item.get("title_es", ""),
            topics=item.get("topics", []),
            areas=item.get("areas", []),
            date=f"{date_iso}T08:00:00.000+01:00",
            description=item.get("description_es", ""),
            button_label=item.get(
                "button_label_es", f"Leer en {item.get('source', '')}"),
            button_url=item.get("url", ""),
            image=image_ref,
            body=item.get("description_es", ""),
        )
        stats["files_created"] += 1

        # EN
        _write_article(
            path=en_dir / filename,
            title=item.get("title_en", ""),
            topics=item.get("topics", []),
            areas=item.get("areas", []),
            date=f"{date_iso}T08:00:00.000+01:00",
            description=item.get("description_en", ""),
            button_label=item.get(
                "button_label_en", f"Read in {item.get('source', '')}"),
            button_url=item.get("url", ""),
            image=image_ref,
            body=item.get("description_en", ""),
        )
        stats["files_created"] += 1

    # 3. Generar artículo de opinión
    opinion_slug = _slugify(opinion.get("title_en", "opinion"))
    opinion_filename = f"{date_iso}-{opinion_slug}.md"

    opinion_references = [
        {
            "url": item.get("url", ""),
            "image": item.get("image"),
            "source": item.get("source", ""),
            "title": item.get("title_en", item.get("title_es", "")),
        }
        for item in news
    ]

    # ES
    _write_article(
        path=es_dir / opinion_filename,
        title=opinion.get("title_es", ""),
        topics=opinion.get("topics", ["ai", "quantum", "web3"]),
        areas=opinion.get("areas", ["technology", "regulation"]),
        date=f"{date_iso}T08:00:00.000+01:00",
        description=opinion.get("description_es", ""),
        button_label="Leer artículo",
        button_url=None,
        image=None,
        body=opinion.get("body_es", ""),
        radar=True,
        references=opinion_references,
    )
    stats["files_created"] += 1

    # EN
    _write_article(
        path=en_dir / opinion_filename,
        title=opinion.get("title_en", ""),
        topics=opinion.get("topics", ["ai", "quantum", "web3"]),
        areas=opinion.get("areas", ["technology", "regulation"]),
        date=f"{date_iso}T08:00:00.000+01:00",
        description=opinion.get("description_en", ""),
        button_label="Read article",
        button_url=None,
        image=None,
        body=opinion.get("body_en", ""),
        radar=True,
        references=opinion_references,
    )
    stats["files_created"] += 1

    tool_log.append({
        "step": len(tool_log) + 1,
        "tool": "file_generation",
        "model": "N/A",
        "action": f"Generar {stats['files_created']} archivos .md",
        "result": f"OK — {stats['files_created']} archivos",
    })

    # 4. Commit y push
    subprocess.run(["git", "add", "-A"], cwd=work_dir, check=True)

    commit_msg = gh_conf["commit_message_template"].format(date=date_str)
    commit_result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=work_dir, capture_output=True, text=True,
    )
    logger.info(f"  git commit returncode: {commit_result.returncode}")
    if commit_result.stdout.strip():
        logger.info(
            f"  git commit stdout: {commit_result.stdout.strip()[:300]}")
    if commit_result.stderr.strip():
        logger.info(
            f"  git commit stderr: {commit_result.stderr.strip()[:300]}")

    if "nothing to commit" in commit_result.stdout:
        logger.warning("Nada que commitear (¿archivos duplicados?)")
        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "git commit+push",
            "model": "N/A",
            "action": commit_msg,
            "result": "SKIP — nothing to commit",
        })
        return stats

    logger.info(f"  git push → origin/{branch}")
    # push_result = subprocess.run(
    #    ["git", "push", "origin", branch],
    #    cwd=work_dir, capture_output=True, text=True,
    # )

    try:
        push_result = subprocess.run(
            ["git", "push", "origin", branch],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"[push] Timeout tras 120s: {e}")
        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "git commit+push",
            "model": "N/A",
            "action": commit_msg,
            "result": "ERROR — timeout en git push",
        })
    return stats

    logger.info(f"  git push returncode: {push_result.returncode}")
    if push_result.stdout.strip():
        logger.info(f"  git push stdout: {push_result.stdout.strip()[:300]}")
    if push_result.stderr.strip():
        logger.info(f"  git push stderr: {push_result.stderr.strip()[:300]}")

    if push_result.returncode == 0:
        logger.info(f"Push exitoso: {commit_msg}")
        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "git commit+push",
            "model": "N/A",
            "action": commit_msg,
            "result": f"OK — {stats['files_created']} archivos + {stats['images_ok']} imágenes",
        })
    else:
        # Diagnóstico específico del error de push
        stderr = push_result.stderr
        if "403" in stderr or "Permission" in stderr or "denied" in stderr:
            logger.error(
                f"[push] Error 403 — Permiso denegado.\n"
                f"  Causas más comunes:\n"
                f"  1. El token no tiene scope 'repo' (classic) o 'Contents: Write' (fine-grained).\n"
                f"     → Genera uno nuevo en https://github.com/settings/tokens\n"
                f"  2. El token es de otro usuario que no tiene acceso al repo '{repo}'.\n"
                f"  3. El token ha expirado.\n"
                f"  4. Para fine-grained PATs: el repo '{repo}' no está incluido en el token.\n"
                f"  Detalle git: {stderr[:300]}"
            )
        elif "Authentication failed" in stderr:
            logger.error(
                f"[push] Autenticación fallida. Token inválido o expirado. Detalle: {stderr[:200]}")
        elif "could not read Username" in stderr:
            logger.error(
                f"[push] Git no encontró credenciales. ¿Token vacío? Detalle: {stderr[:200]}")
        else:
            logger.error(f"[push] Error desconocido: {stderr[:300]}")

        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "git commit+push",
            "model": "N/A",
            "action": commit_msg,
            "result": f"ERROR — {push_result.stderr[:200]}",
        })

    return stats


def _write_article(
    path: Path,
    title: str,
    topics: list,
    areas: list,
    date: str,
    description: str,
    button_label: str,
    button_url: Optional[str],
    image: Optional[str],
    body: str,
    radar: bool = False,
    references: Optional[List[dict]] = None,
):
    """Escribe un archivo .md con front matter YAML para Hugo."""
    lines = ["---"]
    lines.append(f'title: "{_escape_yaml(title)}"')
    lines.append("topics:")
    for t in topics:
        lines.append(f"  - {t}")
    lines.append("areas:")
    for a in areas:
        lines.append(f"  - {a}")
    lines.append(f"date: {date}")
    lines.append("description: >-")
    lines.append(f"  {description}")
    lines.append('draft: "false"')
    lines.append('featured: "true"')
    lines.append(f"button_label: {button_label}")
    if button_url:
        lines.append(f"button_url: {button_url}")
    if image:
        lines.append(f"image: {image}")
    if radar:
        lines.append("radar: true")
    if references:
        lines.append("references:")
        for ref in references:
            lines.append(f"  - url: {ref.get('url', '')}")
            if ref.get("image"):
                lines.append(f"    image: {ref['image']}")
            lines.append(f"    source: {ref.get('source', '')}")
            lines.append(f'    title: "{_escape_yaml(ref.get("title", ""))}"')
    lines.append("---")

    content = "\n".join(lines)
    if body:
        content += "\n\n" + body
    path.write_text(content, encoding="utf-8")


def _download_og_image(
    page_url: str,
    slug: str,
    date_iso: str,
    img_dir: Path,
    tool_log: list,
) -> Optional[Path]:
    """Intenta descargar la imagen og:image de una URL."""
    try:
        resp = httpx.get(
            page_url,
            headers={"User-Agent": "Mozilla/5.0 (WAIQ Radar)"},
            follow_redirects=True,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        og_tag = soup.find("meta", property="og:image")
        if not og_tag or not og_tag.get("content"):
            tool_log.append({
                "step": len(tool_log) + 1,
                "tool": "fetch_og_image",
                "model": "N/A",
                "action": f"og:image de {page_url[:60]}",
                "result": "SKIP — no og:image encontrado",
            })
            return None

        img_url = og_tag["content"]

        ext = "jpg"
        if ".png" in img_url.lower():
            ext = "png"
        elif ".webp" in img_url.lower():
            ext = "webp"

        filename = f"{date_iso}-{slug}.{ext}"
        filepath = img_dir / filename

        img_resp = httpx.get(
            img_url,
            headers={"User-Agent": "Mozilla/5.0 (WAIQ Radar)"},
            follow_redirects=True,
            timeout=15,
        )
        img_resp.raise_for_status()

        if len(img_resp.content) < 1000:
            tool_log.append({
                "step": len(tool_log) + 1,
                "tool": "fetch_og_image",
                "model": "N/A",
                "action": f"Descargar {img_url[:60]}",
                "result": f"SKIP — archivo demasiado pequeño ({len(img_resp.content)}b)",
            })
            return None

        filepath.write_bytes(img_resp.content)

        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "fetch_og_image",
            "model": "N/A",
            "action": f"Descargar {img_url[:60]}",
            "result": f"OK — {len(img_resp.content)} bytes → {filename}",
        })
        return filepath

    except Exception as e:
        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "fetch_og_image",
            "model": "N/A",
            "action": f"og:image de {page_url[:60]}",
            "result": f"ERROR — {str(e)[:100]}",
        })
        return None


def _slugify(text: str) -> str:
    """Convierte texto en slug URL-friendly."""
    text = text.lower().strip()
    text = re.sub(r'[áàä]', 'a', text)
    text = re.sub(r'[éèë]', 'e', text)
    text = re.sub(r'[íìï]', 'i', text)
    text = re.sub(r'[óòö]', 'o', text)
    text = re.sub(r'[úùü]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].strip('-')


def _escape_yaml(text: str) -> str:
    """Escapa comillas en strings YAML."""
    return text.replace('"', '\\"')

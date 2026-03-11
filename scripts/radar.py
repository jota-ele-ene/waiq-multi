import os
import sys
import json
import argparse
import base64
import requests
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai

# Configuración
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

try:
    from config import radar_config as cfg
except ImportError:
    print("Error: No config found")
    sys.exit(1)

class WaiqRadar:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_id = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
        self.repo_raw = os.getenv("GITHUB_REPO", "").strip()
        self.github_token = os.getenv("GITHUB_TOKEN", "").strip()
        self.branch = os.getenv("GITHUB_BRANCH", "main").strip()
        # Limpieza de nombre de repo
        self.repo_clean = self.repo_raw.replace("https://github.com/", "").replace(".git", "").strip("/")
        self.client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1beta'})
        self.dest_repo_path = os.path.join(BASE_DIR, "repo_destino")

    def setup_dest_repo(self):
        if not os.path.exists(self.dest_repo_path):
            os.makedirs(self.dest_repo_path, exist_ok=True)
            print("Carpeta destino creada.")

    def save_to_local(self, art):
        for lang in ['es', 'en']:
            folder = os.path.join(self.dest_repo_path, "content", lang)
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, f"{art['filename']}.md"), "w", encoding="utf-8") as f:
                f.write(f"{art[f'frontmatter_{lang}']}\n\n{art[f'body_{lang}']}")

    def fetch_and_generate(self):
        print("Consultando a Gemini...")
        prompt = f"{cfg.WAIQ_PROMPT}\n\nDate: {datetime.now().strftime('%Y-%m-%d')}"
        try:
            response = self.client.models.generate_content(model=self.model_id, contents=prompt)
            raw = response.text.strip()
            if "
http://googleusercontent.com/immersive_entry_chip/0

**¿Quieres que verifiquemos si el error de conexión desaparece con este código más limpio?**
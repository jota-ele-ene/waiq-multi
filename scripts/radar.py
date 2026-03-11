import os
import sys
import json
import argparse
import requests
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from google import genai

# --- Configuración de Rutas y Entorno ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

try:
    from config import radar_config as cfg
except ImportError:
    print("❌ Error: No se encontró 'config/radar_config.py'")
    sys.exit(1)

class WaiqRadar:
    def __init__(self, verbose=False, output_dir=None):
        self.verbose = verbose
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_id = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
        
        # Precios 2026: Gemini 2.5 Flash (0.10$ / 1M input, 0.40$ / 1M output)
        self.pricing = {"input": 0.10, "output": 0.40}
        
        self.client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1beta'})
        
        self.output_base = output_dir or os.path.join(BASE_DIR, "output")
        self.logs_dir = os.path.join(BASE_DIR, "logs")
        
        for sub in ['es', 'en', 'static/images/upload']:
            os.makedirs(os.path.join(self.output_base, sub), exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def v_print(self, message):
        if self.verbose: print(f"🔍 [VERBOSE] {message}")

    def sync_repo(self):
        """Sincroniza el repositorio remoto."""
        print("🔄 Sincronizando repositorio remoto...")
        try:
            # git pull origin main
            res = subprocess.run(["git", "pull", "origin", "main"], cwd=BASE_DIR, capture_output=True, text=True)
            self.v_print(f"Git Output:\n{res.stdout}")
        except Exception as e:
            print(f"⚠️ Advertencia en sincronización: {e}")

    def get_history_and_date(self):
        """Calcula fecha (Editorial - 2 días) y lista archivos existentes."""
        es_path = os.path.join(self.output_base, "es")
        if not os.path.exists(es_path): return (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"), []

        files = [f.replace('.md', '') for f in os.listdir(es_path) if f.endswith('.md')]
        editorials = sorted([f for f in files if "editorial" in f], reverse=True)
        
        since = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        if editorials:
            try:
                date_str = "-".join(editorials[0].split('-')[:3])
                since = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")
                self.v_print(f"Referencia: {editorials[0]} -> Búsqueda desde {since}")
            except: pass
            
        return since, files

    def fetch_and_generate(self, forced_since=None):
        self.sync_repo()
        since, history = self.get_history_and_date()
        since = forced_since or since
        
        print(f"🔎 Investigando desde: {since} (Omitiendo {len(history)} existentes)")
        
        history_ctx = f"HISTORY (Do not repeat): {', '.join(history[-50:])}"
        full_prompt = f"{cfg.WAIQ_PROMPT}\n\nDATE: {datetime.now().strftime('%Y-%m-%d')}\nSINCE: {since}\n{history_ctx}"

        try:
            self.v_print("Llamando a Gemini API...")
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=full_prompt,
                config={'temperature': 0.15}
            )

            # Limpiar y cargar JSON
            raw = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(raw)
            
            # Procesar artículos
            count = 0
            for art in data.get('articles', []):
                if art['filename'] in history:
                    self.v_print(f"Saltado por duplicado: {art['filename']}")
                    continue
                
                self.save_article(art)
                print(f"✅ Generado: {art['filename']}")
                count += 1

            # --- Resumen de Costes ---
            usage = response.usage_metadata
            i_cost = (usage.prompt_token_count / 1_000_000) * self.pricing["input"]
            o_cost = (usage.candidates_token_count / 1_000_000) * self.pricing["output"]
            total_cost = i_cost + o_cost

            print("\n" + "="*30)
            print(f"📊 RESUMEN DE EJECUCIÓN")
            print(f"Artículos nuevos: {count}")
            print(f"Tokens Input: {usage.prompt_token_count}")
            print(f"Tokens Output: {usage.candidates_token_count}")
            print(f"Coste estimado: ${round(total_cost, 5)}")
            print("="*30 + "\n")

            self.save_log(full_prompt, data, usage, total_cost)

        except Exception as e:
            print(f"❌ Error: {e}")

    def save_article(self, art):
        for lang in ['es', 'en']:
            path = os.path.join(self.output_base, lang, f"{art['filename']}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"{art[f'frontmatter_{lang}']}\n\n{art[f'body_{lang}']}")

    def save_log(self, prompt, response, usage, cost):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(self.logs_dir, f"radar_{ts}.json"), "w") as f:
            json.dump({"cost": cost, "usage": str(usage)}, f)

    def publish(self):
        """Publica en el repositorio configurado como origin."""
        print("🚀 Publicando cambios en el repositorio remoto...")
        try:
            subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
            msg = f"Radar Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(["git", "commit", "-m", msg], cwd=BASE_DIR, check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=True)
            print("✨ Publicación completada con éxito.")
        except Exception as e:
            print(f"❌ Error en la publicación: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["full", "only-fetch", "only-publish"])
    parser.add_argument("--since", help="Forzar fecha YYYY-MM-DD")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    radar = WaiqRadar(verbose=args.verbose)
    
    if args.mode in ["full", "only-fetch"]:
        radar.fetch_and_generate(forced_since=args.since)
    
    if args.mode in ["full", "only-publish"]:
        radar.publish()

if __name__ == "__main__":
    main()
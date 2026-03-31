##author: Alu-Speed
##contact: contact@aluspeed.be
##project: https://github.com/Alu-Speed/anime-sama-dl

import re
import os
import subprocess
import json
import uuid
import urllib.request
import sys
import shutil
import time
from pathlib import Path

# --- Gestionnaire des var ---
__version__ = "4.0.2.9.6"
GITHUB_REPO = "Alu-Speed/anime-sama-dl"
FAV_FILE = os.path.join(os.environ["APPDATA"], "Alu-Speed Co", "fav_dirs.json")
HISTORIQUE = os.path.join(os.environ["APPDATA"], "Alu-Speed Co", "history.json")

os.system("title Générateur de liens yt-dlp v4")
print("\n=== Générateur yt-dlp v4.0.2.9.6 Early Access")
print("=== Powered by Alu-Speed ===")
print("=== Vérification de la MàJ... ===")

# --- Vérif MàJ Github ---
def get_latest_prerelease(repo: str):
    url = f"https://api.github.com/repos/{repo}/releases"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())

            pre = [r for r in data if r.get("prerelease")]
            if not pre:
                return None

            return pre[0]
    except Exception as e:
        print("[DEBUG] Internet error 0x00000077i:", e)
        return None

def auto_update(local_version, repo):
    print("🔍 Vérification de mise à jour (pre-release)...")

    latest = get_latest_prerelease(repo)
    if not latest:
        print("⚠ Impossible de vérifier les mises à jour GitHub.")
        print("[DEBUG] Uncaught Error 0x00000049g")
        return

    latest_tag = latest["tag_name"]
    latest_clean = latest_tag.lstrip("v")

    if latest_clean == local_version:
        print(f"✔ Vous êtes à jour (pré-release {local_version})")
        print("Vous faites partie d'une version d'essai. Des bugs peuvent survenir.  En cas de problèmes, installez la version stable depuis le repo GitHub officiel.")
        return

    print(f"🚀 Nouvelle pré-release disponible : {latest_clean} (vous avez {local_version})")

    # Récupération du premier asset
    assets = latest.get("assets", [])
    if not assets:
        print("⚠ Aucune ressource à télécharger dans cette pré-release.")
        print("[DEBUG] No assets found! Check your Internet connection and then try again. 0x00000077i")
        return

    asset = assets[0]
    url = asset["browser_download_url"]
    filename = asset["name"]

    print(f"Téléchargement de {filename}...")
    download_with_progress(url, filename)

    current = os.path.abspath(sys.argv[0])
    backup = current + ".old"

    print("📦 Mise à jour du fichier...")
    try:
        shutil.move(current, backup)
        shutil.move(filename, current)
    except Exception as e:
        print("❌ Erreur lors de la mise à jour :", e)
        print("[DEBUG] MàJ error 0x00000103d")
        return

    print("✔ Mise à jour installée. Redémarrage...")
    os.execv(sys.executable, ["python"] + sys.argv)

# Check de YT-DLP
def ensure_ytdlp():
    print("🔍 Vérification de yt-dlp...")

    def test_ytdlp():
        try:
            subprocess.run(
                ["yt-dlp", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return True
        except Exception:
            return False

    if test_ytdlp():
        print("✔ yt-dlp est déjà installé.")
        return True

    print("⚠ yt-dlp n'est pas installé. Tentative d'installation...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except Exception as e:
        print("❌ Erreur lors de l'installation :", e)

    # --- Re-Check
    if test_ytdlp():
        print("✔ yt-dlp installé avec succès.")
        return True

    print("⚠ Impossible d'utiliser yt-dlp après 2 tentatives.")
    print("⚠ Le programme continue, mais les téléchargements risquent d'échouer.")
    return False

# --- Téléchargement avec barre de progression ---
def download_with_progress(url, dest):
    with urllib.request.urlopen(url) as response:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0

        with open(dest, "wb") as f:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

                percent = downloaded * 100 // total
                bar = "█" * (percent // 2) + "-" * (50 - percent // 2)
                print(f"\r[{bar}] {percent}%", end="")

    print("\nTéléchargement terminé.")

# --- Init ---
try:
    import pyperclip
except ImportError:
    pyperclip = None

ensure_ytdlp()

######## V4 ########

# Download episode db
def download_episodes_js(anime, season, lang):
    anime_slug = anime.lower().replace(" ", "-")
    url = f"https://anime-sama.to/catalogue/{anime_slug}/saison{season}/{lang}/episodes.js"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Alu-Speed Systems/4.0 (Windows NT 12.0; Win64; x64)"
        }
    )

    try:
        with urllib.request.urlopen(req) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print("[DEBUG] erreur episodes.js 0x00000133e :", e)
        return None

# Lecture JS + Detection
def extract_all_readers(js_content):
    readers = {}
    matches = re.findall(r"var (eps\d+) = \[(.*?)\];", js_content, re.S)
    for eps_name, content in matches:
        links = re.findall(r"'(.*?)'", content)
        readers[eps_name] = links
    return readers

def detect_reader_type(url):
    if "sibnet.ru" in url:
        return "Sibnet"
    if "sendvid.com" in url:
        return "Sendvid"
    if "myvi.tv" in url:
        return "Myvi"
    if "vidmoly.to" in url:
        return "Vidmoly"
    return "Other"

# Affichage User
def group_readers_by_site(readers):
    grouped = {
        "Sibnet": [],
        "Sendvid": [],
        "Myvi": [],
        "Vidmoly": [],
        "Other": []
    }
    for eps_name, links in readers.items():
        if not links:
            continue
        site = detect_reader_type(links[0])
        grouped[site].append(eps_name)
    return grouped

def choose_site(grouped):
    print("\n=== Choix du site ===")
    print("Veuillez noter que yt-dlp peut ne pas prendre en charge certains sites!")
    sites = [s for s in grouped.keys() if grouped[s]]
    if not sites:
        print("⚠ Aucun lecteur détecté dans episodes.js")
        print("[DEBUG] erreur episodes.js 0x00000133nd : No data")
        return None
    for i, site in enumerate(sites, start=1):
        print(f"{i}. {site}")
    while True:
        choice = input("Choix : ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(sites):
            return sites[int(choice)-1]
        print("⚠ Choix invalide.")
        print("[DEBUG] Invalid Choice 0x00854972c")
        
# Grabbing
def get_links_for_site(grouped, readers, site):
    eps_list = grouped[site]
    eps_name = eps_list[0]
    return readers.get(eps_name, [])

import webbrowser

def check_easter_egg(anime, lang):
    if anime.lower() == "bad apple" and lang.lower() == "bad apple":
        print("\n🍎 Easter Egg détecté : BAD APPLE MODE ✨")
        print("Ouverture de Bad Apple dans votre navigateur...\n")
        webbrowser.open("https://www.youtube.com/watch?v=FtutLA63Cp8")
        time.sleep(2)
        return True
    return False

######## OLD V3 ########

# Lancement auto-update
auto_update(__version__, GITHUB_REPO)

# --- Fonctions pour gérer les favoris ---
def load_favorites():
    if not os.path.exists(FAV_FILE):
        return {}
    try:
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_favorites(favorites):
    os.makedirs(os.path.dirname(FAV_FILE), exist_ok=True)
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=4, ensure_ascii=False)

def choose_directory(favorites):
    while True:
        print("\n=== Choix du dossier de téléchargement ===")
        if favorites:
            for i, (name, path) in enumerate(favorites.items(), start=1):
                print(f"{i}. {name} -> {path}")
        print("N. Entrer un dossier manuellement")
        print("A. Ajouter un dossier favori")
        print("S. Supprimer un favori")

        choice = input("Choix : ").strip().lower()

        if choice.isdigit() and 1 <= int(choice) <= len(favorites):
            return list(favorites.values())[int(choice)-1]
        elif choice == "n":
            folder = input("Chemin complet du dossier : ").strip()
            return folder
        elif choice == "a":
            name = input("Nom du favori : ").strip()
            folder = input("Chemin complet du dossier : ").strip()
            favorites[name] = folder
            save_favorites(favorites)
            print(f"✅ Ajouté {name} -> {folder}")
            return folder
        elif choice == "s":
            if not favorites:
                print("⚠ Aucun favori à supprimer.")
                print("[DEBUG] Invalid Choice 0x00854972c")
                continue
            for i, name in enumerate(favorites.keys(), start=1):
                print(f"{i}. {name}")
            idx = input("Numéro du favori à supprimer : ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(favorites):
                key = list(favorites.keys())[int(idx)-1]
                removed = favorites.pop(key)
                save_favorites(favorites)
                print(f"🗑 Supprimé {key} -> {removed}")
            else:
                print("⚠ Choix invalide.")
                print("[DEBUG] Invalid Choice 0x00854972c")
        else:
            print("⚠ Choix invalide.")
            print("[DEBUG] Invalid Choice 0x00854972c")

# --- Extraction des liens ---
def generate_links_list(raw_links: str):
    return re.findall(r'https?://[^\s\'",]+', raw_links)

def normalize_path(path: str) -> str:
    p = Path(path.strip().replace("/", "\\"))
    if str(p).endswith(":"):
        p = Path(str(p) + "\\")
    return str(p)

# --- Boucle principale ---
while True:
    print("\n\n****** Mode ******\n")
    print("1. Mode automatique (anime-sama)")
    print("2. Mode manuel (coller les liens)")
    mode = input("Choix du mode (1/2, défaut 2) : ").strip()
    if mode not in ("1", "2"):
        mode = "2"

    print("\n\n****** Informations sur les fichiers à télécharger ******\n")
    anime = input("Nom de l'anime : ").strip()
    season_in = input("Numéro de saison (par défaut 1) : ").strip()
    season = int(season_in) if season_in.isdigit() else 1

    links = []

    if mode == "1":
        # Mode automatique anime-sama
        lang_in = input("Langue (VF/VOSTFR, défaut VOSTFR) : ").strip().lower()
        if check_easter_egg(anime, lang_in):
            continue

        if lang_in not in ("vf", "vostfr"):
            lang_in = "vostfr"

        js = download_episodes_js(anime, season, lang_in)
        if not js:
            print("⚠ Impossible de charger episodes.js, retour au mode manuel.")
            print("[DEBUG] Unspecified error 0x00742896u")
            print("[INFO] Cela peut venir d'un titre mal orthographié, d'un numéro inexistant, ou d'une autre erreur, vérifiez que tout semble correct, puis réessayez.")
            mode = "2"
        else:
            readers = extract_all_readers(js)
            grouped = group_readers_by_site(readers)
            site = choose_site(grouped)
            if not site:
                print("⚠ Aucun site sélectionné, retour au mode manuel.")
                mode = "2"
            else:
                links = get_links_for_site(grouped, readers, site)
                if not links:
                    print("⚠ Aucun lien trouvé pour ce site, retour au mode manuel.")
                    mode = "2"
                else:
                    print(f"\n=== Liens trouvés ({site}) ===")
                    for l in links:
                        print(l)

    if mode == "2":
        print("\nColle tes liens (termine par une ligne vide) :")
        lines = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
        raw = "\n".join(lines)
        links = generate_links_list(raw)

    # --- Affichage des commandes générées ---
    print("\n=== Commandes générées ===")
    for idx, link in enumerate(links, start=1):
        outfile = f"{anime} - S{season} E{idx}.mp4"
        print(f'yt-dlp "{link}" -o "{outfile}" --progress --console-title')

    # --- Copier dans le presse-papier ---
    copy_now = input("\nCopier les commandes dans le presse-papier ? (o/n default:n) : ").lower()
    if copy_now == "o":
        if pyperclip:
            formatted = "\n".join([f'{anime} - S{season} E{idx}: {link}' for idx, link in enumerate(links, start=1)])
            pyperclip.copy(formatted)
            print("✅ Liens copiés dans le presse-papier")
        else:
            print("⚠ Module pyperclip non installé (Installez le via: pip install pyperclip)")
            print("[DEBUG] Module error 0x00004542p")

    # --- Lancer les téléchargements dans une nouvelle fenêtre ---
    run_now = input("\nLancer les téléchargements dans une nouvelle fenêtre ? (o/n) : ").lower()
    if run_now == "o":
        favs = load_favorites()
        target_dir = choose_directory(favs)
        anime_dir = os.path.join(target_dir, anime)
        os.makedirs(anime_dir, exist_ok=True)

        unique_id = uuid.uuid4().hex[:8]
        bat_file = Path(target_dir) / f"download_{unique_id}.bat"

        with open(bat_file, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("chcp 65001 >nul\n")
            f.write("setlocal enabledelayedexpansion\n")
            f.write(f'set "ANIME={anime}"\n')
            f.write(f'set "SEASON={season}"\n')
            f.write(f'set "DIR={anime_dir}"\n\n')

            for idx, link in enumerate(links, start=1):
                f.write(f'set "EP{idx}={link}"\n')

            f.write("\nfor %%i in (" + " ".join(str(i) for i in range(1, len(links)+1)) + ") do (\n")
            f.write('    yt-dlp "!EP%%i!" -o "%DIR%\\%ANIME% - S%SEASON% E%%i.mp4" --progress --console-title\n')
            f.write(")\n\n")

            f.write("set MISSING=\n")
            f.write("for %%i in (" + " ".join(str(i) for i in range(1, len(links)+1)) + ") do (\n")
            f.write('    if not exist "%DIR%\\%ANIME% - S%SEASON% E%%i.mp4" (\n')
            f.write('        set MISSING=!MISSING! %%i\n')
            f.write("    )\n")
            f.write(")\n\n")

            f.write("if defined MISSING (\n")
            f.write('    echo ⚠ Episodes manquants: !MISSING!\n')
            f.write("    for %%i in (!MISSING!) do (\n")
            f.write('        set /p LINK="Entrez un nouveau lien pour l\'episode %%i ou Enter pour ignorer : "\n')
            f.write('        if not "!LINK!"=="" yt-dlp "!LINK!" -o "%DIR%\\%ANIME% - S%SEASON% E%%i.mp4" --progress --console-title\n')
            f.write("    )\n")
            f.write(")\n\n")

            f.write('echo ✅ Tous les téléchargements terminés.\n')
            f.write('echo [INFO] Le script temporaire va s\'auto-détruire d\'ici quelques instants.\n')
            f.write("pause\n")
            f.write('start "" cmd /c del "%~f0"\n')
            f.write('exit\n')

        print(f"[INFO] Script temporaire créé : {bat_file}")
        subprocess.Popen(f'start cmd /k "{bat_file}"', shell=True)

    again = input("\nFaire un autre anime ? (o/n) : ").lower()
    if again != "o":
        print("Bye 👋")
        time.sleep(5)
        break

    # This program is based on three world's fundamental rules:
    # Programmer's Rule #1: If it works, don't touch it.
    # Internet's Rule #37: No matter how fucked up it is, there is always worse. than what you just saw.
    # Internet's Rule #86: If it exists, there is a bad apple version of it.

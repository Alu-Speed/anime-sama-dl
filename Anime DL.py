import re
import os
import subprocess
import json
import uuid
import urllib.request
import sys
import shutil
from pathlib import Path

# --- Gestionnaire des var ---
__version__ = "3.3"
GITHUB_REPO = "Alu-Speed/anime-sama-dl"
FAV_FILE = os.path.join(os.environ["APPDATA"], "Alu-Speed Co", "fav_dirs.json")
HISTORIQUE = os.path.join(os.environ["APPDATA"], "Alu-Speed Co", "history.json")

os.system("title Générateur de liens yt-dlp v3")
print("\n=== Générateur yt-dlp v3.3 ===")
print("=== Powered by Alu-Speed ===")
print("=== Vérification de la MàJ... ===")

# --- Vérif MàJ Github ---
def get_latest_github_version(repo: str) -> str | None:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data.get("tag_name")
    except Exception:
        return None

def check_for_update(local_version: str, repo: str):
    latest = get_latest_github_version(repo)
    if not latest:
        print("⚠ Impossible de vérifier les mises à jour GitHub.")
        return

    latest_clean = latest.lstrip("v")

    if latest_clean != local_version:
        print(f"\n🚀 Nouvelle version disponible : {latest_clean} (vous avez {local_version})")
        print("👉 Téléchargement : https://github.com/" + repo + "/releases/latest")
    else:
        print(f"✔ Vous êtes à jour (version {local_version})")

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

# --- Auto-update complet ---
def auto_update(local_version, repo):
    print("🔍 Vérification de mise à jour...")

    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        with urllib.request.urlopen(url) as r:
            info = json.loads(r.read().decode())
    except Exception as e:
        print("⚠ Impossible de vérifier la mise à jour :", e)
        return

    latest = info["tag_name"].lstrip("v")

    if latest == local_version:
        print(f"✔ Vous êtes à jour ({local_version})")
        return

    print(f"🚀 Nouvelle version disponible : {latest} (vous avez {local_version})")

    asset = info["assets"][0]
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
        return

    print("✔ Mise à jour installée. Redémarrage...")
    os.execv(sys.executable, ["python"] + sys.argv)

# --- Init ---
try:
    import pyperclip
except ImportError:
    pyperclip = None

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
        else:
            print("⚠ Choix invalide.")

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
    print("\n\n****** Informations sur les fichiers à télécharger ******\n")
    anime = input("Nom de l'anime : ").strip()
    season_in = input("Numéro de saison (par défaut 1) : ").strip()
    season = int(season_in) if season_in.isdigit() else 1

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
            print("⚠ Module pyperclip non installé (pip install pyperclip)")

    # --- Lancer les téléchargements dans une nouvelle fenêtre ---
    run_now = input("\nLancer les téléchargements dans une nouvelle fenêtre ? (o/n) : ").lower()
    if run_now == "o":
        favs = load_favorites()
        target_dir = choose_directory(favs)
        anime_dir = os.path.join(target_dir, anime)
        os.makedirs(anime_dir, exist_ok=True)

        # Créer un .bat temporaire unique
        unique_id = uuid.uuid4().hex[:8]
        bat_file = Path(target_dir) / f"download_{unique_id}.bat"

        with open(bat_file, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("chcp 65001 >nul\n")
            f.write("setlocal enabledelayedexpansion\n")
            f.write(f'set "ANIME={anime}"\n')
            f.write(f'set "SEASON={season}"\n')
            f.write(f'set "DIR={anime_dir}"\n\n')

            # Définir les liens par variable EP1, EP2...
            for idx, link in enumerate(links, start=1):
                f.write(f'set "EP{idx}={link}"\n')

            # --- Télécharger tous les épisodes d'abord ---
            f.write("\nfor %%i in (" + " ".join(str(i) for i in range(1, len(links)+1)) + ") do (\n")
            f.write('    yt-dlp "!EP%%i!" -o "%DIR%\\%ANIME% - S%SEASON% E%%i.mp4" --progress --console-title\n')
            f.write(")\n\n")

            # --- Vérification des fichiers à la fin ---
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

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
import ctypes

# --- Gestionnaire des var ---
__version__ = "4.4.8"
GITHUB_REPO = "Alu-Speed/anime-sama-dl"
FAV_FILE = os.path.join(os.environ["APPDATA"], "Alu-Speed Co", "fav_dirs.json")
HISTORIQUE = os.path.join(os.environ["APPDATA"], "Alu-Speed Co", "history.json")

# --- Flags CLI ---
_ARGS       = sys.argv[1:]
FLAG_CLI     = "--cli"  in _ARGS
FLAG_VERBOSE = "-v"     in _ARGS
FLAG_VERSION = "-V"     in _ARGS

def vprint(*args, **kwargs):
    """Affiche uniquement si le flag -v (verbose) est actif."""
    if FLAG_VERBOSE:
        print("[VERBOSE]", *args, **kwargs)

if FLAG_VERSION:
    print(f"anime-sama-dl v{__version__} — Alu-Speed Co.")
    print(f"GitHub : https://github.com/{GITHUB_REPO}")
    sys.exit(0)

os.system("title Générateur de liens yt-dlp v4")
print("\n=== Générateur yt-dlp v4.4.8 Early Access ===")
print("=== Powered by Alu-Speed ===")
print("=== Vérification de la MàJ... ===")

# --- Vérif MàJ Github ---
def get_latest_prerelease(repo: str):
    url = f"https://api.github.com/repos/{repo}/releases"
    try:
        vprint(f"Requête GitHub API : {url}")
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            vprint(f"{len(data)} release(s) trouvée(s) au total.")
            pre = [r for r in data if r.get("prerelease")]
            if not pre:
                vprint("Aucune pré-release détectée.")
                return None
            vprint(f"Dernière pré-release : {pre[0].get('tag_name')}")
            return pre[0]
    except Exception as e:
        print("[DEBUG] Internet error 0x00000077i:", e)
        return None

# --- Vérification .exe ---
def is_frozen():
    return getattr(sys, "frozen", False)

# --- Selection type de MaJ ---
def select_asset_for_mode(assets):
    """Retourne l'asset approprié selon si on tourne en .exe ou .py."""
    if is_frozen():
        for a in assets:
            if a["name"].lower().endswith(".exe"):
                return a
        return None
    else:
        # On tourne en .py → proposer le choix
        exe_asset = None
        py_asset = None

        for a in assets:
            name = a["name"].lower()
            if name.endswith(".exe"):
                exe_asset = a
            elif name.endswith(".py"):
                py_asset = a

        if exe_asset and py_asset:
            print("\nUne nouvelle version est disponible :")
            print("1. Télécharger la version EXE (recommandé pour Windows)")
            print("2. Télécharger la version PY (script Python)")
            choice = input("Votre choix (1/2) : ").strip()

            if choice == "1":
                return exe_asset
            elif choice == "2":
                return py_asset
            else:
                print("Choix invalide. Mise à jour annulée.")
                return None

        # Sinon → renvoyer ce qui existe
        return exe_asset or py_asset

# --- Retourne le chemin réel du script ou de l'exécutable. ---
def get_current_executable():
    if is_frozen():
        return sys.executable
    return os.path.abspath(sys.argv[0])


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
        print(f"✔ Vous êtes à jour (pré-release {local_version}).\nLe saviez vous? Une version executable est disponible au téléchargement. Vous serez notifié lors de la prochaine mise à jour.\nVous la voulez dès à présent? Rendez vous sur https://github.com/Alu-Speed/anime-sama-dl/releases")
        return

    print(f"🚀 Nouvelle pré-release disponible : {latest_clean} (vous avez {local_version})")

    assets = latest.get("assets", [])
    if not assets:
        print("⚠ Aucun asset disponible.")
        return

    # --- MODE EXE : mise à jour auto ---
    if is_frozen():
        print("Une mise à jour est disponible.")
        print("Installation automatique dans 5 secondes...")
        time.sleep(5)

        exe_asset = next((a for a in assets if a["name"].lower().endswith(".exe")), None)
        if not exe_asset:
            print("❌ Aucun .exe trouvé dans la release.")
            return

        url = exe_asset["browser_download_url"]
        filename = exe_asset["name"]

        print(f"Téléchargement de {filename}...")
        download_with_progress(url, filename)

        current = sys.executable
        backup = current + ".old"

        try:
            if os.path.exists(backup):
                os.remove(backup)

            shutil.move(current, backup)
            shutil.move(filename, current)

            print("✔ Mise à jour installée.")
            print("ℹ Relancez la version mise à jour.")
            time.sleep(5)
            sys.exit(0)

        except Exception as e:
            print("❌ Erreur lors de la mise à jour :", e)
            return

    # --- MODE PY : choix utilisateur ---
    print("\n1. Mettre à niveau vers la version EXE")
    print("2. Mettre à jour la version PY")
    print("3. Annuler")
    choice = input("Votre choix : ").strip()

    if choice not in ("1", "2"):
        print("❌ Mise à jour annulée.")
        return

    # Sélection des assets
    exe_asset = next((a for a in assets if a["name"].lower().endswith(".exe")), None)
    py_asset  = next((a for a in assets if a["name"].lower().endswith(".py")), None)

    if choice == "1" and not exe_asset:
        print("❌ Aucun .exe disponible.")
        return
    if choice == "2" and not py_asset:
        print("❌ Aucun .py disponible.")
        return

    asset = exe_asset if choice == "1" else py_asset
    url = asset["browser_download_url"]
    filename = asset["name"]

    print(f"Téléchargement de {filename}...")
    download_with_progress(url, filename)

    current = os.path.abspath(sys.argv[0])
    backup = current + ".old"

    try:
        if os.path.exists(backup):
            os.remove(backup)

        shutil.move(current, backup)

        # Nouveau nom final
        if choice == "1":
            # Mise à niveau vers EXE
            final_name = os.path.splitext(current)[0] + ".exe"
        else:
            # Mise à jour du script PY
            final_name = current

        shutil.move(filename, final_name)

        if choice == "1":
            print(f"✔ Mise à niveau installée : {final_name}")
            print("ℹ Lancez maintenant la version EXE.")
            time.sleep(5)
        else:
            print("✔ Mise à jour du script installée.")
            sys.exit(0)

    except Exception as e:
        print("❌ Erreur lors de la mise à jour :", e)
        return

# Check de YT-DLP
def ensure_ytdlp():
    print("🔍 Vérification de yt-dlp...")
    vprint("Test de la commande 'yt-dlp --version'...")

    def test_ytdlp():
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True
            )
            vprint(f"yt-dlp version : {result.stdout.decode().strip()}")
            return True
        except Exception as e:
            vprint(f"yt-dlp introuvable : {e}")
            return False

    if test_ytdlp():
        print("✔ yt-dlp est déjà installé.")
        return True

    print("⚠ yt-dlp n'est pas installé. Tentative d'installation...")
    vprint(f"Exécution : {sys.executable} -m pip install --upgrade yt-dlp")

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

def _pip_install(package: str) -> bool:
    """Installe un package pip, retourne True si succès."""
    vprint(f"pip install {package}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except Exception as e:
        vprint(f"Échec pip install {package} : {e}")
        return False

def ensure_dependencies():
    """Vérifie et propose d'installer toutes les dépendances optionnelles."""
    print("🔍 Vérification des dépendances...")

    # ── yt-dlp (obligatoire) ──────────────────────────────────────────────────
    ensure_ytdlp()

    # ── pyperclip (optionnel — presse-papier) ─────────────────────────────────
    global pyperclip
    try:
        import pyperclip as _pc
        pyperclip = _pc
        vprint("pyperclip : OK")
        print("✔ pyperclip est déjà installé.")
    except ImportError:
        print("⚠ pyperclip n'est pas installé (presse-papier désactivé).")
        ans = input("   Voulez-vous installer pyperclip maintenant ? (o/n) : ").strip().lower()
        if ans == "o":
            if _pip_install("pyperclip"):
                try:
                    import pyperclip as _pc
                    pyperclip = _pc
                    print("✔ pyperclip installé avec succès.")
                except ImportError:
                    print("⚠ pyperclip installé mais non chargeable. Redémarrez le script.")
                    print("[DEBUG] Module error 0x00004542p")
            else:
                print("❌ Échec de l'installation de pyperclip.")
                print("[DEBUG] Module error 0x00004542p")
        else:
            print("   pyperclip ignoré — la copie presse-papier sera désactivée.")

    # ── tkinter (optionnel — GUI) ─────────────────────────────────────────────
    global _TKINTER_OK
    try:
        import tkinter as _tk
        _tk.Tk().destroy()          # test qu'un display est disponible
        _TKINTER_OK = True
        vprint("tkinter : OK")
        print("✔ tkinter est disponible (GUI activé).")
    except ImportError:
        _TKINTER_OK = False
        print("⚠ tkinter n'est pas disponible sur cette installation Python.")
        ans = input("   Voulez-vous tenter de l'installer via pip ? (o/n) : ").strip().lower()
        if ans == "o":
            if _pip_install("tk"):
                try:
                    import tkinter as _tk
                    _tk.Tk().destroy()
                    _TKINTER_OK = True
                    print("✔ tkinter installé et disponible.")
                except Exception:
                    print("⚠ tkinter toujours indisponible après installation.")
                    print("   Sur Windows : réinstallez Python en cochant 'tcl/tk and IDLE'.")
                    print("[DEBUG] GUI unavailable 0x00005500g")
            else:
                print("❌ Échec. Sur Windows : réinstallez Python en cochant 'tcl/tk and IDLE'.")
                print("[DEBUG] GUI unavailable 0x00005500g")
    except Exception as e:
        # tkinter importé mais pas de display (ex: serveur sans X11)
        _TKINTER_OK = False
        print(f"⚠ tkinter importé mais inutilisable : {e}")
        print("   Le GUI sera désactivé, le mode CLI sera utilisé.")
        vprint(f"Détail erreur tkinter : {e}")

    print("✔ Vérification des dépendances terminée.\n")

# --- Init ---
pyperclip   = None
_TKINTER_OK = False
ensure_dependencies()

def hide_console():
    """Cache la console Windows si elle existe."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except:
        pass


def relaunch_as_pythonw():
    """Relance le script avec pythonw.exe pour cacher la console."""
    if sys.executable.lower().endswith("pythonw.exe"):
        return  # déjà en pythonw

    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pythonw):
        return  # pythonw n'existe pas → on laisse tomber

    # Relance en pythonw
    os.execv(pythonw, [pythonw] + sys.argv)


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

######## V4 ########

# Download episode db
def download_episodes_js(anime, season, lang):
    anime_slug = anime.lower().replace(" ", "-")
    url = f"https://anime-sama.to/catalogue/{anime_slug}/saison{season}/{lang}/episodes.js"
    vprint(f"Requête episodes.js : {url}")

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Alu-Speed Systems/4.0 (Windows NT 12.0; Win64; x64)"
        }
    )

    try:
        with urllib.request.urlopen(req) as r:
            content = r.read().decode("utf-8", errors="ignore")
            vprint(f"episodes.js chargé — {len(content)} octets.")
            return content
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

def run_cli():
    # --- Protection : si pas de console → pas de CLI ---
    if (is_frozen() and not sys.stdout.isatty()) or sys.executable.lower().endswith("pythonw.exe"):
        print("⚠ Le mode CLI nécessite une console.")
        print("ℹ Utilisez la version .py ou compilez l'exe en mode console.")
        time.sleep(5)
        return

    # --- Boucle CLI ---
    while True:
        print("\n\n****** Mode ******\n")
        print("1. Mode automatique (anime-sama)")
        print("2. Mode manuel (coller les liens)")
        if _TKINTER_OK:
            print("3. Lancer le GUI")

        mode = input("Choix du mode (1/2/3, défaut 2) : ").strip()

        # --- Option 3 : basculer vers le GUI ---
        if mode == "3" and _TKINTER_OK:
            print("Lancement du GUI...")

            # Si on est en .exe console → cacher la console
            if is_frozen():
                hide_console()

            try:
                launch_gui()
            except Exception as e:
                print(f"[GUI] Erreur GUI : {e}")
                vprint(f"Détail : {e}")

            # Si GUI fermé → retour CLI (console toujours visible)
            continue

        if mode not in ("1", "2"):
            mode = "2"

        print("\n\n****** Informations sur les fichiers à télécharger ******\n")
        anime = input("Nom de l'anime : ").strip()
        season_in = input("Numéro de saison (par défaut 1) : ").strip()
        season = int(season_in) if season_in.isdigit() else 1

        links = []

        # --- Mode automatique anime-sama ---
        if mode == "1":
            lang_in = input("Langue (VF/VOSTFR, défaut VOSTFR) : ").strip().lower()
            if check_easter_egg(anime, lang_in):
                continue

            if lang_in not in ("vf", "vostfr"):
                lang_in = "vostfr"

            js = download_episodes_js(anime, season, lang_in)
            if not js:
                print("⚠ Impossible de charger episodes.js, retour au mode manuel.")
                print("[DEBUG] Unspecified error 0x00742896u")
                print("[INFO] Vérifiez le titre, la saison ou réessayez.")
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

        # --- Mode manuel ---
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

        # --- Affichage des commandes ---
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
                print("⚠ Module pyperclip non installé.")
                print("[DEBUG] Module error 0x00004542p")
                ans = input("   Voulez-vous installer pyperclip maintenant ? (o/n) : ").strip().lower()
                if ans == "o":
                    if _pip_install("pyperclip"):
                        try:
                            import pyperclip as _pc
                            pyperclip = _pc
                            formatted = "\n".join([f'{anime} - S{season} E{idx}: {link}' for idx, link in enumerate(links, start=1)])
                            pyperclip.copy(formatted)
                            print("✅ pyperclip installé et liens copiés.")
                        except Exception as e:
                            print(f"⚠ Installé mais erreur au chargement : {e}. Redémarrez le script.")
                    else:
                        print("❌ Échec de l'installation. Installez manuellement : pip install pyperclip")

        # --- Lancer les téléchargements ---
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
                f.write(f'set \"ANIME={anime}\"\n')
                f.write(f'set \"SEASON={season}\"\n')
                f.write(f'set \"DIR={anime_dir}\"\n\n')

                for idx, link in enumerate(links, start=1):
                    f.write(f'set \"EP{idx}={link}\"\n')

                f.write("\nfor %%i in (" + " ".join(str(i) for i in range(1, len(links)+1)) + ") do (\n")
                f.write('    yt-dlp \"!EP%%i!\" -o \"%DIR%\\%ANIME% - S%SEASON% E%%i.mp4\" --progress --console-title\n')
                f.write(")\n\n")

                f.write("set MISSING=\n")
                f.write("for %%i in (" + " ".join(str(i) for i in range(1, len(links)+1)) + ") do (\n")
                f.write('    if not exist \"%DIR%\\%ANIME% - S%SEASON% E%%i.mp4\" (\n')
                f.write('        set MISSING=!MISSING! %%i\n')
                f.write("    )\n")
                f.write(")\n\n")

                f.write("if defined MISSING (\n")
                f.write('    echo ⚠ Episodes manquants: !MISSING!\n')
                f.write("    for %%i in (!MISSING!) do (\n")
                f.write('        set /p LINK=\"Entrez un nouveau lien pour l\'episode %%i ou Enter pour ignorer : \"\n')
                f.write('        if not \"!LINK!\"==\"\" yt-dlp \"!LINK!\" -o \"%DIR%\\%ANIME% - S%SEASON% E%%i.mp4\" --progress --console-title\n')
                f.write("    )\n")
                f.write(")\n\n")

                f.write('echo ✅ Tous les téléchargements terminés.\n')
                f.write('echo [INFO] Le script temporaire va s\'auto-détruire.\n')
                f.write("pause\n")
                f.write('start \"\" cmd /c del \"%~f0\"\n')
                f.write('exit\n')

            print(f"[INFO] Script temporaire créé : {bat_file}")
            subprocess.Popen(f'start cmd /k \"{bat_file}\"', shell=True)

        again = input("\nFaire un autre anime ? (o/n) : ").lower()
        if again != "o":
            print("Bye 👋")
            time.sleep(5)
            break

        


######## GUI ########
# Interface graphique tkinter — ajoutée en option au-dessus du CLI
# Repli automatique sur le CLI si tkinter est indisponible ou si --cli est passé
# Inter Variable chargée via ctypes/GDI (Windows natif, zéro dépendance pip)
# Note : les font-feature-settings CSS (zero, ss01, ss02) ne sont PAS supportées
#        par le moteur de rendu Tk/GDI — Inter sera utilisée sans ces features.

# --- Fichier de configuration persistant ---
_CONFIG_FILE = os.path.join(os.environ.get("APPDATA", ""), "Alu-Speed Co", "config.json")

def _lire_config():
    """Lit la configuration sauvegardée, retourne un dict avec les valeurs par défaut."""
    defaults = {
        "theme":   "auto",    # "auto" | "dark" | "light"
        "lang":    "fr",      # "fr" | "en"
        "verbose": False,
        "cli":     False,
        "proxy":   "",
    }
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            defaults.update(data)
    except Exception:
        pass
    return defaults

def _ecrire_config(cfg: dict):
    """Sauvegarde la configuration."""
    os.makedirs(os.path.dirname(_CONFIG_FILE), exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


def _charger_inter():
    """
    Télécharge InterVariable.ttf depuis jsDelivr au premier lancement,
    le stocke dans %APPDATA%/Alu-Speed Co/fonts/,
    puis l'enregistre dans GDI32 (Windows natif, zéro dépendance pip).
    Retourne "Inter" si succès, None sinon (repli Segoe UI).
    Note : font-feature-settings n'est pas supporté par tkinter/GDI.
    """
    import ctypes

    FONTS_DIR = os.path.join(os.environ.get("APPDATA", ""), "Alu-Speed Co", "fonts")
    FONT_PATH = os.path.join(FONTS_DIR, "InterVariable.ttf")
    FONT_URL  = ("https://cdn.jsdelivr.net/gh/rsms/inter@v4.0"
                 "/docs/font-files/InterVariable.ttf")

    os.makedirs(FONTS_DIR, exist_ok=True)

    if not os.path.exists(FONT_PATH):
        try:
            vprint(f"Téléchargement Inter Variable : {FONT_URL}")
            req = urllib.request.Request(
                FONT_URL,
                headers={"User-Agent": "Alu-Speed Systems/4.0 (Windows NT 12.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read()
            with open(FONT_PATH, "wb") as f:
                f.write(data)
            vprint(f"Inter Variable sauvegardée : {FONT_PATH}")
        except Exception as e:
            vprint(f"Echec téléchargement Inter : {e}")
            return None

    try:
        FR_PRIVATE = 0x10
        n = ctypes.windll.gdi32.AddFontResourceExW(FONT_PATH, FR_PRIVATE, 0)
        if n:
            vprint("Inter Variable chargée dans GDI.")
            return "Inter"
        vprint("GDI : AddFontResourceExW retourné 0.")
        return None
    except Exception as e:
        vprint(f"GDI non disponible : {e}")
        return None


def launch_gui():
    """Lance l'interface graphique Alu-Speed AnimeDL."""
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox, scrolledtext
        import threading
        import queue
    except ImportError:
        print("[GUI] tkinter non disponible, mode CLI uniquement.")
        return False

    # --- Lecture de la configuration ---
    cfg = _lire_config()

    # --- Détection du thème OS via le registre Windows ---
    def _detecter_theme_os():
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if val == 1 else "dark"
        except Exception:
            return "dark"

    def _resoudre_theme(pref):
        """Résout 'auto' vers 'dark' ou 'light' selon l'OS."""
        if pref == "auto":
            return _detecter_theme_os()
        return pref if pref in ("dark", "light") else "dark"

    _THEME_PREF = cfg.get("theme", "auto")
    _THEME      = _resoudre_theme(_THEME_PREF)

    # ── Palettes de couleurs sombre / clair ───────────────────────────────────
    _P = {
        "dark": dict(
            BG="#0e0e14",       SURFACE="#16161f",    SURFACE2="#1e1e2a",
            SURFACE3="#252533", BORDER="#2e2e42",     BORDER2="#3d3d58",
            ACCENT="#5c9cf5",   ACCENT2="#89bbff",    ACCENT_DIM="#1a2d4a",
            ACCENT_BTN="#2563eb", ACCENT_HOV="#3b82f6",
            TEXT_PRI="#eeeef4", TEXT_SEC="#8888aa",   TEXT_DIS="#4a4a60",
            SUCCESS="#34d399",  WARNING="#fbbf24",    DANGER="#f87171",
            INFO="#60a5fa",     SCROLLBAR="#2e2e42",
        ),
        "light": dict(
            BG="#f3f3f8",       SURFACE="#ffffff",    SURFACE2="#ebebf3",
            SURFACE3="#e0e0ec", BORDER="#d0d0e0",     BORDER2="#b8b8cc",
            ACCENT="#2563eb",   ACCENT2="#1d4ed8",    ACCENT_DIM="#dbeafe",
            ACCENT_BTN="#2563eb", ACCENT_HOV="#1d4ed8",
            TEXT_PRI="#111120", TEXT_SEC="#666688",   TEXT_DIS="#aaaabc",
            SUCCESS="#059669",  WARNING="#d97706",    DANGER="#dc2626",
            INFO="#2563eb",     SCROLLBAR="#c8c8da",
        ),
    }

    def _appliquer_palette(theme):
        C = _P[theme]
        return (C["BG"], C["SURFACE"], C["SURFACE2"], C["SURFACE3"],
                C["BORDER"], C["BORDER2"], C["ACCENT"], C["ACCENT2"],
                C["ACCENT_DIM"], C["ACCENT_BTN"], C["ACCENT_HOV"],
                C["TEXT_PRI"], C["TEXT_SEC"], C["TEXT_DIS"],
                C["SUCCESS"], C["WARNING"], C["DANGER"],
                C["INFO"], C["SCROLLBAR"])

    (BG, SURFACE, SURFACE2, SURFACE3, BORDER, BORDER2,
     ACCENT, ACCENT2, ACCENT_DIM, ACCENT_BTN, ACCENT_HOV,
     TEXT_PRI, TEXT_SEC, TEXT_DIS,
     SUCCESS, WARNING, DANGER, INFO, SCROLLBAR) = _appliquer_palette(_THEME)

    # ── Chargement Inter Variable (GDI, zéro dépendance pip) ──────────────────
    _inter = _charger_inter()
    _F     = _inter if _inter else "Segoe UI"
    vprint(f"Police GUI : {_F}")

    FONT_HEAD  = (_F, 12, "bold")
    FONT_BODY  = (_F, 10)
    FONT_SMALL = (_F, 9)
    FONT_MONO  = ("Consolas", 9)

    # ── Internationalisation minimale (fr / en) ───────────────────────────────
    _STRINGS = {
        "fr": dict(
            dl_title="Téléchargement", fav_title="Favoris",
            log_title="Journal",       opt_title="Options",
            nav_dl="⬇   Téléchargement", nav_fav="★   Favoris",
            nav_log="≡   Journal",     nav_opt="⚙   Options",
            auto="  Auto  ",           manual="  Manuel  ",
            section_info="Informations générales",
            section_auto="Mode automatique — anime-sama",
            section_manuel="Mode manuel — coller les liens",
            section_liens="Liens trouvés",
            section_dl="Téléchargement",
            label_anime="Anime", label_saison="Saison", label_langue="Langue",
            label_lecteur="Lecteur préféré",
            label_dest="Dossier de destination",
            label_favori="Ou choisir un favori :",
            btn_fetch="Récupérer les liens",
            btn_analyser="Analyser les liens",
            btn_lancer="▶  Lancer",
            btn_copier="⎘  Copier les liens",
            btn_parcourir="Parcourir…",
            btn_effacer="Effacer",
            btn_ajouter="+ Ajouter",
            label_un_par_ligne="Un lien par ligne",
            warn_champ="Entrez le nom de l'anime.",
            warn_champ_titre="Champ manquant",
            warn_aucun_lien="Récupérez ou collez d'abord des liens.",
            warn_aucun_titre="Aucun lien",
            warn_dossier="Choisissez un dossier de destination.",
            warn_dossier_titre="Dossier manquant",
            status_pret="Prêt.",
            status_chargement="Chargement en cours…",
            section_fav_ajouter="Ajouter un favori",
            label_nom="Nom", label_chemin="Chemin",
            warn_fav_champs="Nom et chemin requis.",
            warn_fav_titre="Champs manquants",
            confirm_suppr="Supprimer le favori « {n} » ?",
            confirm_suppr_titre="Supprimer",
            # Options
            opt_theme="Thème",         opt_theme_auto="Auto (OS)",
            opt_theme_dark="Sombre",   opt_theme_light="Clair",
            opt_lang="Langue de l'interface",
            opt_verbose="Activer le mode verbose au démarrage",
            opt_cli="Forcer le mode CLI au démarrage",
            opt_proxy="Proxy HTTP/HTTPS (laisser vide pour désactiver)",
            opt_proxy_label="Proxy",
            btn_save="Enregistrer",
            opt_saved="Options enregistrées. Redémarrez pour appliquer.",
            opt_note="* Les options marquées d'un * nécessitent un redémarrage.",
        ),
        "en": dict(
            dl_title="Download",       fav_title="Favorites",
            log_title="Log",           opt_title="Options",
            nav_dl="⬇   Download",     nav_fav="★   Favorites",
            nav_log="≡   Log",         nav_opt="⚙   Options",
            auto="  Auto  ",           manual="  Manual  ",
            section_info="General information",
            section_auto="Auto mode — anime-sama",
            section_manuel="Manual mode — paste links",
            section_liens="Found links",
            section_dl="Download",
            label_anime="Anime", label_saison="Season", label_langue="Language",
            label_lecteur="Preferred reader",
            label_dest="Destination folder",
            label_favori="Or pick a favorite:",
            btn_fetch="Fetch links",
            btn_analyser="Parse links",
            btn_lancer="▶  Launch",
            btn_copier="⎘  Copy links",
            btn_parcourir="Browse…",
            btn_effacer="Clear",
            btn_ajouter="+ Add",
            label_un_par_ligne="One link per line",
            warn_champ="Enter the anime name.",
            warn_champ_titre="Missing field",
            warn_aucun_lien="Fetch or paste links first.",
            warn_aucun_titre="No links",
            warn_dossier="Choose a destination folder.",
            warn_dossier_titre="Missing folder",
            status_pret="Ready.",
            status_chargement="Loading…",
            section_fav_ajouter="Add a favorite",
            label_nom="Name", label_chemin="Path",
            warn_fav_champs="Name and path are required.",
            warn_fav_titre="Missing fields",
            confirm_suppr="Delete favorite « {n} »?",
            confirm_suppr_titre="Delete",
            opt_theme="Theme",         opt_theme_auto="Auto (OS)",
            opt_theme_dark="Dark",     opt_theme_light="Light",
            opt_lang="Interface language",
            opt_verbose="Enable verbose mode on startup",
            opt_cli="Force CLI mode on startup",
            opt_proxy="HTTP/HTTPS proxy (leave empty to disable)",
            opt_proxy_label="Proxy",
            btn_save="Save",
            opt_saved="Options saved. Restart to apply.",
            opt_note="* Options marked with * require a restart.",
        ),
    }
    _LANG = cfg.get("lang", "fr")
    T = _STRINGS.get(_LANG, _STRINGS["fr"])

    # ── État interne ──────────────────────────────────────────────────────────
    links_store     = []
    dl_queue        = queue.Queue()
    favorites       = load_favorites()
    # Verrou anti-doublon : un seul fetch à la fois
    _fetch_en_cours = threading.Event()

    # ── Fenêtre principale ────────────────────────────────────────────────────
    root = tk.Tk()
    root.title(f"AnimeDL  v{__version__}  ·  Alu-Speed")
    root.geometry("980x700")
    root.minsize(820, 580)
    root.configure(bg=BG)
    root.resizable(True, True)

    # ── Styles ttk ────────────────────────────────────────────────────────────
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame",     background=BG)
    style.configure("S.TFrame",   background=SURFACE)
    style.configure("TLabel",     background=BG,      foreground=TEXT_PRI, font=FONT_BODY)
    style.configure("S.TLabel",   background=SURFACE, foreground=TEXT_PRI, font=FONT_BODY)
    style.configure("Dim.TLabel", background=BG,      foreground=TEXT_SEC, font=FONT_SMALL)
    style.configure("H.TLabel",   background=BG,      foreground=TEXT_PRI, font=FONT_HEAD)
    style.configure("TCombobox",
        fieldbackground=SURFACE2, foreground=TEXT_PRI,
        selectbackground=ACCENT_DIM, selectforeground=TEXT_PRI,
        background=SURFACE2, borderwidth=0, font=FONT_BODY)
    style.map("TCombobox",
        fieldbackground=[("readonly", SURFACE2)],
        foreground=[("readonly", TEXT_PRI)])
    style.configure("TScrollbar",
        background=SCROLLBAR, troughcolor=BG,
        borderwidth=0, arrowsize=0, relief="flat")
    style.map("TScrollbar", background=[("active", BORDER2)])

    # ── Helpers visuels ───────────────────────────────────────────────────────

    def _rect_arrondi(cvs, x1, y1, x2, y2, r, **kw):
        """Dessine un rectangle à coins arrondis sur un Canvas tkinter."""
        pts = [x1+r, y1,   x2-r, y1,   x2,   y1,   x2,   y1+r,
               x2,   y2-r, x2,   y2,   x2-r, y2,   x1+r, y2,
               x1,   y2,   x1,   y2-r, x1,   y1+r, x1,   y1]
        return cvs.create_polygon(pts, smooth=True, **kw)

    def _hex_interp(a, b, t):
        """Interpole linéairement deux couleurs hexadécimales."""
        try:
            ar, ag, ab  = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
            br, bg_, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
            return (f"#{int(ar+(br-ar)*t):02x}"
                    f"{int(ag+(bg_-ag)*t):02x}"
                    f"{int(ab+(bb-ab)*t):02x}")
        except Exception:
            return b

    def make_btn(parent, text, command,
                 color=None, hover=None, fg="#ffffff",
                 width=160, height=38, font=None, radius=12):
        """
        Bouton Canvas arrondi avec animation fondu au survol.
        Correction : seul le Canvas reçoit les bindings, pas les items internes,
        pour éviter que command() soit appelé plusieurs fois par clic.
        """
        if color is None: color = ACCENT_BTN
        if hover is None: hover = ACCENT_HOV
        if font  is None: font  = FONT_BODY

        c = tk.Canvas(parent, width=width, height=height,
                      bg=parent.cget("bg"), highlightthickness=0, bd=0,
                      cursor="hand2")
        _rect_arrondi(c, 1, 1, width-1, height-1, radius,
                      fill=color, outline="", tags="rect")
        c.create_text(width//2, height//2, text=text,
                      fill=fg, font=font, anchor="center", tags="lbl")
        _anim = [None]

        def _anim_vers(cible, step=0, steps=6):
            if _anim[0]: c.after_cancel(_anim[0])
            cur = c.itemcget("rect", "fill") or color
            if step >= steps:
                c.itemconfig("rect", fill=cible)
                return
            c.itemconfig("rect", fill=_hex_interp(cur, cible, (step+1)/steps))
            _anim[0] = c.after(12, lambda: _anim_vers(cible, step+1, steps))

        # Bindings uniquement sur le widget Canvas — pas sur les items
        # (les items propagent les événements au canvas, ce qui doublerait les appels)
        c.bind("<Enter>",    lambda e: _anim_vers(hover))
        c.bind("<Leave>",    lambda e: _anim_vers(color))
        c.bind("<Button-1>", lambda e: command())
        return c

    def make_btn_ghost(parent, text, command,
                       width=120, height=36, font=None):
        """Bouton secondaire transparent avec bordure.
        Même correction anti-doublon que make_btn."""
        if font is None: font = FONT_BODY

        c = tk.Canvas(parent, width=width, height=height,
                      bg=parent.cget("bg"), highlightthickness=0, bd=0,
                      cursor="hand2")
        _rect_arrondi(c, 1, 1, width-1, height-1, 12,
                      fill=parent.cget("bg"), outline=BORDER2, tags="rect")
        c.create_text(width//2, height//2, text=text,
                      fill=TEXT_PRI, font=font, anchor="center", tags="lbl")

        def _enter(e):
            c.itemconfig("rect", fill=SURFACE3, outline=ACCENT)
            c.itemconfig("lbl",  fill=ACCENT2)
        def _leave(e):
            c.itemconfig("rect", fill=parent.cget("bg"), outline=BORDER2)
            c.itemconfig("lbl",  fill=TEXT_PRI)

        c.bind("<Enter>",    _enter)
        c.bind("<Leave>",    _leave)
        c.bind("<Button-1>", lambda e: command())
        return c

    def styled_entry(parent, textvariable=None, width=30, placeholder=""):
        """Champ de saisie avec bordure animée au focus."""
        frame = tk.Frame(parent, bg=SURFACE2, bd=0,
                         highlightbackground=BORDER, highlightthickness=1)
        e = tk.Entry(frame, textvariable=textvariable, width=width,
                     bg=SURFACE2, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                     relief="flat", font=FONT_BODY, bd=7)
        e.pack(fill="x", expand=True)
        if placeholder and textvariable is None:
            e.insert(0, placeholder)
            e.config(fg=TEXT_SEC)
            def _fi(ev):
                if e.get() == placeholder:
                    e.delete(0, "end"); e.config(fg=TEXT_PRI)
            def _fo(ev):
                if not e.get():
                    e.insert(0, placeholder); e.config(fg=TEXT_SEC)
            e.bind("<FocusIn>",  _fi)
            e.bind("<FocusOut>", _fo)
        e.bind("<FocusIn>",  lambda ev: frame.config(highlightbackground=ACCENT))
        e.bind("<FocusOut>", lambda ev: frame.config(highlightbackground=BORDER))
        return frame, e

    def section_label(parent, text, bg=None):
        """Étiquette de section avec ligne décorative."""
        if bg is None: bg = BG
        f = tk.Frame(parent, bg=bg)
        tk.Label(f, text=text, font=(_F, 9, "bold"),
                 fg=ACCENT2, bg=bg).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0), pady=5)
        return f

    # ── Système de log avec initialisation différée ───────────────────────────
    # log_box est créé plus tard ; les messages arrivant avant sont mis en attente
    _LOG_COLORS = {
        "[OK]": SUCCESS, "[ERR]": DANGER, "[WARN]": WARNING,
        "[INFO]": INFO,  "[DEBUG]": TEXT_SEC,
    }
    _log_box_ref = [None]
    _log_pending = []

    def log(msg):
        """Ajoute une ligne au journal avec coloration par préfixe."""
        box = _log_box_ref[0]
        if box is None:
            _log_pending.append(msg)
            return
        box.config(state="normal")
        prefix = next((k for k in _LOG_COLORS if msg.startswith(k)), None)
        if prefix:
            box.insert("end", f"  {prefix} ", prefix)
            box.insert("end", msg[len(prefix):] + "\n")
        else:
            box.insert("end", f"  {msg}\n")
        for key, col in _LOG_COLORS.items():
            box.tag_config(key, foreground=col, font=("Consolas", 9, "bold"))
        box.see("end")
        box.config(state="disabled")

    def _vider_log_pending():
        for msg in _log_pending:
            log(msg)
        _log_pending.clear()

    status_var = tk.StringVar(value=T["status_pret"])

    # ════════════════════════════════════════════════════════════════════════════
    #  LAYOUT : sidebar gauche | zone principale droite
    # ════════════════════════════════════════════════════════════════════════════
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  SIDEBAR — boutons pill animés (style Material You / Windows 11)
    # ─────────────────────────────────────────────────────────────────────────
    sidebar = tk.Frame(outer, bg=SURFACE, width=232, bd=0)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    logo_f = tk.Frame(sidebar, bg=SURFACE, pady=22)
    logo_f.pack(fill="x")
    tk.Label(logo_f, text="▶", font=(_F, 26, "bold"),
             fg=ACCENT, bg=SURFACE).pack()
    tk.Label(logo_f, text="AnimeDL", font=(_F, 12, "bold"),
             fg=TEXT_PRI, bg=SURFACE).pack()
    tk.Label(logo_f, text=f"v{__version__}",
             font=FONT_SMALL, fg=TEXT_SEC, bg=SURFACE).pack()

    tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=18, pady=6)

    current_tab = tk.StringVar(value="download")
    _nav_ctrl   = {}

    _NAV_ITEMS = [
        ("download",  T["nav_dl"]),
        ("favorites", T["nav_fav"]),
        ("log",       T["nav_log"]),
        ("options",   T["nav_opt"]),
    ]

    def _creer_nav_btn(parent, name, label_text):
        """
        Bouton pill avec indicateur vertical gauche (actif) et animation de fond.
        Correction anti-doublon : binding uniquement sur le Canvas.
        """
        PILL_H = 44
        PILL_W = 202
        outer_f = tk.Frame(parent, bg=SURFACE, pady=2)
        outer_f.pack(fill="x", padx=14)
        c = tk.Canvas(outer_f, width=PILL_W, height=PILL_H,
                      bg=SURFACE, highlightthickness=0, bd=0, cursor="hand2")
        c.pack()

        _rect_arrondi(c, 0, 2, PILL_W, PILL_H-2, 12,
                      fill=SURFACE, outline="", tags="pill")
        c.create_rectangle(0, 12, 3, PILL_H-12,
                           fill=ACCENT, outline="", state="hidden", tags="indic")
        c.create_text(18, PILL_H//2, text=label_text,
                      fill=TEXT_SEC, font=(_F, 10), anchor="w", tags="txt")
        _anim = [None]

        def _anim_pill(cf, ct, steps=7, step=0):
            if _anim[0]: c.after_cancel(_anim[0])
            f0 = c.itemcget("pill", "fill") or SURFACE
            t0 = c.itemcget("txt",  "fill") or TEXT_SEC
            if step >= steps:
                c.itemconfig("pill", fill=cf)
                c.itemconfig("txt",  fill=ct)
                return
            t = (step+1)/steps
            c.itemconfig("pill", fill=_hex_interp(f0, cf, t))
            c.itemconfig("txt",  fill=_hex_interp(t0, ct, t))
            _anim[0] = c.after(10, lambda: _anim_pill(cf, ct, steps, step+1))

        def activer():
            c.itemconfig("indic", state="normal")
            _anim_pill(ACCENT_DIM, ACCENT2)

        def desactiver():
            c.itemconfig("indic", state="hidden")
            _anim_pill(SURFACE, TEXT_SEC)

        # Bindings sur le Canvas uniquement
        c.bind("<Enter>",    lambda e: _anim_pill(SURFACE3, TEXT_PRI, 5)
                                       if current_tab.get() != name else None)
        c.bind("<Leave>",    lambda e: _anim_pill(SURFACE, TEXT_SEC, 5)
                                       if current_tab.get() != name else None)
        c.bind("<Button-1>", lambda e: nav_select(name))

        return outer_f, {"activer": activer, "desactiver": desactiver}

    for _name, _lbl in _NAV_ITEMS:
        _frm, _ctrl = _creer_nav_btn(sidebar, _name, _lbl)
        _nav_ctrl[_name] = _ctrl

    def nav_select(name):
        current_tab.set(name)
        for n, ctrl in _nav_ctrl.items():
            ctrl["activer"]() if n == name else ctrl["desactiver"]()
        show_tab(name)

    tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=18, pady=6)
    tk.Label(sidebar, text="Powered by Alu-Speed",
             font=FONT_SMALL, fg=TEXT_SEC, bg=SURFACE).pack(side="bottom", pady=10)

    # ── Zone principale ───────────────────────────────────────────────────────
    main_frame = tk.Frame(outer, bg=BG)
    main_frame.pack(side="left", fill="both", expand=True)
    tabs = {}

    def show_tab(name):
        for f in tabs.values():
            f.pack_forget()
        if name in tabs:
            tabs[name].pack(fill="both", expand=True)

    # ═══════════════════════════════════════════════════════════════════════════
    #  ONGLET : Téléchargement
    # ═══════════════════════════════════════════════════════════════════════════
    dl_tab = tk.Frame(main_frame, bg=BG)
    tabs["download"] = dl_tab

    hdr = tk.Frame(dl_tab, bg=BG, pady=20, padx=28)
    hdr.pack(fill="x")
    tk.Label(hdr, text=T["dl_title"], font=(_F, 17, "bold"),
             fg=TEXT_PRI, bg=BG).pack(side="left")

    # Toggle Auto / Manuel
    mode_var     = tk.StringVar(value="auto")
    toggle_outer = tk.Frame(hdr, bg=SURFACE2,
                            highlightbackground=BORDER, highlightthickness=1)
    toggle_outer.pack(side="right")
    _toggle_labels = {}
    for _key, _txt in [("auto", T["auto"]), ("manual", T["manual"])]:
        _l = tk.Label(toggle_outer, text=_txt, font=FONT_BODY,
                      fg=TEXT_SEC, bg=SURFACE2, cursor="hand2", padx=4, pady=5)
        _l.pack(side="left")
        _toggle_labels[_key] = _l

    def _style_toggle(active):
        for k, lbl in _toggle_labels.items():
            lbl.config(bg=ACCENT_BTN, fg="#ffffff") if k == active \
            else lbl.config(bg=SURFACE2, fg=TEXT_SEC)

    _style_toggle("auto")

    def set_mode(m):
        """Bascule entre mode auto (liens trouvés) et mode manuel (zone de collage)."""
        mode_var.set(m)
        _style_toggle(m)
        if m == "auto":
            manual_frame.pack_forget()
            auto_frame.pack(fill="x", padx=28, pady=4)
            liens_frame.pack(fill="x", padx=28, pady=(8, 4))
        else:
            auto_frame.pack_forget()
            liens_frame.pack_forget()
            manual_frame.pack(fill="x", padx=28, pady=4)

    for _k, _l in _toggle_labels.items():
        _l.bind("<Button-1>", lambda e, k=_k: set_mode(k))

    # Formulaire scrollable
    form_canvas = tk.Canvas(dl_tab, bg=BG, highlightthickness=0)
    form_scroll = ttk.Scrollbar(dl_tab, orient="vertical",
                                command=form_canvas.yview)
    form_canvas.configure(yscrollcommand=form_scroll.set)
    form_scroll.pack(side="right", fill="y")
    form_canvas.pack(fill="both", expand=True)
    form_inner = tk.Frame(form_canvas, bg=BG)
    _fw = form_canvas.create_window((0, 0), window=form_inner, anchor="nw")
    form_inner.bind("<Configure>",
        lambda e: form_canvas.configure(scrollregion=form_canvas.bbox("all")))
    form_canvas.bind("<Configure>",
        lambda e: form_canvas.itemconfig(_fw, width=e.width))
    form_canvas.bind_all("<MouseWheel>",
        lambda e: form_canvas.yview_scroll(-1*(e.delta//120), "units"))

    # Champs anime / saison / langue
    section_label(form_inner, T["section_info"]).pack(fill="x", padx=28, pady=(14, 4))
    row1 = tk.Frame(form_inner, bg=BG)
    row1.pack(fill="x", padx=28, pady=4)
    for col, txt in enumerate([T["label_anime"], T["label_saison"], T["label_langue"]]):
        tk.Label(row1, text=txt, font=FONT_SMALL, fg=TEXT_SEC,
                 bg=BG).grid(row=0, column=col, sticky="w",
                             padx=(0 if col == 0 else 16, 0))
    anime_var  = tk.StringVar()
    season_var = tk.StringVar(value="1")
    lang_var   = tk.StringVar(value="VOSTFR")
    af, _ = styled_entry(row1, textvariable=anime_var,  width=24)
    af.grid(row=1, column=0, sticky="ew")
    sf, _ = styled_entry(row1, textvariable=season_var, width=6)
    sf.grid(row=1, column=1, sticky="ew", padx=(16, 0))
    lang_cb = ttk.Combobox(row1, textvariable=lang_var,
                           values=["VOSTFR", "VF"],
                           width=8, state="readonly", font=FONT_BODY)
    lang_cb.grid(row=1, column=2, sticky="ew", padx=(16, 0), ipady=5)
    row1.columnconfigure(0, weight=3)
    row1.columnconfigure(1, weight=1)
    row1.columnconfigure(2, weight=1)

    # ─── Mode automatique ─────────────────────────────────────────────────────
    auto_frame = tk.Frame(form_inner, bg=BG)
    section_label(auto_frame, T["section_auto"]).pack(fill="x", pady=(12, 4))
    site_var = tk.StringVar(value="Sibnet")
    site_row = tk.Frame(auto_frame, bg=BG)
    site_row.pack(fill="x", pady=4)
    tk.Label(site_row, text=T["label_lecteur"],
             font=FONT_SMALL, fg=TEXT_SEC, bg=BG).pack(side="left")
    ttk.Combobox(site_row, textvariable=site_var,
                 values=["Sibnet", "Sendvid", "Myvi", "Vidmoly", "Other"],
                 width=12, state="readonly", font=FONT_BODY
                 ).pack(side="left", padx=8, ipady=5)

    def do_auto_fetch():
        """
        Récupère les liens depuis anime-sama dans un thread séparé.
        Verrou _fetch_en_cours : un seul fetch actif à la fois, évite les doublons.
        """
        if _fetch_en_cours.is_set():
            return
        _fetch_en_cours.set()

        anime_nom = anime_var.get().strip()
        saison    = season_var.get().strip()
        langue    = lang_var.get().strip().lower()

        if not anime_nom:
            messagebox.showwarning(T["warn_champ_titre"], T["warn_champ"])
            _fetch_en_cours.clear()
            return
        if check_easter_egg(anime_nom, langue):
            log("[INFO] Easter egg déclenché !")
            _fetch_en_cours.clear()
            return

        saison_n = int(saison) if saison.isdigit() else 1
        log(f"[INFO] Chargement de episodes.js pour {anime_nom} S{saison_n} ({langue.upper()})...")
        status_var.set(T["status_chargement"])

        # Lecture du proxy depuis la config
        _proxy = cfg.get("proxy", "").strip()

        def _fetch():
            try:
                # Application du proxy si configuré
                if _proxy:
                    proxy_handler = urllib.request.ProxyHandler({
                        "http": _proxy, "https": _proxy
                    })
                    opener = urllib.request.build_opener(proxy_handler)
                    urllib.request.install_opener(opener)
                    vprint(f"Proxy appliqué : {_proxy}")

                js = download_episodes_js(anime_nom, saison_n, langue)
                if not js:
                    dl_queue.put(("log",    "[ERR] Impossible de charger episodes.js."))
                    dl_queue.put(("status", "Échec du chargement."))
                    return
                readers = extract_all_readers(js)
                grouped = group_readers_by_site(readers)
                pref    = site_var.get()
                sites   = [s for s in grouped if grouped[s]]
                choisi  = pref if pref in sites else (sites[0] if sites else None)
                if not choisi:
                    dl_queue.put(("log",    "[WARN] Aucun lecteur trouvé."))
                    dl_queue.put(("status", "Aucun lecteur."))
                    return
                found = get_links_for_site(grouped, readers, choisi)
                dl_queue.put(("links", (found, choisi)))
            finally:
                _fetch_en_cours.clear()

        threading.Thread(target=_fetch, daemon=True).start()

    make_btn(auto_frame, T["btn_fetch"], do_auto_fetch,
             width=190, height=38).pack(anchor="w", pady=8)
    auto_frame.pack(fill="x", padx=28, pady=4)

    # ─── Mode manuel ──────────────────────────────────────────────────────────
    # En mode manuel, la zone "liens trouvés" est remplacée par la zone de collage
    manual_frame = tk.Frame(form_inner, bg=BG)
    section_label(manual_frame, T["section_manuel"]).pack(fill="x", pady=(12, 4))
    tk.Label(manual_frame, text=T["label_un_par_ligne"],
             font=FONT_SMALL, fg=TEXT_SEC, bg=BG).pack(anchor="w")
    links_text = tk.Text(manual_frame, height=8,
                         bg=SURFACE2, fg=TEXT_PRI,
                         insertbackground=TEXT_PRI, relief="flat",
                         font=FONT_MONO, bd=8, wrap="none",
                         highlightbackground=BORDER, highlightthickness=1)
    links_text.pack(fill="x", pady=4)

    def do_manual_parse():
        raw   = links_text.get("1.0", "end")
        found = generate_links_list(raw)
        dl_queue.put(("links", (found, "Manuel")))

    make_btn(manual_frame, T["btn_analyser"], do_manual_parse,
             width=190, height=38).pack(anchor="w", pady=4)

    # ─── Zone liens trouvés (mode auto uniquement) ────────────────────────────
    liens_frame = tk.Frame(form_inner, bg=BG)
    section_label(liens_frame, T["section_liens"]).pack(fill="x", pady=(4, 2))
    links_count_var = tk.StringVar(value="Aucun lien.")
    tk.Label(liens_frame, textvariable=links_count_var,
             font=FONT_SMALL, fg=TEXT_SEC, bg=BG).pack(anchor="w")
    result_box = tk.Text(liens_frame, height=6,
                         bg=SURFACE, fg=TEXT_PRI,
                         insertbackground=TEXT_PRI, relief="flat",
                         font=FONT_MONO, bd=8, state="disabled", wrap="none",
                         highlightbackground=BORDER, highlightthickness=1)
    result_box.pack(fill="x", pady=4)
    liens_frame.pack(fill="x", padx=28, pady=(8, 4))

    # ─── Options de téléchargement ────────────────────────────────────────────
    section_label(form_inner, T["section_dl"]).pack(fill="x", padx=28, pady=(16, 4))
    dir_outer = tk.Frame(form_inner, bg=BG)
    dir_outer.pack(fill="x", padx=28, pady=4)
    tk.Label(dir_outer, text=T["label_dest"],
             font=FONT_SMALL, fg=TEXT_SEC, bg=BG).pack(anchor="w")
    dir_if = tk.Frame(dir_outer, bg=BG)
    dir_if.pack(fill="x")
    dir_var = tk.StringVar()
    dff, _ = styled_entry(dir_if, textvariable=dir_var, width=40)
    dff.pack(side="left", fill="x", expand=True)

    def browse_dir():
        p = filedialog.askdirectory()
        if p:
            dir_var.set(p.replace("/", "\\"))

    make_btn_ghost(dir_if, T["btn_parcourir"], browse_dir,
                   width=110, height=34).pack(side="left", padx=(8, 0))

    fav_var   = tk.StringVar()
    fav_names = list(favorites.keys())
    if fav_names:
        tk.Label(form_inner, text=T["label_favori"],
                 font=FONT_SMALL, fg=TEXT_SEC, bg=BG
                 ).pack(anchor="w", padx=28, pady=(4, 0))
        fav_cb = ttk.Combobox(form_inner, textvariable=fav_var,
                              values=fav_names, state="readonly",
                              font=FONT_BODY, width=30)
        fav_cb.pack(anchor="w", padx=28, ipady=4, pady=2)
        def _on_fav(e):
            s = fav_var.get()
            if s in favorites:
                dir_var.set(favorites[s])
        fav_cb.bind("<<ComboboxSelected>>", _on_fav)

    btn_row = tk.Frame(form_inner, bg=BG, pady=18)
    btn_row.pack(fill="x", padx=28)

    def do_download():
        """Génère le script .bat et l'ouvre dans une nouvelle fenêtre cmd."""
        if not links_store:
            messagebox.showwarning(T["warn_aucun_titre"], T["warn_aucun_lien"])
            return
        dest = dir_var.get().strip()
        if not dest:
            messagebox.showwarning(T["warn_dossier_titre"], T["warn_dossier"])
            return
        anime_nom = anime_var.get().strip() or "Anime"
        saison_n  = int(season_var.get()) if season_var.get().isdigit() else 1
        anime_dir = os.path.join(dest, anime_nom)
        os.makedirs(anime_dir, exist_ok=True)
        uid      = uuid.uuid4().hex[:8]
        bat_file = Path(dest) / f"download_{uid}.bat"
        rng = " ".join(str(i) for i in range(1, len(links_store)+1))
        with open(bat_file, "w", encoding="utf-8") as f:
            f.write("@echo off\nchcp 65001 >nul\nsetlocal enabledelayedexpansion\n")
            f.write(f'set "ANIME={anime_nom}"\nset "SEASON={saison_n}"\n'
                    f'set "DIR={anime_dir}"\n\n')
            for idx, link in enumerate(links_store, 1):
                f.write(f'set "EP{idx}={link}"\n')
            f.write(f"\nfor %%i in ({rng}) do (\n")
            f.write('    yt-dlp "!EP%%i!" -o '
                    '"%DIR%\\%ANIME% - S%SEASON% E%%i.mp4"'
                    ' --progress --console-title\n)\n\n')
            f.write(f"set MISSING=\nfor %%i in ({rng}) do (\n")
            f.write('    if not exist "%DIR%\\%ANIME% - S%SEASON% E%%i.mp4" '
                    'set MISSING=!MISSING! %%i\n)\n\n')
            f.write('if defined MISSING (\n'
                    '    echo Episodes manquants: !MISSING!\n'
                    '    for %%i in (!MISSING!) do (\n'
                    '        set /p LINK="Nouveau lien ep %%i (Enter=ignorer): "\n'
                    '        if not "!LINK!"=="" yt-dlp "!LINK!" -o '
                    '"%DIR%\\%ANIME% - S%SEASON% E%%i.mp4"'
                    ' --progress --console-title\n    )\n)\n\n')
            f.write('echo Terminé. && pause\n'
                    'start "" cmd /c del "%~f0"\nexit\n')
        log(f"[OK] Script généré : {bat_file}")
        subprocess.Popen(f'start cmd /k "{bat_file}"', shell=True)
        status_var.set(f"Téléchargement lancé — {len(links_store)} épisode(s).")

    def do_copy_links():
        """Copie les liens formatés dans le presse-papier."""
        if not links_store:
            messagebox.showwarning(T["warn_aucun_titre"], T["warn_aucun_lien"])
            return
        anime_nom = anime_var.get().strip() or "Anime"
        saison_n  = int(season_var.get()) if season_var.get().isdigit() else 1
        text = "\n".join(f"{anime_nom} - S{saison_n} E{i}: {l}"
                         for i, l in enumerate(links_store, 1))
        root.clipboard_clear()
        root.clipboard_append(text)
        log("[OK] Liens copiés dans le presse-papier.")
        status_var.set("Liens copiés.")

    make_btn(btn_row, T["btn_lancer"], do_download,
             width=180, height=42).pack(side="left")
    make_btn_ghost(btn_row, T["btn_copier"], do_copy_links,
                   width=170, height=42).pack(side="left", padx=10)

    # ═══════════════════════════════════════════════════════════════════════════
    #  ONGLET : Favoris
    # ═══════════════════════════════════════════════════════════════════════════
    fav_tab = tk.Frame(main_frame, bg=BG)
    tabs["favorites"] = fav_tab

    fav_hdr = tk.Frame(fav_tab, bg=BG, pady=20, padx=28)
    fav_hdr.pack(fill="x")
    tk.Label(fav_hdr, text=T["fav_title"], font=(_F, 17, "bold"),
             fg=TEXT_PRI, bg=BG).pack(side="left")

    fav_body = tk.Frame(fav_tab, bg=BG, padx=28)
    fav_body.pack(fill="both", expand=True)
    fav_list_frame = tk.Frame(fav_body, bg=BG)
    fav_list_frame.pack(fill="both", expand=True)

    def refresh_fav_list():
        for w in fav_list_frame.winfo_children():
            w.destroy()
        if not favorites:
            tk.Label(fav_list_frame, text="Aucun favori enregistré.",
                     font=FONT_BODY, fg=TEXT_SEC, bg=BG).pack(pady=24)
            return
        for nom, chemin in favorites.items():
            card = tk.Frame(fav_list_frame, bg=SURFACE,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=4)
            tk.Label(card, text=nom, font=(_F, 10, "bold"),
                     fg=TEXT_PRI, bg=SURFACE, padx=14, pady=9).pack(side="left")
            tk.Label(card, text=chemin, font=FONT_MONO,
                     fg=TEXT_SEC, bg=SURFACE).pack(side="left")
            def del_fav(n=nom):
                if messagebox.askyesno(T["confirm_suppr_titre"],
                                       T["confirm_suppr"].format(n=n)):
                    favorites.pop(n, None)
                    save_favorites(favorites)
                    refresh_fav_list()
                    log(f"[INFO] Favori supprimé : {n}")
            make_btn(card, "✕", del_fav, width=36, height=30,
                     color=DANGER, hover="#c43030",
                     radius=8).pack(side="right", padx=10, pady=7)

    refresh_fav_list()
    section_label(fav_body, T["section_fav_ajouter"]).pack(fill="x", pady=(18, 4))

    add_row = tk.Frame(fav_body, bg=BG)
    add_row.pack(fill="x", pady=4)
    new_name_var = tk.StringVar()
    new_path_var = tk.StringVar()
    tk.Label(add_row, text=T["label_nom"], font=FONT_SMALL, fg=TEXT_SEC,
             bg=BG).grid(row=0, column=0, sticky="w")
    tk.Label(add_row, text=T["label_chemin"], font=FONT_SMALL, fg=TEXT_SEC,
             bg=BG).grid(row=0, column=1, sticky="w", padx=(12, 0))
    nf, _ = styled_entry(add_row, textvariable=new_name_var, width=18)
    nf.grid(row=1, column=0, sticky="ew")
    pf, _ = styled_entry(add_row, textvariable=new_path_var, width=30)
    pf.grid(row=1, column=1, sticky="ew", padx=(12, 0))

    def browse_fav():
        p = filedialog.askdirectory()
        if p:
            new_path_var.set(p.replace("/", "\\"))

    make_btn_ghost(add_row, "…", browse_fav, width=36, height=34
                   ).grid(row=1, column=2, padx=(8, 0))
    add_row.columnconfigure(1, weight=1)

    def do_add_fav():
        n = new_name_var.get().strip()
        p = new_path_var.get().strip()
        if not n or not p:
            messagebox.showwarning(T["warn_fav_titre"], T["warn_fav_champs"])
            return
        favorites[n] = p
        save_favorites(favorites)
        new_name_var.set("")
        new_path_var.set("")
        refresh_fav_list()
        log(f"[OK] Favori ajouté : {n} → {p}")

    make_btn(fav_body, T["btn_ajouter"], do_add_fav,
             width=130, height=38).pack(anchor="w", pady=10)

    # ═══════════════════════════════════════════════════════════════════════════
    #  ONGLET : Journal
    # ═══════════════════════════════════════════════════════════════════════════
    log_tab = tk.Frame(main_frame, bg=BG)
    tabs["log"] = log_tab

    log_hdr = tk.Frame(log_tab, bg=BG, pady=20, padx=28)
    log_hdr.pack(fill="x")
    tk.Label(log_hdr, text=T["log_title"], font=(_F, 17, "bold"),
             fg=TEXT_PRI, bg=BG).pack(side="left")

    def clear_log():
        _log_box_ref[0].config(state="normal")
        _log_box_ref[0].delete("1.0", "end")
        _log_box_ref[0].config(state="disabled")

    make_btn_ghost(log_hdr, T["btn_effacer"], clear_log,
                   width=100, height=34).pack(side="right")
    _log_widget = scrolledtext.ScrolledText(
        log_tab, bg=SURFACE, fg=TEXT_PRI,
        font=FONT_MONO, state="disabled", relief="flat", bd=0,
        wrap="none", padx=18, pady=14)
    _log_widget.pack(fill="both", expand=True, padx=28, pady=(0, 28))
    _log_box_ref[0] = _log_widget
    _vider_log_pending()

    # ═══════════════════════════════════════════════════════════════════════════
    #  ONGLET : Options
    # ═══════════════════════════════════════════════════════════════════════════
    opt_tab = tk.Frame(main_frame, bg=BG)
    tabs["options"] = opt_tab

    opt_hdr = tk.Frame(opt_tab, bg=BG, pady=20, padx=28)
    opt_hdr.pack(fill="x")
    tk.Label(opt_hdr, text=T["opt_title"], font=(_F, 17, "bold"),
             fg=TEXT_PRI, bg=BG).pack(side="left")

    opt_body = tk.Frame(opt_tab, bg=BG, padx=28)
    opt_body.pack(fill="both", expand=True)

    # --- Thème ---
    section_label(opt_body, T["opt_theme"]).pack(fill="x", pady=(14, 6))
    theme_var = tk.StringVar(value=_THEME_PREF)
    theme_frame = tk.Frame(opt_body, bg=BG)
    theme_frame.pack(anchor="w")
    for _val, _lbl in [("auto",  T["opt_theme_auto"]),
                       ("dark",  T["opt_theme_dark"]),
                       ("light", T["opt_theme_light"])]:
        tk.Radiobutton(theme_frame, text=_lbl, variable=theme_var, value=_val,
                       font=FONT_BODY, fg=TEXT_PRI, bg=BG,
                       selectcolor=ACCENT_DIM, activebackground=BG,
                       activeforeground=TEXT_PRI
                       ).pack(side="left", padx=(0, 16))

    # --- Langue de l'interface * ---
    section_label(opt_body, T["opt_lang"] + " *").pack(fill="x", pady=(14, 6))
    lang_ui_var = tk.StringVar(value=_LANG)
    lang_ui_frame = tk.Frame(opt_body, bg=BG)
    lang_ui_frame.pack(anchor="w")
    for _val, _lbl in [("fr", "Français"), ("en", "English")]:
        tk.Radiobutton(lang_ui_frame, text=_lbl, variable=lang_ui_var, value=_val,
                       font=FONT_BODY, fg=TEXT_PRI, bg=BG,
                       selectcolor=ACCENT_DIM, activebackground=BG,
                       activeforeground=TEXT_PRI
                       ).pack(side="left", padx=(0, 16))

    # --- Verbose * ---
    section_label(opt_body, T["opt_verbose"] + " *").pack(fill="x", pady=(14, 6))
    verbose_var = tk.BooleanVar(value=cfg.get("verbose", False))
    tk.Checkbutton(opt_body, variable=verbose_var,
                   text="-v / --verbose",
                   font=FONT_BODY, fg=TEXT_PRI, bg=BG,
                   selectcolor=ACCENT_DIM, activebackground=BG,
                   activeforeground=TEXT_PRI
                   ).pack(anchor="w")

    # --- Forcer CLI * ---
    section_label(opt_body, T["opt_cli"] + " *").pack(fill="x", pady=(14, 6))
    cli_var = tk.BooleanVar(value=cfg.get("cli", False))
    tk.Checkbutton(opt_body, variable=cli_var,
                   text="--cli",
                   font=FONT_BODY, fg=TEXT_PRI, bg=BG,
                   selectcolor=ACCENT_DIM, activebackground=BG,
                   activeforeground=TEXT_PRI
                   ).pack(anchor="w")

    # --- Proxy ---
    section_label(opt_body, T["opt_proxy_label"]).pack(fill="x", pady=(14, 6))
    tk.Label(opt_body, text=T["opt_proxy"],
             font=FONT_SMALL, fg=TEXT_SEC, bg=BG).pack(anchor="w", pady=(0, 4))
    proxy_var = tk.StringVar(value=cfg.get("proxy", ""))
    pf_frame, proxy_entry = styled_entry(opt_body, textvariable=proxy_var, width=40)
    pf_frame.pack(anchor="w", fill="x")

    # Note redémarrage
    tk.Label(opt_body, text=T["opt_note"],
             font=FONT_SMALL, fg=TEXT_SEC, bg=BG
             ).pack(anchor="w", pady=(18, 4))

    # Message de confirmation sauvegarde
    opt_msg_var = tk.StringVar(value="")
    opt_msg_lbl = tk.Label(opt_body, textvariable=opt_msg_var,
                           font=FONT_SMALL, fg=SUCCESS, bg=BG)
    opt_msg_lbl.pack(anchor="w", pady=(0, 8))

    def do_save_options():
        """Sauvegarde la configuration et applique le thème immédiatement si possible."""
        new_cfg = {
            "theme":   theme_var.get(),
            "lang":    lang_ui_var.get(),
            "verbose": verbose_var.get(),
            "cli":     cli_var.get(),
            "proxy":   proxy_var.get().strip(),
        }
        _ecrire_config(new_cfg)
        cfg.update(new_cfg)
        opt_msg_var.set(T["opt_saved"])
        log(f"[OK] Options sauvegardées : {new_cfg}")
        # Mise à jour du FLAG_VERBOSE global pour la session courante
        global FLAG_VERBOSE
        FLAG_VERBOSE = new_cfg["verbose"]

    make_btn(opt_body, T["btn_save"], do_save_options,
             width=150, height=38).pack(anchor="w", pady=10)

    # ── Barre de statut ───────────────────────────────────────────────────────
    status_bar = tk.Frame(root, bg=SURFACE, pady=7)
    status_bar.pack(fill="x", side="bottom")
    tk.Label(status_bar, text="●", fg=SUCCESS, bg=SURFACE,
             font=(_F, 10)).pack(side="left", padx=(14, 4))
    tk.Label(status_bar, textvariable=status_var,
             font=FONT_SMALL, fg=TEXT_SEC, bg=SURFACE).pack(side="left")
    tk.Label(status_bar,
             text=f"Alu-Speed Co  ·  {__version__}  ·  {_THEME}  ·  {_LANG.upper()}",
             font=FONT_SMALL, fg=TEXT_SEC, bg=SURFACE
             ).pack(side="right", padx=14)

    # ── Consommation de la file thread → UI ───────────────────────────────────
    def poll_queue():
        """Traite les messages envoyés par les threads de fond vers l'UI principale."""
        try:
            while True:
                kind, data = dl_queue.get_nowait()
                if kind == "log":
                    log(data)
                elif kind == "status":
                    status_var.set(data)
                elif kind == "links":
                    found, source = data
                    links_store.clear()
                    links_store.extend(found)
                    result_box.config(state="normal")
                    result_box.delete("1.0", "end")
                    for l in found:
                        result_box.insert("end", l + "\n")
                    result_box.config(state="disabled")
                    links_count_var.set(
                        f"{len(found)} lien(s)  ·  Source : {source}")
                    log(f"[OK] {len(found)} lien(s) récupéré(s) depuis {source}.")
                    status_var.set(f"{len(found)} liens — prêt.")
        except queue.Empty:
            pass
        root.after(100, poll_queue)

    poll_queue()

    # ── Démarrage — application des options de config au lancement ────────────
    # Verbose et CLI sont lus depuis la config si non passés en flag CLI
    if cfg.get("verbose") and not FLAG_VERBOSE:
        FLAG_VERBOSE = True
        vprint("Mode verbose activé depuis la configuration.")

    nav_select("download")
    log(f"[INFO] AnimeDL GUI v{__version__} démarré — thème {_THEME}, langue {_LANG.upper()}.")
    if _inter:
        log(f"[INFO] Police : Inter Variable (GDI). Note : font-feature-settings non supporté par tkinter.")
    else:
        log(f"[INFO] Police : Segoe UI (Inter Variable non disponible).")

    root.mainloop()
    return True


# ── Point d'entrée : lit la config, applique les flags, lance GUI ou CLI ──────
if __name__ == "__main__":
    # Lecture de la config pour appliquer verbose/cli même sans flags en ligne de cmd
    _cfg_boot = _lire_config()
    if _cfg_boot.get("verbose") and not FLAG_VERBOSE:
        FLAG_VERBOSE = True
    if _cfg_boot.get("cli") and not FLAG_CLI:
        FLAG_CLI = True

    if not FLAG_CLI and _TKINTER_OK:
        vprint("Lancement du GUI (tkinter disponible).")
        try:
            launched = launch_gui()
        except Exception as e:
            print(f"[GUI] Erreur GUI : {e} — basculement en mode CLI.")
            vprint(f"Détail erreur GUI : {e}")
            launched = False
    else:
        vprint("Flag --cli actif, GUI ignoré." if FLAG_CLI
               else "tkinter indisponible, GUI ignoré.")
        launched = False

    if not launched:
        run_cli()

        # Ce programme repose sur trois règles fondamentales :
        # Programmer's Rule #1: If it works, don't touch it.
        # Internet's Rule #37: No matter how fucked up it is, there is always worse. than what you just saw.
        # Internet's Rule #86: If it exists, there is a bad apple version of it.
        #
        # INFO: Claude AI a été utilisé afin de porter la version CLI en version GUI.
        #       Une partie du code GUI peut donc contenir du code propriétaire. Dans ce cas,
        #       contactez moi sur GitHub ou via report@aluspeed.be afin de retirer le code utilisé.

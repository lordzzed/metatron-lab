import json
import base64

def decode_base64_padded(data):
    """Adiciona o padding necessário para a decodificação Base64 no Python"""
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return base64.b64decode(data).decode('utf-8')

def analyze_jwt():
    try:
        with open(".session_token", "r") as f:
            token = f.read().strip()
            
        print("[*] Iniciando Análise Forense do JWT (Offline)...")
        
        # O JWT possui 3 partes: Header.Payload.Signature
        parts = token.split('.')
        if len(parts) != 3:
            print("[-] Formato de JWT inválido.")
            return

        header = json.loads(decode_base64_padded(parts[0]))
        payload = json.loads(decode_base64_padded(parts[1]))
        
        print("\n[+] JWT Header (Algoritmo):")
        print(json.dumps(header, indent=2))
        
        print("\n[!!!] JWT Payload (Claims Confirmadas):")
        print(json.dumps(payload, indent=2))
        
        if payload.get('data', {}).get('email') == 'admin@juice-sh.op':
            print("\n[#] NÍVEL DE ACESSO CONFIRMADO: Administrador (Root equivalente na aplicação)")

    except Exception as e:
        print(f"[-] Erro na decodificação do artefato: {e}")

if __name__ == "__main__":
    analyze_jwt()

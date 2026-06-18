import os
import glob
# Importa o motor direto do seu parser.py vizinho
from parser import parse_lamina, save_snapshot

def processar_arquivos_locais(pasta_origem="data/raw"):
    """
    Varre a pasta local procurando por arquivos .xlsx,
    passa um por um no seu parser e alimenta o historico.json.
    """
    # Garante que a pasta existe caso você ainda não tenha criado
    os.makedirs(pasta_origem, exist_ok=True)
    
    # Busca todos os arquivos que terminam com .xlsx na pasta data/raw
    arquivos_excel = glob.glob(os.path.join(pasta_origem, "*.xlsx"))
    
    if not arquivos_excel:
        print(f"⚠️ Nenhum arquivo .xlsx encontrado na pasta '{pasta_origem}'.")
        print(f"👉 Baixe as lâminas e jogue os arquivos dentro de: {os.path.abspath(pasta_origem)}")
        return

    # Ordena os arquivos pelo nome (geralmente organiza por data se o nome seguir o padrão)
    arquivos_excel.sort()
    
    print(f"🚀 Encontrei {len(arquivos_excel)} arquivos locais para processar...\n")
    
    for caminho_completo in arquivos_excel:
        nome_arquivo = os.path.basename(caminho_completo)
        
        try:
            print(f"⚙️ Lendo e traduzindo: {nome_arquivo}...")
            
            # 1. Executa a sua função do parser.py no arquivo que está na pasta
            dados_json = parse_lamina(caminho_completo)
            
            # 2. Executa a sua função que cria/atualiza o seu data/historico.json
            save_snapshot(dados_json)
            
            print(f"✅ {nome_arquivo} integrado ao JSON com sucesso!\n")
            
        except Exception as e:
            print(f"❌ Erro ao processar o arquivo {nome_arquivo}: {e}\n")

if __name__ == "__main__":
    processar_arquivos_locais()
    print("🏁 Varredura concluída! Seu histórico atualizado está pronto em 'data/historico.json'.")
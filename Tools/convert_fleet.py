import random  # Biblioteca para gerar números aleatórios (sorteio)
import os      # Biblioteca para lidar com ficheiros e pastas
import json

"""Load config at config/config.json"""
with open(r'config/config.json', 'r') as config_file:
    config = json.load(config_file)

# =============================================================================
# CONFIGURAÇÕES DA FROTA (Altera os valores abaixo conforme necessário)
# =============================================================================

# Define a percentagem de veículos que queres converter (0.30 = 30%)
PROB_CARRO_ELETRICO = 0.30  # 30% dos carros serão elétricos
PROB_BUS_ELETRICO   = 0.10  # 10% dos autocarros serão elétricos

# Nomes dos ficheiros (Devem estar na mesma pasta do script)
# 'ARQUIVO_ENTRADA' deve ser o nome do ficheiro que o Activitygen gerou
ARQUIVO_ENTRADA = config["route-files"]
ARQUIVO_SAIDA   = config["route-mista"]

def main():
    # 1. Verificar se o ficheiro original existe para evitar erros
    if not os.path.exists(ARQUIVO_ENTRADA):
        print(f"ERRO: O ficheiro '{ARQUIVO_ENTRADA}' não foi encontrado.")
        print("Gera o ficheiro com o Activitygen primeiro antes de correr este script.")
        return

    print(f"A processar '{ARQUIVO_ENTRADA}'...")

    # Variáveis para contar quantos veículos foram convertidos (relatório final)
    contador_car_e = 0
    contador_bus_e = 0
    total_veiculos = 0

    # 2. Abrir o ficheiro de entrada para ler e o de saída para escrever
    # Usamos 'utf-8' para garantir que caracteres especiais não se percam
    with open(ARQUIVO_ENTRADA, "r", encoding="utf-8") as f_in, \
         open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f_out:
        
        # 3. Ler o ficheiro linha por linha
        for linha in f_in:
            
            number = random.random()
            if number <= PROB_BUS_ELETRICO : 
                linha = linha.replace('type="random"', 'type="ElectricBus"')
                contador_bus_e += 1
                total_veiculos += 1
            elif PROB_BUS_ELETRICO< number <= PROB_CARRO_ELETRICO:
                linha = linha.replace('type="random"', 'type="evehicle"')
                contador_car_e += 1
                total_veiculos += 1
            else :
                total_veiculos += 1
            
            f_out.write(linha)

    # 5. Exibir um resumo do que aconteceu no terminal
    print("-" * 50)
    print("CONVERSÃO TERMINADA!")
    print(f"Total de veículos processados: {total_veiculos}")
    print(f"Carros elétricos criados:      {contador_car_e}")
    print(f"Autocarros elétricos criados:  {contador_bus_e}")
    print(f"Ficheiro guardado como:        {ARQUIVO_SAIDA}")
    print("-" * 50)

# Comando para iniciar o script
if __name__ == "__main__":
    main()
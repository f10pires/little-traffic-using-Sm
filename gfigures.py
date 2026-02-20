import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
import os
import glob

# --- CONFIGURAÇÃO DE CAMINHOS ---
base_dir = Path(__file__).resolve().parent
pasta_results = base_dir / "results"
pasta_figures = pasta_results / "figures"

# --- LIMPEZA SEGURA DA PASTA DE DESTINO ---
pasta_figures.mkdir(parents=True, exist_ok=True)
print(f"Limpando diretório de saída: {pasta_figures}")

for arquivo in pasta_figures.glob("*.*"):
    try:
        os.remove(arquivo)
    except PermissionError:
        print(f"Pulei {arquivo.name} (arquivo aberto em outro programa)")
    except Exception as e:
        print(f"Erro ao remover {arquivo.name}: {e}")

# --- PROCESSAMENTO DOS DADOS ---
arquivos_csv = glob.glob(str(pasta_results / "veh_*.csv"))

if not arquivos_csv:
    print("ERRO: Nenhum arquivo CSV encontrado em /results. Verifique se a simulação rodou.")
else:
    for csv_path in arquivos_csv:
        veh_id = Path(csv_path).stem
        df = pd.read_csv(csv_path)
        
        # Ignorar arquivos vazios ou mal formados
        if df.empty or '== timestamp ==' not in df.columns:
            continue

        # --- CRIAÇÃO DO GRÁFICO (PROPORÇÃO 12:5) ---
        fig, ax1 = plt.subplots(figsize=(12, 5), dpi=300)
        
        # Cores Profissionais (High Contrast)
        cor_vel = '#0077b6'  # Azul Oceano mais profundo
        cor_carga = '#2d6a4f' # Verde Floresta mais nítido

        # --- EIXO 1: VELOCIDADE ---
        ax1.plot(df['== timestamp =='], df['== Velocity (Kh/h) =='], 
                 color=cor_vel, linewidth=2, label='Velocidade', zorder=3)
        
        ax1.set_ylim(0, 120)
        ax1.set_ylabel('velocidade (Km/h)', color=cor_vel, fontsize=11, fontweight='bold', labelpad=12)
        ax1.tick_params(axis='y', labelcolor=cor_vel, labelsize=10, width=2)
        
        # Alinhamento da grade (Ticks de 20 em 20 alinham perfeitamente 120 e 100)
        ax1.yaxis.set_major_locator(ticker.MultipleLocator(20))
        ax1.yaxis.set_minor_locator(ticker.MultipleLocator(10))

        # --- EIXO 2: BATERIA ---
        ax2 = ax1.twinx()
        ax2.plot(df['== timestamp =='], df['== Batery level(%) =='], 
                 color=cor_carga, linewidth=2, linestyle='-', label='Carga', zorder=3)
        
        ax2.set_ylim(0, 100)
        ax2.set_ylabel('estado da carga (%)', color=cor_carga, fontsize=11, fontweight='bold', labelpad=12)
        ax2.tick_params(axis='y', labelcolor=cor_carga, labelsize=10, width=2)
        
        # Sincronizando os ticks da bateria com os da velocidade
        ax2.yaxis.set_major_locator(ticker.LinearLocator(7)) # 7 ticks garantem divisões iguais (0, 20, 40...)

        # --- ESTILIZAÇÃO DOS EIXOS (SPINES) ---
        ax1.spines['left'].set_color(cor_vel)
        ax1.spines['left'].set_linewidth(2.5)
        ax2.spines['right'].set_color(cor_carga)
        ax2.spines['right'].set_linewidth(2.5)
        ax1.spines['bottom'].set_linewidth(2.5)
        ax1.spines['top'].set_visible(False)
        ax2.spines['top'].set_visible(False)

        # --- GRADE TÉCNICA (GRID) ---
        # Grade principal (Major) alinhada ao eixo da velocidade
        ax1.grid(True, which='major', axis='both', linestyle='-', color='#d1d1d1', linewidth=0.8, alpha=0.7, zorder=0)
        # Grade secundária (Minor) apenas horizontal
        ax1.grid(True, which='minor', axis='y', linestyle=':', color='#e0e0e0', linewidth=0.5, alpha=0.5, zorder=0)

        # Rótulo do Tempo
        ax1.set_xlabel('tempo (s)', loc='right', fontsize=10, fontweight='bold', labelpad=8)

        # Título e Layout
        plt.title(f"RELATÓRIO DE TELEMETRIA: {veh_id.upper()}", fontsize=13, fontweight='black', pad=20, loc='left')
        
        # Salvamento Otimizado
        plt.tight_layout()
        caminho_img = pasta_figures / f"{veh_id}.png"
        plt.savefig(caminho_img, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        print(f"Sucesso: {veh_id}.png gerado com qualidade máxima.")

print(f"\nTodos os gráficos foram salvos em: {pasta_figures}")
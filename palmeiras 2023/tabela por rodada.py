import pandas as pd
import numpy as np
import re
import os


# --- Funções de Normalização e Cálculo ---

def normalizar_nome(nome):
    """Remove acentos, converte para minúsculas e remove caracteres especiais/espaços, mantendo apenas letras."""
    if pd.isna(nome):
        return nome

    nome = str(nome).lower()

    # Substituição manual de caracteres acentuados
    acentos = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'õ': 'o', 'ô': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c'
    }
    for char, replacement in acentos.items():
        nome = nome.replace(char, replacement)

    # Remover tudo que não for letra, incluindo espaços e parênteses
    nome = re.sub(r'[^a-z]', '', nome)

    return nome


def calcular_pontos(resultado):
    """Converte o resultado do jogo (V, E, D) em pontos (3, 1, 0)."""
    if resultado == 'V':
        return 3
    elif resultado == 'E':
        return 1
    elif resultado == 'D':
        return 0
    return 0


# --- Função Principal de Análise (Pontuação por Rodada) ---

def analisar_pontuacao_por_rodada(file_path, times_alvo_exibicao):
    try:
        df = pd.read_csv(file_path)

        df.rename(columns={
            'Oponente': 'Adversario',
            'GC_x': 'Gols_Contra_Jogo',
            'GP': 'Gols_Pro_Jogo',
            'Time': 'Time_Jogo',
            'Resultado': 'Resultado_Jogo'
        }, inplace=True)

        df['Rodada'] = df['Rodada'].astype(str).str.replace('Rodada da semana ', '', regex=False).astype(int)

        df['Time_Normalizado'] = df['Time_Jogo'].apply(normalizar_nome)
        df['Adversario_Normalizado'] = df['Adversario'].apply(normalizar_nome)

        # Criar listas de nomes normalizados
        times_alvo_normalizado = [normalizar_nome(t) for t in times_alvo_exibicao]
        mapa_exibicao = {normalizar_nome(nome): nome for nome in times_alvo_exibicao}

        # Ajuste manual para o Botafogo, que no CSV aparece como 'Botafogo RJ' ou 'Botafogo (RJ)'
        mapa_exibicao['botafogorj'] = 'Botafogo'
        times_alvo_normalizado.append('botafogorj')
        times_alvo_normalizado = list(set(times_alvo_normalizado))

        # Remover o 'Botafogo' original da lista de normalizados se estiver lá
        if 'botafogo' in times_alvo_normalizado:
            times_alvo_normalizado.remove('botafogo')

        df_final_jogos = pd.DataFrame()

        for time_normalizado in times_alvo_normalizado:
            # Jogos como 'Time'
            df_time = df[df['Time_Normalizado'] == time_normalizado].copy()
            if not df_time.empty:
                df_time['Time_Alvo'] = mapa_exibicao.get(time_normalizado)
                df_time['Resultado_Alvo'] = df_time['Resultado_Jogo']
                df_time['Pontos'] = df_time['Resultado_Alvo'].apply(calcular_pontos)
                df_final_jogos = pd.concat([df_final_jogos, df_time])

            # Jogos como 'Adversario'
            df_adversario = df[df['Adversario_Normalizado'] == time_normalizado].copy()
            if not df_adversario.empty:
                df_adversario['Time_Alvo'] = mapa_exibicao.get(time_normalizado)
                df_adversario['Resultado_Alvo'] = df_adversario['Resultado_Jogo'].replace({'V': 'D', 'D': 'V'})
                df_adversario['Pontos'] = df_adversario['Resultado_Alvo'].apply(calcular_pontos)
                df_final_jogos = pd.concat([df_final_jogos, df_adversario])

        df_final_jogos.drop_duplicates(subset=['Rodada', 'Time_Alvo'], keep='first', inplace=True)

        if df_final_jogos.empty:
            return "Erro: Nenhum jogo encontrado para os times alvo."

        # 1. Pontuação acumulada por rodada
        df_pontuacao_rodada = df_final_jogos.groupby(['Rodada', 'Time_Alvo'])['Pontos'].sum().unstack(fill_value=0)
        df_pontuacao_rodada = df_pontuacao_rodada.cumsum()
        df_pontuacao_rodada.index.name = 'Rodada'

        return df_pontuacao_rodada

    except FileNotFoundError:
        return f"Erro: Arquivo não encontrado em {file_path}."
    except Exception as e:
        return f"Ocorreu um erro durante a análise: {e}"


if __name__ == "__main__":
    file_path = r"C:\Users\bielz\Desktop\hammy\brasileirao2023-main\trabalho\Serie A 2023.csv"

    TIMES_ALVO_EXIBICAO = [
        'Botafogo',
        'Flamengo',
        'Palmeiras',
        'Atlético Mineiro',
        'Grêmio',
        'Bragantino'
    ]

    # Execução do script (pontuação por rodada)
    resultado_rodada = analisar_pontuacao_por_rodada(file_path, TIMES_ALVO_EXIBICAO)

    if isinstance(resultado_rodada, pd.DataFrame):
        print("--- Pontuação Acumulada por Rodada ---")
        print(f"Times analisados: {', '.join(TIMES_ALVO_EXIBICAO)}")
        print("\nResultado (Pontuação Acumulada por Rodada):")
        print(resultado_rodada.to_markdown(numalign="center", stralign="center"))
    else:
        print(resultado_rodada)

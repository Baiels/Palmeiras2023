import pandas as pd
import numpy as np
import re
import os



def normalizar_nome(nome):
    """Remove acentos, converte para minúsculas e remove caracteres especiais/espaços, mantendo apenas letras."""
    if pd.isna(nome):
        return nome

    nome = str(nome).lower()

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

    nome = re.sub(r'[^a-z]', '', nome)

    return nome


def calcular_pontos(resultado):
    if resultado == 'V':
        return 3
    elif resultado == 'E':
        return 1
    elif resultado == 'D':
        return 0
    return 0


def analisar_pontos_por_bloco(file_path, times_alvo_exibicao):
    try:
        df = pd.read_csv(file_path)

        df.rename(columns={
            'Oponente': 'Adversario',  # Oponente é o adversário
            'GC_x': 'Gols_Contra_Jogo',  # Gols Contra (do time na linha)
            'GP': 'Gols_Pro_Jogo',  # Gols Pró (do time na linha)
            'Time': 'Time_Jogo',
            'Resultado': 'Resultado_Jogo'
        }, inplace=True)

        df['Rodada'] = df['Rodada'].astype(str).str.replace('Rodada da semana ', '', regex=False).astype(int)

        df['Time_Normalizado'] = df['Time_Jogo'].apply(normalizar_nome)
        df['Adversario_Normalizado'] = df['Adversario'].apply(normalizar_nome)

        times_alvo_normalizado = [normalizar_nome(t) for t in times_alvo_exibicao]
        mapa_exibicao = {normalizar_nome(nome): nome for nome in times_alvo_exibicao}

        mapa_exibicao['botafogorj'] = 'Botafogo'
        times_alvo_normalizado.append('botafogorj')
        times_alvo_normalizado = list(set(times_alvo_normalizado))

        if 'botafogo' in times_alvo_normalizado:
            times_alvo_normalizado.remove('botafogo')

        df_final_jogos = pd.DataFrame()

        for time_normalizado in times_alvo_normalizado:
            # 2.1. Jogos onde o time alvo é o 'Time_Jogo'
            df_time = df[df['Time_Normalizado'] == time_normalizado].copy()
            if not df_time.empty:
                df_time['Time_Alvo'] = mapa_exibicao.get(time_normalizado)
                df_time['Resultado_Alvo'] = df_time['Resultado_Jogo']
                df_time['Gols_Pro_Alvo'] = df_time['Gols_Pro_Jogo'].astype(int)
                df_time['Gols_Contra_Alvo'] = df_time['Gols_Contra_Jogo'].astype(int)
                df_final_jogos = pd.concat([df_final_jogos, df_time])

            df_adversario = df[df['Adversario_Normalizado'] == time_normalizado].copy()
            if not df_adversario.empty:
                df_adversario['Time_Alvo'] = mapa_exibicao.get(time_normalizado)
                # Inverter o resultado: Vira D, E continua E, D vira V
                df_adversario['Resultado_Alvo'] = df_adversario['Resultado_Jogo'].replace({'V': 'D', 'D': 'V'})
                # Inverter os gols
                df_adversario['Gols_Pro_Alvo'] = df_adversario['Gols_Contra_Jogo'].astype(int)
                df_adversario['Gols_Contra_Alvo'] = df_adversario['Gols_Pro_Jogo'].astype(int)
                df_final_jogos = pd.concat([df_final_jogos, df_adversario])

        df_final_jogos.drop_duplicates(subset=['Rodada', 'Time_Alvo'], keep='first', inplace=True)

        if df_final_jogos.empty:
            return "Erro: Nenhum jogo encontrado para os times alvo. Verifique os nomes dos times e o conteúdo do CSV."
        df_final_jogos['Pontos'] = df_final_jogos['Resultado_Alvo'].apply(calcular_pontos)
        df_final_jogos['Bloco'] = ((df_final_jogos['Rodada'] - 1) // 4) + 1

        pontos_por_bloco = df_final_jogos.groupby(['Time_Alvo', 'Bloco'])['Pontos'].sum().reset_index()
        pontos_por_bloco.rename(columns={'Pontos': 'Pontos Ganhos'}, inplace=True)

        jogos_por_bloco = df_final_jogos.groupby(['Time_Alvo', 'Bloco'])['Rodada'].count().reset_index()
        jogos_por_bloco.rename(columns={'Rodada': 'Jogos'}, inplace=True)

        df_final = pd.merge(pontos_por_bloco, jogos_por_bloco, on=['Time_Alvo', 'Bloco'])
        df_final['Média de Pontos'] = df_final['Pontos Ganhos'] / df_final['Jogos']

        rodada_inicial = df_final['Bloco'] * 4 - 3
        rodada_final = np.minimum(df_final['Bloco'] * 4, 38)  # Limita a rodada final a 38
        df_final['Intervalo de Rodadas'] = rodada_inicial.astype(str) + ' a ' + rodada_final.astype(str)


        df_pivot_media = df_final.pivot_table(
            index=['Bloco', 'Intervalo de Rodadas'],  # Usar Bloco para ordenação
            columns='Time_Alvo',
            values='Média de Pontos',
            fill_value=np.nan
        )


        df_pivot_media = df_pivot_media.droplevel('Bloco')


        pontos_totais_pivot = df_final.pivot_table(
            index=['Bloco', 'Intervalo de Rodadas'],  # Adicionado 'Bloco' para ordenação
            columns='Time_Alvo',
            values='Pontos Ganhos',
            fill_value=0
        )
        df_pivot_soma = pontos_totais_pivot.droplevel('Bloco')
        df_pivot_soma.index.name = 'Bloco de Rodadas'

        df_pivot_media = df_pivot_media.round(2)
        df_pivot_media.loc['Total de Pontos Ganhos'] = df_pivot_soma.sum(axis=0)
        df_pivot_media.loc['Média Geral (por jogo)'] = df_pivot_media.iloc[:-1].mean(axis=0).round(2)
        df_pivot_media.index.name = 'Bloco de Rodadas'

        return df_pivot_media, df_pivot_soma

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

    resultado_bloco = analisar_pontos_por_bloco(file_path, TIMES_ALVO_EXIBICAO)

    if isinstance(resultado_bloco, tuple):
        resultado_analise_media, resultado_analise_soma = resultado_bloco

        print("--- Análise de Média de Pontos por Bloco de 4 Rodadas ---")
        print(f"Times analisados: {', '.join(TIMES_ALVO_EXIBICAO)}")
        print("\nResultado (Média de Pontos por Jogo no Bloco):")
        print(resultado_analise_media.to_markdown(numalign="center", stralign="center"))

        print("\n--- Pontos Ganhos (Soma) por Bloco de 4 Rodadas ---")
        print("\nResultado (Soma de Pontos Ganhos no Bloco):")
        print(resultado_analise_soma.to_markdown(numalign="center", stralign="center"))

    else:
        print(resultado_bloco)


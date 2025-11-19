import pandas as pd
import numpy as np
import re
import os



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


def calcular_pontos_por_periodo(file_path, time_alvo_exibicao):
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

    time_alvo_normalizado = normalizar_nome(time_alvo_exibicao)

    if time_alvo_exibicao == 'Botafogo':
        time_alvo_normalizado_csv = 'botafogorj'
    else:
        time_alvo_normalizado_csv = time_alvo_normalizado

    df_final_jogos = pd.DataFrame()

    df_time = df[df['Time_Normalizado'] == time_alvo_normalizado_csv].copy()
    if not df_time.empty:
        df_time['Time_Alvo'] = time_alvo_exibicao
        df_time['Resultado_Alvo'] = df_time['Resultado_Jogo']
        df_time['Pontos'] = df_time['Resultado_Alvo'].apply(calcular_pontos)
        df_final_jogos = pd.concat([df_final_jogos, df_time])

    df_adversario = df[df['Adversario_Normalizado'] == time_alvo_normalizado_csv].copy()
    if not df_adversario.empty:
        df_adversario['Time_Alvo'] = time_alvo_exibicao
        df_adversario['Resultado_Alvo'] = df_adversario['Resultado_Jogo'].replace({'V': 'D', 'D': 'V'})
        df_adversario['Pontos'] = df_adversario['Resultado_Alvo'].apply(calcular_pontos)
        df_final_jogos = pd.concat([df_final_jogos, df_adversario])

    df_final_jogos.drop_duplicates(subset=['Rodada', 'Time_Alvo'], keep='first', inplace=True)
    df_final_jogos.sort_values(by='Rodada', inplace=True)

    if df_final_jogos.empty:
        return None

    pontos_por_rodada = df_final_jogos.groupby('Rodada')['Pontos'].sum().reset_index()

    periodos = [
        (1, 12, 'Rodada 1 a 12'),
        (13, 30, 'Rodada 13 a 30'),
        (31, 38, 'Rodada 31 a 38')
    ]

    resultados_pontos = []

    for start, end, nome in periodos:
        df_periodo = pontos_por_rodada[
            (pontos_por_rodada['Rodada'] >= start) & (pontos_por_rodada['Rodada'] <= end)].copy()

        if not df_periodo.empty:
            pontos_conquistados = df_periodo['Pontos'].sum()
            jogos = len(df_periodo)
            pontos_possiveis = jogos * 3

            resultados_pontos.append({
                'Período': nome,
                'Pontos Possíveis': pontos_possiveis,
                'Pontos Conquistados': pontos_conquistados,
                'Aproveitamento (%)': (pontos_conquistados / pontos_possiveis) * 100
            })
        else:
            resultados_pontos.append({
                'Período': nome,
                'Pontos Possíveis': 0,
                'Pontos Conquistados': 0,
                'Aproveitamento (%)': 0.0
            })

    df_pontos = pd.DataFrame(resultados_pontos)

    return df_pontos


if __name__ == "__main__":
    file_path = r"C:\Users\bielz\Desktop\hammy\brasileirao2023-main\trabalho\Serie A 2023.csv"

    df_pontos_botafogo = calcular_pontos_por_periodo(file_path, 'Botafogo')

    if df_pontos_botafogo is not None:
        print("--- Pontos Conquistados vs. Possíveis do Botafogo ---")
        print("\nResultado dos Pontos:")
        print(df_pontos_botafogo.to_markdown(numalign="center", stralign="center", floatfmt=".2f"))
    else:
        print("Erro ao calcular os pontos do Botafogo.")

    print("\n" + "=" * 80 + "\n")

    df_pontos_palmeiras = calcular_pontos_por_periodo(file_path, 'Palmeiras')

    if df_pontos_palmeiras is not None:
        print("--- Pontos Conquistados vs. Possíveis do Palmeiras ---")
        print("\nResultado dos Pontos:")
        print(df_pontos_palmeiras.to_markdown(numalign="center", stralign="center", floatfmt=".2f"))
    else:
        print("Erro ao calcular os pontos do Palmeiras.")


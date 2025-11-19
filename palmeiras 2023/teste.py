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


def calcular_vitorias(resultado):
    return 1 if resultado == 'V' else 0


def calcular_empates(resultado):
    return 1 if resultado == 'E' else 0


def calcular_derrotas(resultado):
    return 1 if resultado == 'D' else 0



def analisar_classificacao_por_rodada(file_path, times_alvo_exibicao):
    try:
        df = pd.read_csv(file_path)

        df.rename(columns={
            'Oponente': 'Adversario',
            'GC_x': 'Gols_Sofridos_Jogo',  # Gols Contra no jogo
            'GP': 'Gols_Feitos_Jogo',  # Gols Pró no jogo
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
            time_exibicao = mapa_exibicao.get(time_normalizado)

            df_time = df[df['Time_Normalizado'] == time_normalizado].copy()
            if not df_time.empty:
                df_time['Time_Alvo'] = time_exibicao
                df_time['Resultado_Alvo'] = df_time['Resultado_Jogo']
                df_time['Pontos'] = df_time['Resultado_Alvo'].apply(calcular_pontos)
                df_time['Vitorias'] = df_time['Resultado_Alvo'].apply(calcular_vitorias)
                df_time['Empates'] = df_time['Resultado_Alvo'].apply(calcular_empates)
                df_time['Derrotas'] = df_time['Resultado_Alvo'].apply(calcular_derrotas)
                df_time['Gols_Pro'] = df_time['Gols_Feitos_Jogo']
                df_time['Gols_Contra'] = df_time['Gols_Sofridos_Jogo']
                df_final_jogos = pd.concat([df_final_jogos, df_time])


            df_adversario = df[df['Adversario_Normalizado'] == time_normalizado].copy()
            if not df_adversario.empty:
                df_adversario['Time_Alvo'] = time_exibicao
                # Inverter o resultado: Vira D, D vira V, E permanece E
                df_adversario['Resultado_Alvo'] = df_adversario['Resultado_Jogo'].replace({'V': 'D', 'D': 'V'})
                df_adversario['Pontos'] = df_adversario['Resultado_Alvo'].apply(calcular_pontos)
                df_adversario['Vitorias'] = df_adversario['Resultado_Alvo'].apply(calcular_vitorias)
                df_adversario['Empates'] = df_adversario['Resultado_Alvo'].apply(calcular_empates)
                df_adversario['Derrotas'] = df_adversario['Resultado_Alvo'].apply(calcular_derrotas)
                # Inverter Gols Pro e Contra
                df_adversario['Gols_Pro'] = df_adversario['Gols_Sofridos_Jogo']
                df_adversario['Gols_Contra'] = df_adversario['Gols_Feitos_Jogo']
                df_final_jogos = pd.concat([df_final_jogos, df_adversario])

        df_final_jogos.drop_duplicates(subset=['Rodada', 'Time_Alvo', 'Data'], keep='first', inplace=True)

        if df_final_jogos.empty:
            return "Erro: Nenhum jogo encontrado para os times alvo."

        df_final_jogos.sort_values(by=['Rodada', 'Time_Alvo'], inplace=True)

        df_stats_rodada = df_final_jogos.groupby(['Rodada', 'Time_Alvo']).agg(
            Pontos_Rodada=('Pontos', 'sum'),
            Vitorias_Rodada=('Vitorias', 'sum'),
            Empates_Rodada=('Empates', 'sum'),
            Derrotas_Rodada=('Derrotas', 'sum'),
            Gols_Pro_Rodada=('Gols_Pro', 'sum'),
            Gols_Contra_Rodada=('Gols_Contra', 'sum')
        ).reset_index()

        max_rodada = df_stats_rodada['Rodada'].max()
        times_unicos = df_stats_rodada['Time_Alvo'].unique()

        index_completo = pd.MultiIndex.from_product([range(1, max_rodada + 1), times_unicos],
                                                    names=['Rodada', 'Time_Alvo'])
        df_stats_rodada = df_stats_rodada.set_index(['Rodada', 'Time_Alvo']).reindex(index_completo,
                                                                                     fill_value=0).reset_index()

        df_stats_rodada.sort_values(by=['Time_Alvo', 'Rodada'], inplace=True)

        df_stats_rodada['Pontos_Acumulados'] = df_stats_rodada.groupby('Time_Alvo')['Pontos_Rodada'].cumsum()
        df_stats_rodada['Vitorias_Acumuladas'] = df_stats_rodada.groupby('Time_Alvo')['Vitorias_Rodada'].cumsum()
        df_stats_rodada['Empates_Acumuladas'] = df_stats_rodada.groupby('Time_Alvo')['Empates_Rodada'].cumsum()
        df_stats_rodada['Derrotas_Acumuladas'] = df_stats_rodada.groupby('Time_Alvo')['Derrotas_Rodada'].cumsum()
        df_stats_rodada['Gols_Pro_Acumulados'] = df_stats_rodada.groupby('Time_Alvo')['Gols_Pro_Rodada'].cumsum()
        df_stats_rodada['Gols_Contra_Acumulados'] = df_stats_rodada.groupby('Time_Alvo')['Gols_Contra_Rodada'].cumsum()
        df_stats_rodada['Saldo_Gols_Acumulados'] = df_stats_rodada['Gols_Pro_Acumulados'] - df_stats_rodada[
            'Gols_Contra_Acumulados']

        df_classificacao = pd.DataFrame()
        max_rodada = df_stats_rodada['Rodada'].max()

        for rodada in range(1, max_rodada + 1):
            df_rodada = df_stats_rodada[df_stats_rodada['Rodada'] == rodada].copy()
            df_rodada.sort_values(
                by=['Pontos_Acumulados', 'Vitorias_Acumuladas', 'Saldo_Gols_Acumulados', 'Gols_Pro_Acumulados'],
                ascending=[False, False, False, False],
                inplace=True
            )

            df_rodada['Posicao'] = range(1, len(df_rodada) + 1)

            df_rodada_final = df_rodada[
                ['Rodada', 'Posicao', 'Time_Alvo', 'Pontos_Acumulados', 'Vitorias_Acumuladas', 'Empates_Acumuladas',
                 'Derrotas_Acumuladas', 'Gols_Pro_Acumulados', 'Gols_Contra_Acumulados', 'Saldo_Gols_Acumulados']]
            df_classificacao = pd.concat([df_classificacao, df_rodada_final])

        df_pivot = df_classificacao.pivot_table(
            index='Rodada',
            columns='Time_Alvo',
            values='Posicao',
            fill_value=None  # Deixa NaN para rodadas onde o time não jogou (embora para o G6 isso não deve ocorrer)
        )

        colunas_ordenadas = [t for t in times_alvo_exibicao if t in df_pivot.columns]
        df_pivot = df_pivot[colunas_ordenadas]

        return df_pivot

    except FileNotFoundError:
        return f"Erro: Arquivo não encontrado em {file_path}."
    except Exception as e:
        return f"Ocorreu um erro durante a análise: {e}"


if __name__ == "__main__":
    file_path = "SerieA2023.csv"  # Assumindo que o arquivo está no mesmo diretório do script

    TIMES_ALVO_EXIBICAO = [
        'Palmeiras',
        'Grêmio',
        'Botafogo',
        'Flamengo',
        'Atlético Mineiro',
        'Bragantino'
    ]
    resultado_classificacao = analisar_classificacao_por_rodada(file_path, TIMES_ALVO_EXIBICAO)

    if isinstance(resultado_classificacao, pd.DataFrame):
        print("--- Classificação do G6 Final por Rodada - Brasileirão 2023 ---")
        print(f"Times analisados: {', '.join(TIMES_ALVO_EXIBICAO)}")
        print("\nA tabela abaixo mostra a **posição** de cada time na classificação geral ao final de cada rodada:")
        print(resultado_classificacao.to_markdown(numalign="center", stralign="center"))
    else:

        print(resultado_classificacao)

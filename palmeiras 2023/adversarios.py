import pandas as pd
import numpy as np
import re
import os




def normalizar_nome(nome):
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


def limpar_nome_exibicao(nome_original):
    if pd.isna(nome_original):
        return nome_original

    nome_limpo = nome_original.replace(' (RJ)', '').replace(' (MG)', '')
    if nome_limpo == 'Ath Paranaense':
        return 'Athletico Paranaense'
    if nome_limpo == 'Botafogo RJ':
        return 'Botafogo'
    if nome_limpo == 'America MG':
        return 'América'
    if nome_limpo == 'Gremio':
        return 'Grêmio'
    if nome_limpo == 'Goias':
        return 'Goiás'
    if nome_limpo == 'Sao Paulo':
        return 'São Paulo'
    if nome_limpo == 'Cuiaba':
        return 'Cuiabá'
    if nome_limpo == 'Bahia':
        return 'Bahia'
    if nome_limpo == 'Vasco da Gama':
        return 'Vasco da Gama'
    if nome_limpo == 'Coritiba':
        return 'Coritiba'
    if nome_limpo == 'Cruzeiro':
        return 'Cruzeiro'
    if nome_limpo == 'Santos':
        return 'Santos'
    if nome_limpo == 'Internacional':
        return 'Internacional'
    if nome_limpo == 'Fortaleza':
        return 'Fortaleza'
    if nome_limpo == 'Fluminense':
        return 'Fluminense'
    if nome_limpo == 'Corinthians':
        return 'Corinthians'
    if nome_limpo == 'Bragantino':
        return 'Bragantino'
    if nome_limpo == 'Flamengo':
        return 'Flamengo'
    if nome_limpo == 'Palmeiras':
        return 'Palmeiras'
    if nome_limpo == 'Atletico Mineiro':
        return 'Atlético Mineiro'

    return nome_limpo


def calcular_classificacao_completa(df_original):
    df = df_original.copy()

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

    todos_times_normalizados = pd.concat([df['Time_Normalizado'], df['Adversario_Normalizado']]).unique()

    mapa_exibicao = {}
    for nome_original in pd.concat([df['Time_Jogo'], df['Adversario']]).unique():
        nome_limpo = nome_original.replace(' (RJ)', '').replace(' (MG)', '').replace(' Ath Paranaense',
                                                                                     'Athletico Paranaense')
        mapa_exibicao[normalizar_nome(nome_original)] = limpar_nome_exibicao(nome_original)

    mapa_exibicao['botafogorj'] = 'Botafogo'

    df_final_jogos = pd.DataFrame()

    for time_normalizado in todos_times_normalizados:
        # Jogos onde o time é o 'Time_Jogo'
        df_time = df[df['Time_Normalizado'] == time_normalizado].copy()
        if not df_time.empty:
            df_time['Time_Alvo'] = mapa_exibicao.get(time_normalizado, time_normalizado)
            df_time['Pontos'] = df_time['Resultado_Jogo'].apply(calcular_pontos)
            df_time['Gols_Pro'] = df_time['Gols_Pro_Jogo'].astype(int)
            df_time['Gols_Contra'] = df_time['Gols_Contra_Jogo'].astype(int)
            df_final_jogos = pd.concat([df_final_jogos, df_time])

        df_adversario = df[df['Adversario_Normalizado'] == time_normalizado].copy()
        if not df_adversario.empty:
            df_adversario['Time_Alvo'] = mapa_exibicao.get(time_normalizado, time_normalizado)
            df_adversario['Resultado_Alvo'] = df_adversario['Resultado_Jogo'].replace({'V': 'D', 'D': 'V'})
            df_adversario['Pontos'] = df_adversario['Resultado_Alvo'].apply(calcular_pontos)
            df_adversario['Gols_Pro'] = df_adversario['Gols_Contra_Jogo'].astype(int)
            df_adversario['Gols_Contra'] = df_adversario['Gols_Pro_Jogo'].astype(int)
            df_final_jogos = pd.concat([df_final_jogos, df_adversario])

    df_final_jogos.drop_duplicates(subset=['Rodada', 'Time_Alvo'], keep='first', inplace=True)

    df_rodada_time = df_final_jogos.groupby(['Rodada', 'Time_Alvo']).agg(
        Pontos=('Pontos', 'sum'),
        Gols_Pro=('Gols_Pro', 'sum'),
        Gols_Contra=('Gols_Contra', 'sum')
    ).reset_index()

    df_rodada_time['Pontos_Acumulados'] = df_rodada_time.groupby('Time_Alvo')['Pontos'].cumsum()
    df_rodada_time['Gols_Pro_Acumulados'] = df_rodada_time.groupby('Time_Alvo')['Gols_Pro'].cumsum()
    df_rodada_time['Gols_Contra_Acumulados'] = df_rodada_time.groupby('Time_Alvo')['Gols_Contra'].cumsum()
    df_rodada_time['Saldo_Gols_Acumulados'] = df_rodada_time['Gols_Pro_Acumulados'] - df_rodada_time[
        'Gols_Contra_Acumulados']

    min_sg = df_rodada_time['Saldo_Gols_Acumulados'].min()
    offset_sg = abs(min_sg) + 1
    df_rodada_time['SG_Normalizado'] = df_rodada_time['Saldo_Gols_Acumulados'] + offset_sg

    df_rodada_time['Ordem_Classificacao'] = (
            df_rodada_time['Pontos_Acumulados'].astype(str).str.zfill(3) +
            df_rodada_time['SG_Normalizado'].astype(str).str.zfill(3) +
            df_rodada_time['Gols_Pro_Acumulados'].astype(str).str.zfill(3)
    )

    df_rodada_time['Posição'] = df_rodada_time.groupby('Rodada')['Ordem_Classificacao'].rank(
        method='min', ascending=False
    ).astype(int)

    return df_rodada_time[['Rodada', 'Time_Alvo', 'Posição']]


def gerar_tabela_adversarios_separada(file_path, times_foco, rodada_inicial):
    df_original = pd.read_csv(file_path)

    # 1. Calcular a classificação completa de todos os times
    df_classificacao = calcular_classificacao_completa(df_original)

    # 2. Preparar o DataFrame de jogos
    df_jogos = df_original.copy()
    df_jogos.rename(columns={
        'Oponente': 'Adversario',
        'Time': 'Time_Jogo',
        'Resultado': 'Resultado_Jogo'
    }, inplace=True)
    df_jogos['Rodada'] = df_jogos['Rodada'].astype(str).str.replace('Rodada da semana ', '', regex=False).astype(int)

    df_jogos_filtrados = df_jogos[df_jogos['Rodada'] >= rodada_inicial].copy()

    tabela_final = []

    for time_foco in times_foco:
        time_foco_normalizado = normalizar_nome(time_foco)

        if time_foco == 'Botafogo':
            time_foco_normalizado_csv = 'botafogorj'
        else:
            time_foco_normalizado_csv = time_foco_normalizado

        df_como_time = df_jogos_filtrados[
            df_jogos_filtrados['Time_Jogo'].apply(normalizar_nome) == time_foco_normalizado_csv].copy()
        df_como_time['Adversario_Nome'] = df_como_time['Adversario'].apply(limpar_nome_exibicao)
        df_como_time['Local'] = 'Casa'
        df_como_time['Resultado'] = df_como_time['Resultado_Jogo']

        df_como_adversario = df_jogos_filtrados[
            df_jogos_filtrados['Adversario'].apply(normalizar_nome) == time_foco_normalizado_csv].copy()
        df_como_adversario['Adversario_Nome'] = df_como_adversario['Time_Jogo'].apply(limpar_nome_exibicao)
        df_como_adversario['Local'] = 'Fora'
        df_como_adversario['Resultado'] = df_como_adversario['Resultado_Jogo'].replace(
            {'V': 'D', 'D': 'V'})  # Inverte o resultado

        df_foco = pd.concat([
            df_como_time[['Rodada', 'Adversario_Nome', 'Local', 'Resultado']],
            df_como_adversario[['Rodada', 'Adversario_Nome', 'Local', 'Resultado']]
        ]).sort_values(by='Rodada').drop_duplicates(subset=['Rodada'])  # Apenas uma linha por rodada

        for index, row in df_foco.iterrows():
            rodada = row['Rodada']
            adversario = row['Adversario_Nome']

            posicao_adversario = df_classificacao[
                (df_classificacao['Rodada'] == rodada) &
                (df_classificacao['Time_Alvo'] == adversario)
                ]['Posição'].iloc[0] if not df_classificacao[
                (df_classificacao['Rodada'] == rodada) &
                (df_classificacao['Time_Alvo'] == adversario)
                ].empty else np.nan

            resultado_texto = ''
            if row['Resultado'] == 'V':
                resultado_texto = 'Vitória'
            elif row['Resultado'] == 'E':
                resultado_texto = 'Empate'
            elif row['Resultado'] == 'D':
                resultado_texto = 'Derrota'

            tabela_final.append({
                'Time': time_foco,
                'Rodada': rodada,
                'Adversário': row['Adversario_Nome'],
                'Local': row['Local'],
                'Resultado (V/E/D)': row['Resultado'],  # Mantém a coluna original
                'Resultado do Jogo': resultado_texto,  # Nova coluna com texto completo
                'Posição Adversário': int(posicao_adversario) if pd.notna(posicao_adversario) else 'N/A'
            })

    df_tabela_final = pd.DataFrame(tabela_final)

    # Separar em dois DataFrames
    df_palmeiras = df_tabela_final[df_tabela_final['Time'] == 'Palmeiras'].drop(columns=['Time']).set_index('Rodada')
    df_botafogo = df_tabela_final[df_tabela_final['Time'] == 'Botafogo'].drop(columns=['Time']).set_index('Rodada')

    return df_palmeiras, df_botafogo


if __name__ == "__main__":
    file_path = r"C:\Users\bielz\Desktop\hammy\brasileirao2023-main\trabalho\Serie A 2023.csv"

    TIMES_FOCO = ['Palmeiras', 'Botafogo']
    RODADA_INICIAL = 31

    resultado = gerar_tabela_adversarios_separada(file_path, TIMES_FOCO, RODADA_INICIAL)

    if isinstance(resultado, tuple):
        df_palmeiras, df_botafogo = resultado

        print("--- Confrontos Finais do Palmeiras (Rodada 31 em diante) ---")
        print("\nResultado:")
        print(df_palmeiras.to_markdown(numalign="center", stralign="center"))

        print("\n" + "=" * 80 + "\n")

        print("--- Confrontos Finais do Botafogo (Rodada 31 em diante) ---")
        print("\nResultado:")
        print(df_botafogo.to_markdown(numalign="center", stralign="center"))
    else:
        print(resultado)


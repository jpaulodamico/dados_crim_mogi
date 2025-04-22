import pandas as pd
import sys

def analyze_data(file_path):
    try:
        # Lendo o arquivo com a codificação correta e separador ponto e vírgula
        df = pd.read_csv(file_path, encoding='latin1', sep=';', on_bad_lines='skip')
        
        print("\nAnálise dos Dados Criminais de São Paulo (2024-2025)")
        print("="*70)
        
        print("\nInformações gerais:")
        print(f"Total de registros: {len(df)}")
        print(f"Período dos dados: {df['DATA_OCORRENCIA_BO'].min()} a {df['DATA_OCORRENCIA_BO'].max()}")
        
        print("\nColunas disponíveis:")
        for col in df.columns:
            print(f"- {col}")
        
        print("\nTipos de crimes mais comuns:")
        print(df['NATUREZA_APURADA'].value_counts().head(10))
        
        print("\nDistribuição por município:")
        print(df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].value_counts().head(10))
        
        print("\nLocais mais comuns de ocorrências:")
        print(df['DESCR_SUBTIPOLOCAL'].value_counts().head(10))
        
        # Convertendo datas para análise temporal
        df['DATA_OCORRENCIA_BO'] = pd.to_datetime(df['DATA_OCORRENCIA_BO'], errors='coerce', format='%d/%m/%Y')
        df['MES_ANO'] = df['DATA_OCORRENCIA_BO'].dt.strftime('%m/%Y')
        
        print("\nDistribuição por mês/ano:")
        print(df['MES_ANO'].value_counts().sort_index().head(10))
        
        # Verificando dados geográficos
        print("\nRegistros com coordenadas geográficas:")
        df['LATITUDE'] = pd.to_numeric(df['LATITUDE'], errors='coerce')
        df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
        geo_count = df[(df['LATITUDE'] != 0) & (df['LONGITUDE'] != 0) & (~df['LATITUDE'].isna()) & (~df['LONGITUDE'].isna())].shape[0]
        print(f"Total: {geo_count} ({geo_count/len(df)*100:.2f}%)")
        
        # Salvando uma versão limpa do dataset para uso posterior
        df.to_csv('/home/ubuntu/dados_criminais_limpos.csv', index=False)
        
        return df
    
    except Exception as e:
        print(f"Erro na análise: {e}")
        return None

if __name__ == "__main__":
    file_path = '/home/ubuntu/upload/SPDadosCriminais_2024_2025.csv'
    df = analyze_data(file_path)
    
    if df is not None:
        print("\nAnálise concluída com sucesso e dados limpos salvos em 'dados_criminais_limpos.csv'")
    else:
        print("\nNão foi possível completar a análise dos dados.")

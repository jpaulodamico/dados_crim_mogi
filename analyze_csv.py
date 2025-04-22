import pandas as pd
import sys

def try_encodings(file_path):
    encodings = ['latin1', 'iso-8859-1', 'cp1252', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            print(f"\nTentando codificação: {encoding}")
            # Usando ponto e vírgula como separador e ignorando erros de análise
            df = pd.read_csv(file_path, encoding=encoding, sep=';', on_bad_lines='skip')
            print(f"Sucesso com codificação: {encoding}")
            print("\nPrimeiras 5 linhas:")
            print(df.head())
            print("\nInformações da estrutura:")
            print(df.info())
            print("\nEstatísticas descritivas:")
            print(df.describe())
            print("\nColunas disponíveis:")
            print(df.columns.tolist())
            print("\nQuantidade de registros:", len(df))
            return df, encoding
        except Exception as e:
            print(f"Erro com codificação {encoding}: {e}")
    
    return None, None

if __name__ == "__main__":
    file_path = '/home/ubuntu/upload/SPDadosCriminais_2024_2025.csv'
    df, successful_encoding = try_encodings(file_path)
    
    if df is not None:
        print(f"\nAnálise concluída com sucesso usando codificação: {successful_encoding}")
        
        # Análise adicional
        print("\nTipos de crimes mais comuns:")
        print(df['NATUREZA_APURADA'].value_counts().head(10))
        
        print("\nDistribuição por município:")
        print(df['NOME_MUNICIPIO_CIRCUNSCRIM-GM-CO'].value_counts().head(10))
        
        print("\nDistribuição por mês/ano:")
        df['DATA_OCORRENCIA_BO'] = pd.to_datetime(df['DATA_OCORRENCIA_BO'], errors='coerce', format='%d/%m/%Y')
        df['MES_ANO'] = df['DATA_OCORRENCIA_BO'].dt.strftime('%m/%Y')
        print(df['MES_ANO'].value_counts().sort_index().head(10))
    else:
        print("\nNão foi possível ler o arquivo com nenhuma das codificações testadas.")

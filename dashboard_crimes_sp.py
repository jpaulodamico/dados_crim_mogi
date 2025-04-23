import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="Dashboard de Dados Criminais - SP",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_assets():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
      :root { --primary: #1E3A8A; --bg: #F5F7F9; --card-radius: 12px; --padding: 16px; }
      body { background-color: var(--bg); }
      .card { background:white; border-radius:var(--card-radius); padding:var(--padding);
              box-shadow:0 4px 12px rgba(0,0,0,0.05); margin-bottom:24px; }
      .grid-container { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
                        gap:24px; margin-top:24px; }
    </style>
    """, unsafe_allow_html=True)

def load_lottie(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

@st.cache_data
def load_data():
    df = pd.read_csv('dados_criminais_limpos.csv')
    # Converte explicitamente para datetime
    df['DATA_REGISTRO']      = pd.to_datetime(df['DATA_REGISTRO'], dayfirst=True, errors='coerce')
    df['DATA_OCORRENCIA_BO'] = pd.to_datetime(df['DATA_OCORRENCIA_BO'], errors='coerce')
    # Extrai componentes de data
    df['ANO_REGISTRO']       = df['DATA_REGISTRO'].dt.year
    df['MES_REGISTRO']       = df['DATA_REGISTRO'].dt.month
    df['ANO_OCORRENCIA']     = df['DATA_OCORRENCIA_BO'].dt.year
    df['MES_OCORRENCIA']     = df['DATA_OCORRENCIA_BO'].dt.month
    df['DIA_SEMANA']         = df['DATA_OCORRENCIA_BO'].dt.day_name()
    # Garante que texto não seja nulo
    for c in ['BAIRRO','LOGRADOURO','NUMERO_LOGRADOURO',
              'NOME_DELEGACIA_CIRCUNSCRIÇÃO','NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
              'RUBRICA','DESCR_CONDUTA','NATUREZA_APURADA','MES_ANO']:
        if c in df.columns:
            df[c] = df[c].fillna('').astype(str)
    # Converte lat/lon para numérico (se existir)
    if 'LATITUDE' in df.columns:
        df['LATITUDE']  = pd.to_numeric(df['LATITUDE'],  errors='coerce')
    if 'LONGITUDE' in df.columns:
        df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
    return df


def main():
    load_assets()
    lottie = load_lottie("https://assets8.lottiefiles.com/packages/lf20_j1adxtyb.json")
    if lottie:
        st_lottie(lottie, height=100, key="crime")

    st.title("🚨 Dashboard de Dados Criminais - SP")
    st.markdown("### Análise interativa de ocorrências criminais (2024–2025)")

    df = load_data()

    # Sidebar
    with st.sidebar:
        menu = option_menu(
            "📋 Navegação",
            ["Distribuição","Temporal","Municípios","Rubricas","ENDEREÇOS"],
            icons=["bar-chart","calendar","geo-alt","list-task","house"],
            menu_icon="cast",
            default_index=0
        )
        st.header("Filtros")

        # filtro anos registro
        anos = sorted(df['ANO_REGISTRO'].dropna().unique().astype(int))
        sel_anos = st.slider("Registro (anos)", min(anos), max(anos), (min(anos), max(anos)))
        df = df[(df['ANO_REGISTRO']>=sel_anos[0])&(df['ANO_REGISTRO']<=sel_anos[1])]

        # filtros sem seleção padrão
        sel_mun    = st.multiselect("Municípios", sorted(df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].unique()), default=[])
        sel_nat    = st.multiselect("Natureza Apurada", sorted(df['NATUREZA_APURADA'].unique()), default=[])
        sel_rub    = st.multiselect("Rubricas", sorted(df['RUBRICA'].unique()), default=[])
        sel_cond   = st.multiselect("Condutas", sorted(df['DESCR_CONDUTA'].unique()), default=[])
        sel_del    = st.multiselect("Delegacia Circ.", sorted(df['NOME_DELEGACIA_CIRCUNSCRIÇÃO'].unique()), default=[])

        # Aplicar filtros
        if sel_mun:  df = df[df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(sel_mun)]
        if sel_nat:  df = df[df['NATUREZA_APURADA'].isin(sel_nat)]
        if sel_rub:  df = df[df['RUBRICA'].isin(sel_rub)]
        if sel_cond: df = df[df['DESCR_CONDUTA'].isin(sel_cond)]
        if sel_del:  df = df[df['NOME_DELEGACIA_CIRCUNSCRIÇÃO'].isin(sel_del)]

        st.markdown("---")

    if df.empty:
        st.warning("Não há dados para os filtros selecionados.")
        return

    # Métricas
    mais_comum = df['NATUREZA_APURADA'].mode().iloc[0] if len(df)>0 else "N/A"
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Ocorrências", f"{len(df):,}")
    c2.metric("Tipos de Crime", df['NATUREZA_APURADA'].nunique())
    c3.metric("Municípios", df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].nunique())
    c4.metric("Crime Mais Comum", mais_comum)

    tab1,tab2,tab3,tab4,tab5 = st.tabs(
        ["📊 Distribuição","📅 Temporal","🏙 Municípios","📑 Rubricas","🏠 ENDEREÇOS"]
    )

    # Distribuição
    with tab1:
        st.header("Top 10 Crimes")
        vc = df['NATUREZA_APURADA'].value_counts()
        if len(vc)>1:
            top10 = vc.head(10).reset_index(name='Qtd').rename(columns={'index':'Crime'})
            fig = px.bar(top10, x='Crime', y='Qtd',
                         color='Qtd', color_continuous_scale='Blues',
                         template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione ao menos 2 categorias para comparar.")

    # Temporal mês a mês e dia da semana
    with tab2:
        st.header("Análise Temporal")
        df_time = df.dropna(subset=['DATA_OCORRENCIA_BO'])
        # Série Mensal
        if df_time.shape[0]>1:
            df_time['MES_ANO_DT'] = pd.to_datetime(df_time['MES_ANO'], format='%m/%Y', errors='coerce')
            mensal = df_time.groupby('MES_ANO_DT').size().reset_index(name='Qtd')
            fig1 = px.line(mensal, x='MES_ANO_DT', y='Qtd',
                           title="Ocorrências Mês a Mês", markers=True)
            fig1.update_layout(xaxis_title="Mês/Ano", yaxis_title="Qtd")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Dados insuficientes para série mensal.")

        # Dia da semana
        dias = df_time['DIA_SEMANA'].value_counts()
        if len(dias)>1:
            ordem = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            dias_df = dias.reindex(ordem).dropna().reset_index(name='Qtd').rename(columns={'index':'Dia'})
            dias_df['Dia_PT'] = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
            fig2 = px.bar(dias_df, x='Dia_PT', y='Qtd',
                          title="Ocorrências por Dia da Semana",
                          color='Qtd', color_continuous_scale='Blues')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Selecione ao menos 2 dias para comparação.")

    # Municípios comparativo
    with tab3:
        st.header("Comparativo por Município")
        vc_mun = df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].value_counts()
        if len(vc_mun)>1:
            mun_df = vc_mun.reset_index(name='Qtd').rename(columns={'index':'Município'})
            fig = px.bar(mun_df, x='Município', y='Qtd',
                         color='Qtd', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione ao menos 2 municípios para comparar.")

    # Rubricas comparativo
    with tab4:
        st.header("Comparativo por Rubrica")
        vc_rub = df['RUBRICA'].value_counts()
        if len(vc_rub)>1:
            rub_df = vc_rub.reset_index(name='Qtd').rename(columns={'index':'Rubrica'})
            fig = px.bar(rub_df, x='Rubrica', y='Qtd',
                         color='Qtd', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione ao menos 2 rubricas para comparar.")

    # Endereços
    with tab5:
        st.header("Endereços das Ocorrências")
        addr = df[['LOGRADOURO','NUMERO_LOGRADOURO','BAIRRO']].dropna(subset=['LOGRADOURO'])
        addr = addr.rename(columns={
            'LOGRADOURO':'Logradouro',
            'NUMERO_LOGRADOURO':'Número',
            'BAIRRO':'Bairro'
        })
        st.dataframe(addr, use_container_width=True)

    st.markdown("---")
    st.caption("Dashboard desenvolvido para SP (2024–2025)")

if __name__=="__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu

# --- Configuração da página ---
st.set_page_config(
    page_title="Dashboard de Dados Criminais - SP",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Fonte e CSS customizado ---
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

# --- Lottie animation loader ---
def load_lottie(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

# --- Carrega e prepara os dados ---
@st.cache_data
def load_data():
    df = pd.read_csv('dados_criminais_limpos.csv')
    # converte datas
    df['DATA_REGISTRO']      = pd.to_datetime(df['DATA_REGISTRO'], dayfirst=True, errors='coerce')
    df['DATA_OCORRENCIA_BO'] = pd.to_datetime(df['DATA_OCORRENCIA_BO'], errors='coerce')
    # componentes temporais
    df['ANO_REGISTRO']    = df['DATA_REGISTRO'].dt.year
    df['MES_REGISTRO']    = df['DATA_REGISTRO'].dt.month
    df['ANO_OCORRENCIA']  = df['DATA_OCORRENCIA_BO'].dt.year
    df['MES_OCORRENCIA']  = df['DATA_OCORRENCIA_BO'].dt.month
    df['DIA_SEMANA']      = df['DATA_OCORRENCIA_BO'].dt.day_name()
    # colunas de texto
    for c in ['DESCR_SUBTIPOLOCAL','BAIRRO','LOGRADOURO','NUMERO_LOGRADOURO',
              'NOME_DELEGACIA_CIRCUNSCRIÇÃO','NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
              'RUBRICA','DESCR_CONDUTA','NATUREZA_APURADA','MES_ANO']:
        if c in df.columns:
            df[c] = df[c].fillna('').astype(str)
    return df


def main():
    load_assets()
    lottie = load_lottie("https://assets8.lottiefiles.com/packages/lf20_j1adxtyb.json")
    if lottie:
        st_lottie(lottie, height=100)

    st.title("🚨 Dashboard de Dados Criminais - SP")
    st.markdown("### Análise interativa de ocorrências criminais (2024–2025)")

    df = load_data()

    # --- Sidebar de filtros ---
    with st.sidebar:
        menu = option_menu(
            "📋 Navegação",
            ["📊 Distribuição","📅 Temporal","🏙 Municípios","📑 Rubricas","🏠 ENDEREÇOS"],
            icons=["bar-chart","calendar","geo-alt","list-task","house"],
            menu_icon="cast",
            default_index=0
        )
        st.header("Filtros")

        # Filtro de Mês/Ano Ocorrência: somente meses de 2024 e 2025
        all_mes_anos = sorted({m for m in df['MES_ANO'].unique() if m.endswith('/2024') or m.endswith('/2025')})
        sel_ma = st.multiselect(
            "Mês/Ano Ocorrência", 
            options=all_mes_anos, 
            default=all_mes_anos
        )
        if sel_ma:
            df = df[df['MES_ANO'].isin(sel_ma)]

        # Demais filtros sem seleção padrão
        sel_mun  = st.multiselect("Municípios", sorted(df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].unique()), default=[])
        sel_nat  = st.multiselect("Natureza Apurada", sorted(df['NATUREZA_APURADA'].unique()), default=[])
        sel_rub  = st.multiselect("Rubricas", sorted(df['RUBRICA'].unique()), default=[])
        sel_cond = st.multiselect("Condutas", sorted(df['DESCR_CONDUTA'].unique()), default=[])
        sel_del  = st.multiselect("Delegacia Circ.", sorted(df['NOME_DELEGACIA_CIRCUNSCRIÇÃO'].unique()), default=[])

        if sel_mun:  df = df[df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(sel_mun)]
        if sel_nat:  df = df[df['NATUREZA_APURADA'].isin(sel_nat)]
        if sel_rub:  df = df[df['RUBRICA'].isin(sel_rub)]
        if sel_cond: df = df[df['DESCR_CONDUTA'].isin(sel_cond)]
        if sel_del:  df = df[df['NOME_DELEGACIA_CIRCUNSCRIÇÃO'].isin(sel_del)]

        st.markdown("---")

    if df.empty:
        st.warning("Não há dados para os filtros selecionados.")
        return

    # --- Métricas principais ---
    mais_comum = df['NATUREZA_APURADA'].mode().iloc[0] if not df.empty else "N/A"
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Ocorrências", f"{len(df):,}")
    c2.metric("Tipos de Crime", df['NATUREZA_APURADA'].nunique())
    c3.metric("Municípios", df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].nunique())
    c4.metric("Crime Mais Comum", mais_comum)

    # --- Abas ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Distribuição","📅 Temporal","🏙 Municípios","📑 Rubricas","🏠 ENDEREÇOS"
    ])

    # 1) Distribuição de Crimes
    with tab1:
        st.header("Top 10 Crimes")
        vc = df['NATUREZA_APURADA'].value_counts()
        if vc.shape[0] > 1:
            top10 = vc.rename_axis('Crime').reset_index(name='Qtd').head(10)
            fig = px.bar(top10, x='Crime', y='Qtd',
                         color='Qtd', color_continuous_scale='Blues', template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione ao menos 2 categorias para comparar.")

    # 2) Ocorrências Mês a Mês
    with tab2:
        st.header("Ocorrências Mês a Mês (2024-2025)")
        mensal = df.groupby('MES_ANO').size().reset_index(name='Qtd')
        mensal['dt'] = pd.to_datetime(mensal['MES_ANO'], format='%m/%Y', errors='coerce')
        mensal = mensal.sort_values('dt')
        fig1 = px.bar(
            mensal, x='dt', y='Qtd',
            labels={'dt':'Mês/Ano','Qtd':'Ocorrências'},
            template='plotly_white'
        )
        fig1.update_xaxes(tickformat='%b %Y', dtick="M1")
        st.plotly_chart(fig1, use_container_width=True)

    # 3) Comparativo por Município
    with tab3:
        st.header("Comparativo por Município")
        vc_mun = df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].value_counts()
        if vc_mun.shape[0] > 1:
            mun_df = vc_mun.rename_axis('Município').reset_index(name='Qtd')
            fig = px.bar(mun_df, x='Município', y='Qtd',
                         color='Qtd', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)

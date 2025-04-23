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
    df['DATA_REGISTRO']      = pd.to_datetime(df['DATA_REGISTRO'], errors='coerce', format='%d/%m/%Y')
    df['DATA_OCORRENCIA_BO'] = pd.to_datetime(df['DATA_OCORRENCIA_BO'], errors='coerce')
    df['ANO_REGISTRO']       = df['DATA_REGISTRO'].dt.year
    df['MES_REGISTRO']       = df['DATA_REGISTRO'].dt.month
    df['ANO_OCORRENCIA']     = df['DATA_OCORRENCIA_BO'].dt.year
    df['MES_OCORRENCIA']     = df['DATA_OCORRENCIA_BO'].dt.month
    df['DIA_SEMANA']         = df['DATA_OCORRENCIA_BO'].dt.day_name()
    # Garante colunas de texto
    df['BAIRRO']             = df.get('BAIRRO','').fillna('')
    df['LOGRADOURO']         = df.get('LOGRADOURO','').fillna('')
    # numérico em lat/lon (mas não usaremos mapa)
    df['LATITUDE']  = pd.to_numeric(df.get('LATITUDE'),  errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df.get('LONGITUDE'), errors='coerce')
    return df

def main():
    load_assets()
    lottie = load_lottie("https://assets8.lottiefiles.com/packages/lf20_j1adxtyb.json")
    if lottie:
        st_lottie(lottie, height=100, key="crime")

    st.title("🚨 Dashboard de Dados Criminais - SP")
    st.markdown("### Análise interativa de ocorrências criminais em municípios de SP")

    df = load_data()
    with st.sidebar:
        menu = option_menu(
            "📋 Navegação",
            ["Distribuição","Temporal","Municípios","Rubricas","ENDEREÇOS"],
            icons=["bar-chart","calendar","geo-alt","list-task","house"],
            default_index=0
        )
        st.header("Filtros")

        # Período (anos de registro)
        anos = sorted(df['ANO_REGISTRO'].dropna().unique().astype(int))
        ano_sel = st.slider("Registro (anos)", min(anos), max(anos), (min(anos), max(anos)))
        df = df[(df['ANO_REGISTRO'] >= ano_sel[0]) & (df['ANO_REGISTRO'] <= ano_sel[1])]

        # Município (sem default)
        municipios = sorted(df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].dropna().unique())
        sel_muns = st.multiselect("Municípios", municipios, default=[])
        if sel_muns:
            df = df[df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(sel_muns)]

        # Natureza apurada (sem default)
        crimes = sorted(df['NATUREZA_APURADA'].dropna().unique())
        sel_crimes = st.multiselect("Natureza Apurada", crimes, default=[])
        if sel_crimes:
            df = df[df['NATUREZA_APURADA'].isin(sel_crimes)]

        # Rubrica
        rubricas = sorted(df['RUBRICA'].dropna().unique())
        sel_rub = st.multiselect("Rubricas", rubricas, default=[])
        if sel_rub:
            df = df[df['RUBRICA'].isin(sel_rub)]

        # Conduta
        condutas = sorted(df['DESCR_CONDUTA'].dropna().unique())
        sel_cond = st.multiselect("Condutas", condutas, default=[])
        if sel_cond:
            df = df[df['DESCR_CONDUTA'].isin(sel_cond)]

        # Delegacia / Distrito Policial
        deleg = sorted(df['NOME_DELEGACIA_CIRCUNSCRIÇÃO'].dropna().unique())
        sel_del = st.multiselect("Delegacia (Circ.)", deleg, default=[])
        if sel_del:
            df = df[df['NOME_DELEGACIA_CIRCUNSCRIÇÃO'].isin(sel_del)]

        st.markdown("---")

    if df.empty:
        st.warning("Sem dados para os filtros selecionados.")
        return

    # Métricas
    mais_comum = df['NATUREZA_APURADA'].mode().iloc[0] if not df.empty else "N/A"
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Ocorrências", f"{len(df):,}")
    c2.metric("Tipos de Crime", df['NATUREZA_APURADA'].nunique())
    c3.metric("Municípios", df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].nunique())
    c4.metric("Crime Mais Comum", mais_comum)

    tab1,tab2,tab3,tab4,tab5 = st.tabs(
        ["📊 Distribuição","📅 Temporal","🏙 Municípios","📑 Rubricas","🏠 ENDEREÇOS"]
    )

    # 1) Distribuição
    with tab1:
        st.header("Top 10 Crimes")
        vc = df['NATUREZA_APURADA'].value_counts()
        if len(vc)>1:
            top10 = vc.head(10).reset_index().rename(columns={'index':'Crime','NATUREZA_APURADA':'Qtd'})
            fig = px.bar(top10, x='Crime', y='Qtd',
                         color='Qtd', color_continuous_scale='Blues', template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione ao menos 2 crimes para comparar.")

    # 2) Temporal
    with tab2:
        st.header("Séries Temporais")
        # Mês a mês (ocorrência)
        df_time = df.dropna(subset=['DATA_OCORRENCIA_BO'])
        if df_time.shape[0]>1:
            df_time['MÊS_ANO'] = df_time['DATA_OCORRENCIA_BO'].dt.to_period('M').dt.to_timestamp()
            mensal = df_time.groupby('MÊS_ANO').size().reset_index(name='Qtd')
            fig1 = px.line(mensal, x='MÊS_ANO', y='Qtd',
                           title="Ocorrências Mês a Mês", markers=True)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Não há dados suficientes para série mensal.")

        # Dia da semana
        dias = df_time['DIA_SEMANA'].value_counts()
        if len(dias)>1:
            ordem = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            dias = dias.reindex(ordem).dropna().reset_index().rename(columns={'index':'Dia','DIA_SEMANA':'Qtd'})
            dias['Dia_PT'] = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
            fig2 = px.bar(dias, x='Dia_PT', y='Qtd',
                          title="Ocorrências por Dia da Semana",
                          color='Qtd', color_continuous_scale='Blues')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Selecione dados suficientes para comparação por dia.")

    # 3) Municípios
    with tab3:
        st.header("Comparativo por Município")
        mun_counts = df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].value_counts()
        if len(mun_counts)>1:
            mun_df = mun_counts.reset_index().rename(columns={'index':'Município','NOME_MUNICIPIO_CIRCUNSCRIÇÃO':'Qtd'})
            fig = px.bar(mun_df, x='Município', y='Qtd',
                         color='Qtd', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione ao menos 2 municípios para comparar.")

    # 4) Rubricas
    with tab4:
        st.header("Comparativo por Rubrica")
        rub_counts = df['RUBRICA'].value_counts()
        if len(rub_counts)>1:
            rub_df = rub_counts.head(15).reset_index().rename(columns={'index':'Rubrica','RUBRICA':'Qtd'})
            fig = px.bar(rub_df, x='Rubrica', y='Qtd',
                         color='Qtd', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione ao menos 2 rubricas para comparar.")

    # 5) Endereços
    with tab5:
        st.header("Endereços das Ocorrências")
        cols = ['NOME_MUNICIPIO_CIRCUNSCRIÇÃO','LOGRADOURO','NUMERO_LOGRADOURO','BAIRRO']
        addr = df[cols].dropna(subset=['LOGRADOURO'])
        addr = addr.rename(columns={
            'NOME_MUNICIPIO_CIRCUNSCRIÇÃO':'Município',
            'LOGRADOURO':'Logradouro',
            'NUMERO_LOGRADOURO':'Número',
            'BAIRRO':'Bairro'
        })
        st.dataframe(addr, use_container_width=True)

    st.markdown("---")
    st.caption("Dashboard SP (2024–2025)")

if __name__=="__main__":
    main()

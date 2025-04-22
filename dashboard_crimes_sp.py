import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Dados Criminais - Delegacia Seccional Mogi das Cruzes - SP",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para carregar os dados
@st.cache_data
def load_data():
    df = pd.read_csv('dados_criminais_limpos.csv')
    # Renomeando colunas para facilitar o uso
    
    # Convertendo datas para datetime com tratamento de formatos mistos
    # Primeiro, garantir que todas as datas estão no mesmo formato
    df['DATA_REGISTRO'] = pd.to_datetime(df['DATA_REGISTRO'], errors='coerce', format='%d/%m/%Y')
    
    # Para DATA_OCORRENCIA_BO, tentar primeiro o formato ISO e depois o formato brasileiro
    try:
        df['DATA_OCORRENCIA_BO'] = pd.to_datetime(df['DATA_OCORRENCIA_BO'], errors='coerce')
    except:
        # Se falhar, tenta outros formatos
        pass
    
    # Criando colunas de ano e mês para facilitar a análise
    df['ANO'] = df['DATA_OCORRENCIA_BO'].dt.year
    df['MES'] = df['DATA_OCORRENCIA_BO'].dt.month
    
    # Criar MES_ANO a partir das colunas ANO e MES para evitar problemas com NaT
    df['MES_ANO_CALC'] = df.apply(lambda x: f"{x['MES']:02d}/{x['ANO']}" if pd.notna(x['MES']) and pd.notna(x['ANO']) else "Desconhecido", axis=1)
    
    return df

# Função para aplicar estilo personalizado
def local_css():
    st.markdown("""
    <style>
        .main {
            background-color: #f5f7f9;
        }
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1, h2, h3 {
            color: #1E3A8A;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #FFFFFF;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1E3A8A;
            color: white;
        }
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .metric-card {
            background-color: #1E3A8A;
            color: white;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
        }
        .metric-label {
            font-size: 14px;
            opacity: 0.8;
        }
    </style>
    """, unsafe_allow_html=True)

# Função principal
def main():
    # Aplicar estilo personalizado
    local_css()
    
    # Título do dashboard
    st.title("🚨 Dashboard de Dados Criminais - Delegacia Seccional de Mogi das Cruzes - SP")
    st.markdown("### Análise interativa de ocorrências criminais em municípios da região")
    st.markdown("#### Dados de 2024 a 2025")
    st.markdown("---")
    st.markdown("### Carregando dados...")
    st.spinner("Carregando dados, por favor aguarde...")
    st.markdown("---")
    
    # Carregar dados
    try:
        df = load_data()
        
        # Sidebar para filtros
        st.sidebar.header("Filtros")
        
        # Filtro de período - usando anos em vez de datas específicas para evitar problemas com NaT
        anos_disponiveis = sorted(df['ANO'].dropna().unique().astype(int).tolist())
        if anos_disponiveis:
            ano_min = min(anos_disponiveis)
            ano_max = max(anos_disponiveis)
            
            anos_selecionados = st.sidebar.slider(
                "Período (Anos)",
                min_value=ano_min,
                max_value=ano_max,
                value=(ano_min, ano_max)
            )
            
            filtered_df = df[(df['ANO'] >= anos_selecionados[0]) & (df['ANO'] <= anos_selecionados[1])]
        else:
            filtered_df = df
            st.sidebar.warning("Não foi possível determinar o período dos dados.")
        
        # Filtro de município
        municipios = sorted(df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].dropna().unique())
        selected_municipios = st.sidebar.multiselect(
            "Municípios",
            options=municipios,
            default=municipios[:3] if len(municipios) >= 3 else municipios  # Seleciona os 3 primeiros por padrão
        )
        
        if selected_municipios:
            filtered_df = filtered_df[filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(selected_municipios)]
        
        # Filtro de tipo de crime
        crimes = sorted(df['NATUREZA_APURADA'].dropna().unique())
        selected_crimes = st.sidebar.multiselect(
            "Tipos de Crime",
            options=crimes,
            default=crimes[:5] if len(crimes) >= 5 else crimes  # Seleciona os 5 primeiros por padrão
        )
        
        if selected_crimes:
            filtered_df = filtered_df[filtered_df['NATUREZA_APURADA'].isin(selected_crimes)]
        
        # Verificar se há dados após a filtragem
        if filtered_df.empty:
            st.warning("Não há dados disponíveis para os filtros selecionados. Por favor, ajuste os filtros.")
            return
        
        # Métricas principais
        st.markdown("## Métricas Principais")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(filtered_df)}</div>
                <div class="metric-label">Total de Ocorrências</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{filtered_df['NATUREZA_APURADA'].nunique()}</div>
                <div class="metric-label">Tipos de Crime</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].nunique()}</div>
                <div class="metric-label">Municípios</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            crime_mais_comum = filtered_df['NATUREZA_APURADA'].value_counts().idxmax() if not filtered_df['NATUREZA_APURADA'].empty else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 18px;">{crime_mais_comum}</div>
                <div class="metric-label">Crime Mais Comum</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Abas para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📊 Distribuição de Crimes", "📅 Análise Temporal", "🏙️ Análise por Município"])
        
        with tab1:
            st.markdown("## Distribuição de Crimes")
            
            # Gráfico de distribuição de crimes
            crime_counts = filtered_df['NATUREZA_APURADA'].value_counts().reset_index()
            crime_counts.columns = ['Crime', 'Quantidade']
            
            if not crime_counts.empty:
                fig = px.bar(
                    crime_counts.head(10), 
                    x='Crime', 
                    y='Quantidade',
                    title='Top 10 Crimes Mais Frequentes',
                    color='Quantidade',
                    color_continuous_scale='Blues',
                    template='plotly_white'
                )
                
                fig.update_layout(
                    xaxis_title="Tipo de Crime",
                    yaxis_title="Número de Ocorrências",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Não há dados suficientes para gerar o gráfico de distribuição de crimes.")
            
            # Distribuição por local de ocorrência
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                if not filtered_df['DESCR_SUBTIPOLOCAL'].dropna().empty:
                    local_counts = filtered_df['DESCR_SUBTIPOLOCAL'].value_counts().reset_index()
                    local_counts.columns = ['Local', 'Quantidade']
                    
                    fig = px.pie(
                        local_counts.head(5), 
                        values='Quantidade', 
                        names='Local',
                        title='Top 5 Locais de Ocorrência',
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Blues_r
                    )
                    
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Não há dados suficientes para gerar o gráfico de locais de ocorrência.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                hora_counts = filtered_df['HORA_OCORRENCIA_BO'].dropna()
                if not hora_counts.empty:
                    try:
                        hora_counts = pd.to_datetime(hora_counts, format='%H:%M:%S', errors='coerce')
                        hora_counts = hora_counts.dt.hour.value_counts().sort_index()
                        
                        fig = px.line(
                            x=hora_counts.index, 
                            y=hora_counts.values,
                            title='Distribuição de Ocorrências por Hora do Dia',
                            markers=True
                        )
                        
                        fig.update_layout(
                            xaxis_title="Hora do Dia",
                            yaxis_title="Número de Ocorrências",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except:
                        st.warning("Não foi possível processar os dados de hora para visualização.")
                else:
                    st.warning("Não há dados suficientes para gerar o gráfico de distribuição por hora.")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.markdown("## Análise Temporal")
            
            # Análise por ano
            temporal = filtered_df.groupby('ANO').size().reset_index(name='Quantidade')
            temporal = temporal.sort_values('ANO')
            
            if not temporal.empty and len(temporal) > 1:
                fig = px.line(
                    temporal, 
                    x='ANO', 
                    y='Quantidade',
                    title='Evolução de Ocorrências ao Longo dos Anos',
                    markers=True
                )
                
                fig.update_layout(
                    xaxis_title="Ano",
                    yaxis_title="Número de Ocorrências",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Não há dados suficientes para gerar o gráfico de evolução temporal.")
            
            # Análise por dia da semana e tipo de crime
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                if not filtered_df['DATA_OCORRENCIA_BO'].dropna().empty:
                    try:
                        filtered_df['DIA_SEMANA'] = filtered_df['DATA_OCORRENCIA_BO'].dt.day_name()
                        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                        
                        dia_counts = filtered_df['DIA_SEMANA'].value_counts().reindex(dias_ordem).reset_index()
                        dia_counts.columns = ['Dia', 'Quantidade']
                        dia_counts['Dia_PT'] = dias_pt
                        
                        fig = px.bar(
                            dia_counts, 
                            x='Dia_PT', 
                            y='Quantidade',
                            title='Distribuição por Dia da Semana',
                            color='Quantidade',
                            color_continuous_scale='Blues'
                        )
                        
                        fig.update_layout(
                            xaxis_title="Dia da Semana",
                            yaxis_title="Número de Ocorrências",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except:
                        st.warning("Não foi possível processar os dados por dia da semana.")
                else:
                    st.warning("Não há dados suficientes para gerar o gráfico por dia da semana.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                # Selecionar os 3 crimes mais comuns para análise temporal
                top_crimes = filtered_df['NATUREZA_APURADA'].value_counts().head(3).index.tolist()
                if top_crimes:
                    top_crimes_df = filtered_df[filtered_df['NATUREZA_APURADA'].isin(top_crimes)]
                    
                    # Agrupar por ano e tipo de crime
                    crime_temporal = top_crimes_df.groupby(['ANO', 'NATUREZA_APURADA']).size().reset_index(name='Quantidade')
                    
                    if not crime_temporal.empty and len(crime_temporal) > 3:
                        fig = px.line(
                            crime_temporal, 
                            x='ANO', 
                            y='Quantidade',
                            color='NATUREZA_APURADA',
                            title='Evolução dos 3 Crimes Mais Comuns',
                            markers=True
                        )
                        
                        fig.update_layout(
                            xaxis_title="Ano",
                            yaxis_title="Número de Ocorrências",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Não há dados suficientes para gerar o gráfico de evolução por tipo de crime.")
                else:
                    st.warning("Não há dados suficientes para identificar os crimes mais comuns.")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab3:
            st.markdown("## Análise por Município")
            
            # Distribuição por município
            municipio_counts = filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].value_counts().reset_index()
            municipio_counts.columns = ['Município', 'Quantidade']
            
            if not municipio_counts.empty:
                fig = px.bar(
                    municipio_counts, 
                    x='Município', 
                    y='Quantidade',
                    title='Distribuição de Ocorrências por Município',
                    color='Quantidade',
                    color_continuous_scale='Blues'
                )
                
                fig.update_layout(
                    xaxis_title="Município",
                    yaxis_title="Número de Ocorrências",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Não há dados suficientes para gerar o gráfico de distribuição por município.")
            
            # Análise por município e tipo de crime
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                # Selecionar os 3 municípios com mais ocorrências
                top_municipios = municipio_counts['Município'].head(3).tolist() if not municipio_counts.empty else []
                
                if top_municipios:
                    # Filtrar para os municípios selecionados
                    top_mun_df = filtered_df[filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(top_municipios)]
                    
                    # Contar os tipos de crimes mais comuns em cada município
                    mun_crime = top_mun_df.groupby(['NOME_MUNICIPIO_CIRCUNSCRIÇÃO', 'NATUREZA_APURADA']).size().reset_index(name='Quantidade')
                    
                    # Pegar os 5 crimes mais comuns para cada município
                    top_crimes_por_mun = []
                    for mun in top_municipios:
                        mun_data = mun_crime[mun_crime['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'] == mun]
                        top_5 = mun_data.nlargest(5, 'Quantidade')
                        top_crimes_por_mun.append(top_5)
                    
                    mun_crime_top = pd.concat(top_crimes_por_mun)
                    
                    fig = px.bar(
                        mun_crime_top, 
                        x='NATUREZA_APURADA', 
                        y='Quantidade',
                        color='NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
                        title='Top 5 Crimes por Município',
                        barmode='group'
                    )
                    
                    fig.update_layout(
                        xaxis_title="Tipo de Crime",
                        yaxis_title="Número de Ocorrências",
                        height=400,
                        xaxis={'categoryorder':'total descending'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Não há dados suficientes para gerar o gráfico de crimes por município.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                if top_municipios:
                    # Análise de locais mais comuns por município
                    mun_local = filtered_df.groupby(['NOME_MUNICIPIO_CIRCUNSCRIÇÃO', 'DESCR_SUBTIPOLOCAL']).size().reset_index(name='Quantidade')
                    
                    # Filtrar para os 3 municípios principais
                    mun_local = mun_local[mun_local['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(top_municipios)]
                    
                    # Pegar os 3 locais mais comuns para cada município
                    top_locais_por_mun = []
                    for mun in top_municipios:
                        mun_data = mun_local[mun_local['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'] == mun]
                        top_3 = mun_data.nlargest(3, 'Quantidade')
                        top_locais_por_mun.append(top_3)
                    
                    mun_local_top = pd.concat(top_locais_por_mun)
                    
                    fig = px.bar(
                        mun_local_top, 
                        x='DESCR_SUBTIPOLOCAL', 
                        y='Quantidade',
                        color='NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
                        title='Locais Mais Comuns por Município',
                        barmode='group'
                    )
                    
                    fig.update_layout(
                        xaxis_title="Local",
                        yaxis_title="Número de Ocorrências",
                        height=400,
                        xaxis={'categoryorder':'total descending'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Não há dados suficientes para gerar o gráfico de locais por município.")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Rodapé
        st.markdown("---")
        st.markdown("Dashboard desenvolvido para análise interativa de dados criminais da Região do Alto Tietê - Del.Sec. Mogi das Cruzes (2024-2025)")
        
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados: {e}")
        st.info("Verifique se o arquivo 'dados_criminais_limpos.csv' está disponível no diretório atual.")

if __name__ == "__main__":
    main()

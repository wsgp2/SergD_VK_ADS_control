"""
Модуль для отображения дашборда с ключевыми метриками рекламных кампаний.
"""
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

def render_dashboard(vk_client, openai_client, account_id, date_from, date_to, campaigns):
    """
    Отображает дашборд с ключевыми метриками рекламных кампаний.
    
    Args:
        vk_client: Клиент API ВКонтакте
        openai_client: Клиент API OpenAI
        account_id: ID рекламного аккаунта
        date_from: Начальная дата анализа
        date_to: Конечная дата анализа
        campaigns: Список рекламных кампаний
    """
    # Собираем данные для дашборда
    campaign_data = []
    
    for campaign in campaigns:
        if campaign.get('status') == 'active':
            try:
                # Получение статистики по кампании
                stats = vk_client.get_statistics(
                    account_id=account_id,
                    ids_type="campaign",
                    ids=[campaign['id']],
                    period="day",
                    date_from=date_from,
                    date_to=date_to
                )
                
                if stats and len(stats) > 0 and 'stats' in stats[0]:
                    for day_stat in stats[0]['stats']:
                        day_data = {
                            'campaign_id': campaign['id'],
                            'campaign_name': campaign['name'],
                            'date': day_stat.get('day', ''),
                            'impressions': day_stat.get('impressions', 0),
                            'clicks': day_stat.get('clicks', 0),
                            'ctr': round(day_stat.get('clicks', 0) / max(day_stat.get('impressions', 1), 1) * 100, 2),
                            'spent': day_stat.get('spent', 0),
                            'cpc': round(day_stat.get('spent', 0) / max(day_stat.get('clicks', 1), 1), 2)
                        }
                        campaign_data.append(day_data)
            
            except Exception as e:
                st.warning(f"Ошибка при получении статистики для кампании {campaign['name']}: {e}")
    
    if not campaign_data:
        st.warning("Нет данных о рекламных кампаниях за выбранный период.")
        return
    
    # Создаем DataFrame с данными
    df = pd.DataFrame(campaign_data)
    
    # Графики и метрики
    render_performance_metrics(df)
    render_trends_analysis(df)
    render_campaign_comparison(df)
    
    # AI рекомендации
    if openai_client:
        render_ai_recommendations(openai_client, df, campaigns)

def render_performance_metrics(df: pd.DataFrame):
    """Отображает ключевые метрики эффективности"""
    st.markdown("<h2 class='sub-header'>Ключевые метрики эффективности</h2>", unsafe_allow_html=True)
    
    # Агрегированные метрики
    total_impressions = df['impressions'].sum()
    total_clicks = df['clicks'].sum()
    total_spent = df['spent'].sum()
    avg_ctr = round(total_clicks / max(total_impressions, 1) * 100, 2)
    avg_cpc = round(total_spent / max(total_clicks, 1), 2)
    
    # Отображение метрик
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(label="Показы", value=f"{int(total_impressions):,}")
    
    with col2:
        st.metric(label="Клики", value=f"{int(total_clicks):,}")
    
    with col3:
        st.metric(label="CTR", value=f"{avg_ctr}%")
    
    with col4:
        st.metric(label="Расходы", value=f"{total_spent:,.2f} ₽")
    
    with col5:
        st.metric(label="CPC", value=f"{avg_cpc:.2f} ₽")

def render_trends_analysis(df: pd.DataFrame):
    """Отображает анализ трендов по дням"""
    st.markdown("<h2 class='sub-header'>Динамика показателей по дням</h2>", unsafe_allow_html=True)
    
    # Агрегация данных по дням
    daily_data = df.groupby('date').agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'spent': 'sum'
    }).reset_index()
    
    # Расчет CTR и CPC
    daily_data['ctr'] = daily_data['clicks'] / daily_data['impressions'] * 100
    daily_data['cpc'] = daily_data['spent'] / daily_data['clicks']
    
    # Создаем график с двумя осями Y
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(
            daily_data, 
            x='date', 
            y=['impressions', 'clicks'],
            title="Динамика показов и кликов",
            labels={'value': 'Количество', 'date': 'Дата', 'variable': 'Метрика'},
            color_discrete_sequence=['#4CAF50', '#2196F3']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(
            daily_data, 
            x='date', 
            y=['ctr', 'cpc'],
            title="Динамика CTR и CPC",
            labels={'value': 'Значение', 'date': 'Дата', 'variable': 'Метрика'},
            color_discrete_sequence=['#FFC107', '#F44336']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # График расходов
    fig = px.bar(
        daily_data,
        x='date',
        y='spent',
        title="Ежедневные расходы на рекламу",
        labels={'spent': 'Расходы (₽)', 'date': 'Дата'},
        color_discrete_sequence=['#673AB7']
    )
    st.plotly_chart(fig, use_container_width=True)

def render_campaign_comparison(df: pd.DataFrame):
    """Отображает сравнение эффективности кампаний"""
    st.markdown("<h2 class='sub-header'>Сравнение эффективности кампаний</h2>", unsafe_allow_html=True)
    
    # Агрегация данных по кампаниям
    campaign_data = df.groupby('campaign_name').agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'spent': 'sum'
    }).reset_index()
    
    # Расчет CTR и CPC
    campaign_data['ctr'] = campaign_data['clicks'] / campaign_data['impressions'] * 100
    campaign_data['cpc'] = campaign_data['spent'] / campaign_data['clicks']
    campaign_data['efficiency'] = campaign_data['clicks'] / campaign_data['spent']
    
    # Сортировка по эффективности
    campaign_data = campaign_data.sort_values(by='efficiency', ascending=False)
    
    # Создаем графики
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            campaign_data,
            x='campaign_name',
            y='ctr',
            title="CTR по кампаниям",
            labels={'ctr': 'CTR (%)', 'campaign_name': 'Кампания'},
            color='ctr',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            campaign_data,
            x='campaign_name',
            y='cpc',
            title="CPC по кампаниям",
            labels={'cpc': 'CPC (₽)', 'campaign_name': 'Кампания'},
            color='cpc',
            color_continuous_scale='Viridis_r'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Таблица с данными по кампаниям
    st.markdown("<h3>Таблица эффективности кампаний</h3>", unsafe_allow_html=True)
    st.dataframe(
        campaign_data[['campaign_name', 'impressions', 'clicks', 'ctr', 'spent', 'cpc', 'efficiency']].rename(
            columns={
                'campaign_name': 'Кампания',
                'impressions': 'Показы',
                'clicks': 'Клики',
                'ctr': 'CTR (%)',
                'spent': 'Расходы (₽)',
                'cpc': 'CPC (₽)',
                'efficiency': 'Эффективность (клики/₽)'
            }
        ),
        use_container_width=True
    )

def render_ai_recommendations(openai_client, df: pd.DataFrame, campaigns: List[Dict[str, Any]]):
    """Отображает ИИ-рекомендации на основе данных кампаний"""
    st.markdown("<h2 class='sub-header'>AI-рекомендации</h2>", unsafe_allow_html=True)
    
    with st.expander("Получить AI-рекомендации по оптимизации кампаний", expanded=False):
        if st.button("Сгенерировать рекомендации"):
            with st.spinner("Генерация рекомендаций..."):
                # Агрегация данных по кампаниям
                campaign_data = df.groupby('campaign_name').agg({
                    'impressions': 'sum',
                    'clicks': 'sum',
                    'spent': 'sum'
                }).reset_index()
                
                # Расчет CTR и CPC
                campaign_data['ctr'] = campaign_data['clicks'] / campaign_data['impressions'] * 100
                campaign_data['cpc'] = campaign_data['spent'] / campaign_data['clicks']
                
                # Подготовка данных для анализа
                analysis_data = {
                    "campaigns": campaign_data.to_dict('records'),
                    "total_stats": {
                        "impressions": int(df['impressions'].sum()),
                        "clicks": int(df['clicks'].sum()),
                        "spent": float(df['spent'].sum()),
                        "ctr": round(df['clicks'].sum() / df['impressions'].sum() * 100, 2),
                        "cpc": round(df['spent'].sum() / df['clicks'].sum(), 2)
                    },
                    "campaign_count": len(campaigns),
                    "active_campaigns": sum(1 for c in campaigns if c.get('status') == 'active')
                }
                
                # Получение рекомендаций от OpenAI
                recommendations = openai_client.generate_optimization_recommendations(analysis_data)
                
                # Вывод рекомендаций
                st.markdown(recommendations)

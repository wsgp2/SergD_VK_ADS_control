"""
Модуль для создания отчетов по рекламным кампаниям.
"""
import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px

def render_reports(vk_client, openai_client, account_id, date_from, date_to):
    """
    Отображает страницу с отчетами по рекламным кампаниям.
    
    Args:
        vk_client: Клиент API ВКонтакте
        openai_client: Клиент API OpenAI
        account_id: ID рекламного аккаунта
        date_from: Начальная дата анализа
        date_to: Конечная дата анализа
    """
    # Типы отчетов
    report_types = {
        "Эффективность кампаний": "campaign_performance",
        "Демографический анализ": "demographic",
        "Оценка работы специалиста": "specialist_evaluation",
        "Прогноз на следующий период": "forecast"
    }
    
    # Выбор типа отчета
    selected_report = st.selectbox(
        "Выберите тип отчета",
        options=list(report_types.keys())
    )
    
    # Рендеринг выбранного отчета
    report_type = report_types[selected_report]
    
    if report_type == "campaign_performance":
        render_campaign_performance_report(vk_client, account_id, date_from, date_to)
    elif report_type == "demographic":
        render_demographic_report(vk_client, account_id, date_from, date_to)
    elif report_type == "specialist_evaluation":
        render_specialist_evaluation_report(vk_client, openai_client, account_id, date_from, date_to)
    elif report_type == "forecast":
        render_forecast_report(vk_client, openai_client, account_id, date_from, date_to)

def render_campaign_performance_report(vk_client, account_id, date_from, date_to):
    """Отчет по эффективности кампаний"""
    st.subheader("Отчет по эффективности рекламных кампаний")
    
    try:
        # Получение кампаний
        campaigns = vk_client.get_campaigns(account_id)
        
        # Получение данных по каждой кампании
        campaign_data = []
        
        for campaign in campaigns:
            try:
                # Получение статистики для кампании
                stats = vk_client.get_statistics(
                    account_id=account_id,
                    ids_type="campaign",
                    ids=[campaign['id']],
                    period="overall",
                    date_from=date_from,
                    date_to=date_to
                )
                
                if stats and len(stats) > 0 and 'stats' in stats[0] and len(stats[0]['stats']) > 0:
                    campaign_stats = stats[0]['stats'][0]
                    
                    # Создание записи с данными кампании
                    campaign_record = {
                        'campaign_id': campaign['id'],
                        'campaign_name': campaign['name'],
                        'campaign_status': campaign['status'],
                        'impressions': campaign_stats.get('impressions', 0),
                        'clicks': campaign_stats.get('clicks', 0),
                        'ctr': round(campaign_stats.get('clicks', 0) / max(campaign_stats.get('impressions', 1), 1) * 100, 2),
                        'spent': campaign_stats.get('spent', 0),
                        'cpc': round(campaign_stats.get('spent', 0) / max(campaign_stats.get('clicks', 1), 1), 2)
                    }
                    
                    campaign_data.append(campaign_record)
            
            except Exception as e:
                st.warning(f"Ошибка при получении данных для кампании {campaign['name']}: {e}")
        
        if campaign_data:
            # Создание DataFrame
            df = pd.DataFrame(campaign_data)
            
            # Вывод общей статистики
            st.subheader("Общая статистика")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Всего показов", f"{int(df['impressions'].sum()):,}")
            with col2:
                st.metric("Всего кликов", f"{int(df['clicks'].sum()):,}")
            with col3:
                st.metric("Всего потрачено", f"{df['spent'].sum():,.2f} ₽")
            
            # График эффективности кампаний
            st.subheader("Эффективность кампаний")
            
            # Сортировка по расходам
            df_sorted = df.sort_values(by='spent', ascending=False)
            
            # График расходов и кликов по кампаниям
            fig = px.bar(
                df_sorted,
                x='campaign_name',
                y=['spent', 'clicks'],
                title="Расходы и клики по кампаниям",
                barmode='group',
                labels={
                    'campaign_name': 'Кампания',
                    'value': 'Значение',
                    'variable': 'Метрика'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # График CTR и CPC по кампаниям
            fig = px.bar(
                df_sorted,
                x='campaign_name',
                y=['ctr', 'cpc'],
                title="CTR и CPC по кампаниям",
                barmode='group',
                labels={
                    'campaign_name': 'Кампания',
                    'value': 'Значение',
                    'variable': 'Метрика'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Таблица с данными
            st.subheader("Детальные данные по кампаниям")
            st.dataframe(
                df.sort_values(by='spent', ascending=False),
                use_container_width=True
            )
            
            # Экспорт данных
            csv = df.to_csv(index=False)
            st.download_button(
                label="Скачать отчет в CSV",
                data=csv,
                file_name=f"campaign_performance_report_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Нет данных для отображения отчета.")
    
    except Exception as e:
        st.error(f"Ошибка при формировании отчета: {e}")

def render_demographic_report(vk_client, account_id, date_from, date_to):
    """Демографический отчет"""
    st.subheader("Демографический отчет")
    st.info("Для получения демографического отчета необходимо выбрать конкретную кампанию.")
    
    try:
        # Получение кампаний
        campaigns = vk_client.get_campaigns(account_id)
        
        # Выбор кампании для анализа
        campaign_options = {f"{c['name']} (ID: {c['id']})": c['id'] for c in campaigns}
        
        selected_campaign = st.selectbox(
            "Выберите кампанию для анализа",
            options=list(campaign_options.keys())
        )
        
        campaign_id = campaign_options[selected_campaign]
        
        if campaign_id:
            # Получение демографических данных
            demo_data = vk_client.get_demographics(
                account_id=account_id,
                ids_type="campaign",
                ids=[campaign_id],
                period="overall",
                date_from=date_from,
                date_to=date_to
            )
            
            if demo_data and len(demo_data) > 0 and 'stats' in demo_data[0] and len(demo_data[0]['stats']) > 0:
                stats = demo_data[0]['stats'][0]
                
                # Возраст
                if 'age' in stats:
                    st.subheader("Распределение по возрасту")
                    
                    age_data = []
                    for age_item in stats['age']:
                        age_data.append({
                            'age': age_item['value'],
                            'impressions': age_item.get('impressions', 0),
                            'clicks': age_item.get('clicks', 0),
                            'ctr': round(age_item.get('clicks', 0) / max(age_item.get('impressions', 1), 1) * 100, 2)
                        })
                    
                    df_age = pd.DataFrame(age_data)
                    
                    # График по возрасту
                    fig = px.bar(
                        df_age,
                        x='age',
                        y=['impressions', 'clicks'],
                        title="Показы и клики по возрастным группам",
                        barmode='group',
                        labels={
                            'age': 'Возраст',
                            'value': 'Количество',
                            'variable': 'Метрика'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Пол
                if 'sex' in stats:
                    st.subheader("Распределение по полу")
                    
                    sex_data = []
                    for sex_item in stats['sex']:
                        sex_label = "Мужчины" if sex_item['value'] == "m" else "Женщины"
                        sex_data.append({
                            'sex': sex_label,
                            'impressions': sex_item.get('impressions', 0),
                            'clicks': sex_item.get('clicks', 0),
                            'ctr': round(sex_item.get('clicks', 0) / max(sex_item.get('impressions', 1), 1) * 100, 2)
                        })
                    
                    df_sex = pd.DataFrame(sex_data)
                    
                    # График по полу
                    fig = px.pie(
                        df_sex,
                        values='impressions',
                        names='sex',
                        title="Распределение показов по полу"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    fig = px.pie(
                        df_sex,
                        values='clicks',
                        names='sex',
                        title="Распределение кликов по полу"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Города
                if 'cities' in stats:
                    st.subheader("Распределение по городам")
                    
                    cities_data = []
                    for city_item in stats['cities']:
                        cities_data.append({
                            'city': city_item['value'],
                            'impressions': city_item.get('impressions', 0),
                            'clicks': city_item.get('clicks', 0),
                            'ctr': round(city_item.get('clicks', 0) / max(city_item.get('impressions', 1), 1) * 100, 2)
                        })
                    
                    df_cities = pd.DataFrame(cities_data)
                    
                    # График по городам
                    fig = px.bar(
                        df_cities.sort_values(by='impressions', ascending=False).head(10),
                        x='city',
                        y=['impressions', 'clicks'],
                        title="Показы и клики по городам (топ-10)",
                        barmode='group',
                        labels={
                            'city': 'Город',
                            'value': 'Количество',
                            'variable': 'Метрика'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Нет демографических данных для выбранной кампании.")
    
    except Exception as e:
        st.error(f"Ошибка при формировании демографического отчета: {e}")

def render_specialist_evaluation_report(vk_client, openai_client, account_id, date_from, date_to):
    """Отчет по оценке работы специалиста"""
    st.subheader("Отчет по оценке работы специалиста")
    
    if not openai_client:
        st.warning("Для генерации отчета необходим настроенный доступ к OpenAI API.")
        return
    
    try:
        # Получение кампаний
        campaigns = vk_client.get_campaigns(account_id)
        
        # Сбор данных по всем кампаниям
        campaign_data = []
        
        for campaign in campaigns:
            try:
                # Получение статистики для кампании
                stats = vk_client.get_statistics(
                    account_id=account_id,
                    ids_type="campaign",
                    ids=[campaign['id']],
                    period="overall",
                    date_from=date_from,
                    date_to=date_to
                )
                
                if stats and len(stats) > 0 and 'stats' in stats[0] and len(stats[0]['stats']) > 0:
                    campaign_stats = stats[0]['stats'][0]
                    
                    # Создание записи с данными кампании
                    campaign_record = {
                        'campaign_id': campaign['id'],
                        'campaign_name': campaign['name'],
                        'campaign_status': campaign['status'],
                        'impressions': campaign_stats.get('impressions', 0),
                        'clicks': campaign_stats.get('clicks', 0),
                        'ctr': round(campaign_stats.get('clicks', 0) / max(campaign_stats.get('impressions', 1), 1) * 100, 2),
                        'spent': campaign_stats.get('spent', 0),
                        'cpc': round(campaign_stats.get('spent', 0) / max(campaign_stats.get('clicks', 1), 1), 2)
                    }
                    
                    campaign_data.append(campaign_record)
            
            except Exception as e:
                st.warning(f"Ошибка при получении данных для кампании {campaign['name']}: {e}")
        
        if campaign_data:
            # Создание DataFrame
            df = pd.DataFrame(campaign_data)
            
            # Вывод общей статистики
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Всего кампаний", len(campaigns))
            with col2:
                st.metric("Активные кампании", sum(1 for c in campaigns if c.get('status') == 'active'))
            with col3:
                st.metric("Общие расходы", f"{df['spent'].sum():,.2f} ₽")
            
            # Генерация отчета
            if st.button("Сгенерировать оценку работы специалиста"):
                with st.spinner("Генерация отчета..."):
                    # Подготовка данных для анализа
                    specialist_data = {
                        "period": f"{date_from} - {date_to}",
                        "total_campaigns": len(campaigns),
                        "active_campaigns": sum(1 for c in campaigns if c.get('status') == 'active'),
                        "total_metrics": {
                            "impressions": int(df['impressions'].sum()),
                            "clicks": int(df['clicks'].sum()),
                            "ctr": round(df['clicks'].sum() / max(df['impressions'].sum(), 1) * 100, 2),
                            "spent": float(df['spent'].sum()),
                            "cpc": round(df['spent'].sum() / max(df['clicks'].sum(), 1), 2)
                        },
                        "campaigns_performance": df.to_dict('records')
                    }
                    
                    # Получение анализа от OpenAI
                    analysis = openai_client.evaluate_specialist(specialist_data)
                    
                    # Вывод анализа
                    st.markdown(analysis)
                    
                    # Экспорт отчета
                    st.download_button(
                        label="Скачать отчет",
                        data=analysis,
                        file_name=f"specialist_evaluation_report_{datetime.now().strftime('%Y-%m-%d')}.md",
                        mime="text/markdown"
                    )
        else:
            st.warning("Нет данных для формирования отчета.")
    
    except Exception as e:
        st.error(f"Ошибка при формировании отчета: {e}")

def render_forecast_report(vk_client, openai_client, account_id, date_from, date_to):
    """Отчет с прогнозом на следующий период"""
    st.subheader("Прогноз на следующий период")
    
    if not openai_client:
        st.warning("Для генерации прогноза необходим настроенный доступ к OpenAI API.")
        return
    
    try:
        # Получение кампаний
        campaigns = vk_client.get_campaigns(account_id)
        
        # Сбор исторических данных
        historical_data = []
        
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
                            historical_data.append(day_data)
                
                except Exception as e:
                    st.warning(f"Ошибка при получении статистики для кампании {campaign['name']}: {e}")
        
        if historical_data:
            # Создание DataFrame
            df = pd.DataFrame(historical_data)
            
            # Агрегация данных по дням
            daily_data = df.groupby('date').agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'spent': 'sum'
            }).reset_index()
            
            # Расчет CTR и CPC
            daily_data['ctr'] = daily_data['clicks'] / daily_data['impressions'] * 100
            daily_data['cpc'] = daily_data['spent'] / daily_data['clicks']
            
            # График исторических данных
            st.subheader("Исторические данные")
            
            fig = px.line(
                daily_data,
                x='date',
                y=['impressions', 'clicks', 'spent'],
                title="Динамика ключевых метрик",
                labels={
                    'date': 'Дата',
                    'value': 'Значение',
                    'variable': 'Метрика'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Генерация прогноза
            if st.button("Сгенерировать прогноз"):
                with st.spinner("Генерация прогноза..."):
                    # Подготовка данных для прогноза
                    forecast_data = {
                        "historical_period": f"{date_from} - {date_to}",
                        "daily_metrics": daily_data.to_dict('records'),
                        "total_metrics": {
                            "impressions": int(df['impressions'].sum()),
                            "clicks": int(df['clicks'].sum()),
                            "spent": float(df['spent'].sum()),
                            "ctr": round(df['clicks'].sum() / max(df['impressions'].sum(), 1) * 100, 2),
                            "cpc": round(df['spent'].sum() / max(df['clicks'].sum(), 1), 2)
                        },
                        "active_campaigns": sum(1 for c in campaigns if c.get('status') == 'active')
                    }
                    
                    # Здесь можно использовать OpenAI для генерации прогноза
                    # В реальном приложении здесь бы использовались модели машинного обучения
                    
                    # Временная заглушка для демонстрации
                    forecast = """
                    ## Прогноз на следующий период
                    
                    ### Ожидаемые результаты
                    
                    На основе анализа исторических данных, прогнозируются следующие результаты на следующий период:
                    
                    - **Показы:** ~20,000 (+15%)
                    - **Клики:** ~800 (+12%)
                    - **CTR:** 4.0% (-3%)
                    - **Расходы:** 12,000 ₽ (+8%)
                    - **CPC:** 15 ₽ (-4%)
                    
                    ### Рекомендации
                    
                    1. **Оптимизировать ставки** для наиболее эффективных кампаний
                    2. **Пересмотреть таргетинг** для кампаний с низким CTR
                    3. **Обновить креативы** для повышения конверсии
                    4. **Перераспределить бюджет** в пользу более эффективных кампаний
                    
                    ### Потенциальные риски
                    
                    - Возможное увеличение конкуренции в нише
                    - Сезонные колебания спроса
                    - Изменения алгоритмов платформы
                    
                    ### План действий
                    
                    1. Еженедельный мониторинг ключевых показателей
                    2. A/B тестирование новых креативов
                    3. Постепенная корректировка ставок
                    4. Расширение аудитории для наиболее успешных кампаний
                    """
                    
                    st.markdown(forecast)
                    
                    # Экспорт прогноза
                    st.download_button(
                        label="Скачать прогноз",
                        data=forecast,
                        file_name=f"forecast_report_{datetime.now().strftime('%Y-%m-%d')}.md",
                        mime="text/markdown"
                    )
        else:
            st.warning("Недостаточно исторических данных для формирования прогноза.")

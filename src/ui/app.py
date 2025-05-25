"""
Основной файл приложения Streamlit для SergD_VK_ADS_control.
Предоставляет интерфейс для анализа рекламных кампаний ВКонтакте.
"""
import os
import sys
import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в путь импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Импорт модулей проекта
from src.api.vk_api_client import VKAdsApiClient
from src.api.openai_client import OpenAIClient
from src.ui.dashboard import render_dashboard
from src.ui.reports import render_reports

# Загрузка переменных окружения
load_dotenv()

# Настройка страницы
st.set_page_config(
    page_title="SergD VK ADS Control",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4CAF50;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2196F3;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #f5f5f5;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .big-number {
        font-size: 2rem;
        font-weight: bold;
        color: #333;
    }
    .footer {
        margin-top: 50px;
        text-align: center;
        color: #777;
    }
</style>
""", unsafe_allow_html=True)

# Функция для инициализации сессии
def init_session_state():
    """Инициализирует состояние сессии Streamlit"""
    if 'vk_client' not in st.session_state:
        try:
            st.session_state.vk_client = VKAdsApiClient()
        except Exception as e:
            st.session_state.vk_client = None
            st.error(f"Ошибка при инициализации VK API клиента: {e}")
    
    if 'openai_client' not in st.session_state:
        try:
            st.session_state.openai_client = OpenAIClient()
        except Exception as e:
            st.session_state.openai_client = None
            st.error(f"Ошибка при инициализации OpenAI клиента: {e}")
    
    if 'accounts' not in st.session_state:
        st.session_state.accounts = []
        if st.session_state.vk_client:
            try:
                st.session_state.accounts = st.session_state.vk_client.get_accounts()
            except Exception as e:
                st.error(f"Ошибка при получении рекламных аккаунтов: {e}")

# Боковая панель
def render_sidebar():
    """Отображает боковую панель приложения"""
    with st.sidebar:
        st.image("https://www.vkontakte.ru/images/logos/vk-logo.png", width=100)
        st.title("SergD VK ADS Control")
        
        # Выбор рекламного аккаунта
        if st.session_state.accounts:
            account_options = {f"{acc['account_name']} (ID: {acc['account_id']})": acc['account_id'] 
                              for acc in st.session_state.accounts}
            selected_account = st.selectbox(
                "Выберите рекламный аккаунт",
                options=list(account_options.keys())
            )
            st.session_state.selected_account_id = account_options[selected_account]
        else:
            st.warning("Не найдены рекламные аккаунты. Проверьте настройки API.")
            if st.button("Обновить"):
                if st.session_state.vk_client:
                    try:
                        st.session_state.accounts = st.session_state.vk_client.get_accounts()
                        st.success("Данные обновлены!")
                    except Exception as e:
                        st.error(f"Ошибка при получении рекламных аккаунтов: {e}")
        
        # Выбор периода анализа
        st.subheader("Период анализа")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Начало периода",
                value=datetime.date.today() - datetime.timedelta(days=30)
            )
        with col2:
            end_date = st.date_input(
                "Конец периода",
                value=datetime.date.today()
            )
        
        st.session_state.date_from = start_date.strftime("%Y-%m-%d")
        st.session_state.date_to = end_date.strftime("%Y-%m-%d")
        
        # Выбор раздела
        st.subheader("Навигация")
        pages = {
            "📊 Дашборд": "dashboard",
            "📈 Анализ кампаний": "campaigns",
            "👤 Анализ специалиста": "specialist",
            "📝 Отчеты": "reports",
            "⚙️ Настройки": "settings"
        }
        
        selected_page = st.radio("Выберите раздел", list(pages.keys()))
        st.session_state.current_page = pages[selected_page]
        
        # Нижняя часть сайдбара
        st.markdown("---")
        st.caption("© 2025 SergD_VK_ADS_control")
        st.caption("Разработчик: [Sergei Dyshkant](https://t.me/sergei_dyshkant)")

# Страница дашборда
def render_page_dashboard():
    """Отображает страницу дашборда"""
    st.markdown("<h1 class='main-header'>Дашборд эффективности рекламы</h1>", unsafe_allow_html=True)
    
    # Проверка доступа к API
    if not st.session_state.vk_client or not hasattr(st.session_state, 'selected_account_id'):
        st.warning("Необходимо настроить доступ к API ВКонтакте и выбрать рекламный аккаунт.")
        return
    
    try:
        # Получение бюджета аккаунта
        budget = st.session_state.vk_client.get_budget(st.session_state.selected_account_id)
        
        # Получение кампаний
        campaigns = st.session_state.vk_client.get_campaigns(st.session_state.selected_account_id)
        
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric(
                label="Бюджет аккаунта",
                value=f"{budget.get('budget', 0):,.2f} ₽"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric(
                label="Активные кампании",
                value=sum(1 for c in campaigns if c.get('status') == 'active')
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric(
                label="Всего кампаний",
                value=len(campaigns)
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col4:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric(
                label="Период анализа",
                value=f"{st.session_state.date_from} — {st.session_state.date_to}"
            )
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Загрузка аналитического дашборда
        render_dashboard(
            vk_client=st.session_state.vk_client,
            openai_client=st.session_state.openai_client,
            account_id=st.session_state.selected_account_id,
            date_from=st.session_state.date_from,
            date_to=st.session_state.date_to,
            campaigns=campaigns
        )
        
    except Exception as e:
        st.error(f"Ошибка при загрузке дашборда: {e}")

# Страница анализа кампаний
def render_page_campaigns():
    """Отображает страницу анализа кампаний"""
    st.markdown("<h1 class='main-header'>Анализ рекламных кампаний</h1>", unsafe_allow_html=True)
    
    # Проверка доступа к API
    if not st.session_state.vk_client or not hasattr(st.session_state, 'selected_account_id'):
        st.warning("Необходимо настроить доступ к API ВКонтакте и выбрать рекламный аккаунт.")
        return
    
    try:
        # Получение кампаний
        campaigns = st.session_state.vk_client.get_campaigns(st.session_state.selected_account_id)
        
        # Создание DataFrame с кампаниями
        df_campaigns = pd.DataFrame(campaigns)
        
        # Фильтры
        st.markdown("<h2 class='sub-header'>Фильтры</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.multiselect(
                "Статус кампании",
                options=df_campaigns['status'].unique().tolist(),
                default=df_campaigns['status'].unique().tolist()
            )
        
        with col2:
            search_term = st.text_input("Поиск по названию кампании")
        
        # Применение фильтров
        filtered_df = df_campaigns[df_campaigns['status'].isin(status_filter)]
        
        if search_term:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False)]
        
        # Вывод отфильтрованных кампаний
        st.markdown("<h2 class='sub-header'>Список кампаний</h2>", unsafe_allow_html=True)
        st.dataframe(
            filtered_df[['name', 'id', 'status', 'type', 'day_limit', 'all_limit']],
            use_container_width=True
        )
        
        # Выбор кампании для детального анализа
        if not filtered_df.empty:
            selected_campaign_id = st.selectbox(
                "Выберите кампанию для детального анализа",
                options=filtered_df['id'].tolist(),
                format_func=lambda x: filtered_df[filtered_df['id'] == x]['name'].iloc[0]
            )
            
            if selected_campaign_id:
                st.markdown("<h2 class='sub-header'>Детальный анализ кампании</h2>", unsafe_allow_html=True)
                
                # Получение статистики для выбранной кампании
                stats = st.session_state.vk_client.get_statistics(
                    account_id=st.session_state.selected_account_id,
                    ids_type="campaign",
                    ids=[selected_campaign_id],
                    period="day",
                    date_from=st.session_state.date_from,
                    date_to=st.session_state.date_to
                )
                
                # Вывод статистики
                if stats and len(stats) > 0 and 'stats' in stats[0]:
                    # Преобразование статистики в DataFrame
                    campaign_stats = []
                    for day_stat in stats[0]['stats']:
                        day_data = {
                            'date': day_stat['day'],
                            'impressions': day_stat.get('impressions', 0),
                            'clicks': day_stat.get('clicks', 0),
                            'ctr': round(day_stat.get('clicks', 0) / day_stat.get('impressions', 1) * 100, 2),
                            'spent': day_stat.get('spent', 0),
                            'cpc': round(day_stat.get('spent', 0) / day_stat.get('clicks', 1), 2)
                        }
                        campaign_stats.append(day_data)
                    
                    df_stats = pd.DataFrame(campaign_stats)
                    
                    # Графики
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Показы и клики")
                        st.line_chart(df_stats, x='date', y=['impressions', 'clicks'])
                    
                    with col2:
                        st.subheader("CTR и CPC")
                        st.line_chart(df_stats, x='date', y=['ctr', 'cpc'])
                    
                    # AI анализ кампании
                    if st.session_state.openai_client:
                        st.markdown("<h3 class='sub-header'>AI-анализ кампании</h3>", unsafe_allow_html=True)
                        
                        if st.button("Выполнить AI-анализ"):
                            with st.spinner("Выполняется анализ кампании..."):
                                # Подготовка данных для анализа
                                campaign_data = {
                                    "campaign_name": filtered_df[filtered_df['id'] == selected_campaign_id]['name'].iloc[0],
                                    "campaign_id": selected_campaign_id,
                                    "campaign_type": filtered_df[filtered_df['id'] == selected_campaign_id]['type'].iloc[0],
                                    "campaign_status": filtered_df[filtered_df['id'] == selected_campaign_id]['status'].iloc[0],
                                    "period": f"{st.session_state.date_from} - {st.session_state.date_to}",
                                    "metrics": {
                                        "impressions": df_stats['impressions'].sum(),
                                        "clicks": df_stats['clicks'].sum(),
                                        "ctr": round(df_stats['clicks'].sum() / df_stats['impressions'].sum() * 100, 2),
                                        "spent": df_stats['spent'].sum(),
                                        "cpc": round(df_stats['spent'].sum() / df_stats['clicks'].sum(), 2)
                                    }
                                }
                                
                                # Получение анализа от OpenAI
                                analysis = st.session_state.openai_client.analyze_campaign_performance(campaign_data)
                                
                                # Вывод анализа
                                st.markdown(analysis)
                else:
                    st.warning("Нет данных статистики для выбранной кампании.")
        else:
            st.info("Нет кампаний, соответствующих фильтрам.")
            
    except Exception as e:
        st.error(f"Ошибка при анализе кампаний: {e}")

# Страница анализа специалиста
def render_page_specialist():
    """Отображает страницу анализа работы специалиста по рекламе"""
    st.markdown("<h1 class='main-header'>Анализ работы специалиста по рекламе</h1>", unsafe_allow_html=True)
    
    # Проверка доступа к API
    if not st.session_state.vk_client or not hasattr(st.session_state, 'selected_account_id'):
        st.warning("Необходимо настроить доступ к API ВКонтакте и выбрать рекламный аккаунт.")
        return
    
    if not st.session_state.openai_client:
        st.warning("Необходимо настроить доступ к OpenAI API для анализа работы специалиста.")
        return
    
    try:
        # Получение кампаний
        campaigns = st.session_state.vk_client.get_campaigns(st.session_state.selected_account_id)
        
        # Общая статистика
        st.markdown("<h2 class='sub-header'>Общая статистика работы</h2>", unsafe_allow_html=True)
        
        # Сбор статистики по всем кампаниям
        all_stats = []
        for campaign in campaigns:
            try:
                stats = st.session_state.vk_client.get_statistics(
                    account_id=st.session_state.selected_account_id,
                    ids_type="campaign",
                    ids=[campaign['id']],
                    period="overall",
                    date_from=st.session_state.date_from,
                    date_to=st.session_state.date_to
                )
                
                if stats and len(stats) > 0 and 'stats' in stats[0] and len(stats[0]['stats']) > 0:
                    campaign_overall = stats[0]['stats'][0]
                    campaign_data = {
                        'campaign_id': campaign['id'],
                        'campaign_name': campaign['name'],
                        'campaign_status': campaign['status'],
                        'impressions': campaign_overall.get('impressions', 0),
                        'clicks': campaign_overall.get('clicks', 0),
                        'ctr': round(campaign_overall.get('clicks', 0) / campaign_overall.get('impressions', 1) * 100, 2),
                        'spent': campaign_overall.get('spent', 0),
                        'cpc': round(campaign_overall.get('spent', 0) / campaign_overall.get('clicks', 1), 2)
                    }
                    all_stats.append(campaign_data)
            except Exception as e:
                st.warning(f"Не удалось получить статистику для кампании {campaign['name']}: {e}")
        
        if all_stats:
            df_all_stats = pd.DataFrame(all_stats)
            
            # Общие метрики
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric(
                    label="Всего показов",
                    value=f"{df_all_stats['impressions'].sum():,}"
                )
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col2:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric(
                    label="Всего кликов",
                    value=f"{df_all_stats['clicks'].sum():,}"
                )
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col3:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric(
                    label="Средний CTR",
                    value=f"{round(df_all_stats['clicks'].sum() / df_all_stats['impressions'].sum() * 100, 2)}%"
                )
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col4:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric(
                    label="Общие расходы",
                    value=f"{df_all_stats['spent'].sum():,.2f} ₽"
                )
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Таблица с результатами кампаний
            st.markdown("<h2 class='sub-header'>Результаты кампаний</h2>", unsafe_allow_html=True)
            st.dataframe(
                df_all_stats.sort_values(by='spent', ascending=False),
                use_container_width=True
            )
            
            # AI анализ работы специалиста
            st.markdown("<h2 class='sub-header'>AI-анализ работы специалиста</h2>", unsafe_allow_html=True)
            
            if st.button("Выполнить анализ работы специалиста"):
                with st.spinner("Выполняется анализ работы специалиста..."):
                    # Подготовка данных для анализа
                    specialist_data = {
                        "period": f"{st.session_state.date_from} - {st.session_state.date_to}",
                        "total_campaigns": len(campaigns),
                        "active_campaigns": sum(1 for c in campaigns if c.get('status') == 'active'),
                        "total_metrics": {
                            "impressions": int(df_all_stats['impressions'].sum()),
                            "clicks": int(df_all_stats['clicks'].sum()),
                            "ctr": round(df_all_stats['clicks'].sum() / df_all_stats['impressions'].sum() * 100, 2),
                            "spent": float(df_all_stats['spent'].sum()),
                            "cpc": round(df_all_stats['spent'].sum() / df_all_stats['clicks'].sum(), 2)
                        },
                        "campaigns_performance": df_all_stats.to_dict('records')
                    }
                    
                    # Получение анализа от OpenAI
                    analysis = st.session_state.openai_client.evaluate_specialist(specialist_data)
                    
                    # Вывод анализа
                    st.markdown(analysis)
        else:
            st.warning("Нет данных статистики для анализа работы специалиста.")
            
    except Exception as e:
        st.error(f"Ошибка при анализе работы специалиста: {e}")

# Страница отчетов
def render_page_reports():
    """Отображает страницу отчетов"""
    st.markdown("<h1 class='main-header'>Отчеты</h1>", unsafe_allow_html=True)
    
    # Проверка доступа к API
    if not st.session_state.vk_client or not hasattr(st.session_state, 'selected_account_id'):
        st.warning("Необходимо настроить доступ к API ВКонтакте и выбрать рекламный аккаунт.")
        return
    
    # Загрузка модуля отчетов
    render_reports(
        vk_client=st.session_state.vk_client,
        openai_client=st.session_state.openai_client,
        account_id=st.session_state.selected_account_id,
        date_from=st.session_state.date_from,
        date_to=st.session_state.date_to
    )

# Страница настроек
def render_page_settings():
    """Отображает страницу настроек"""
    st.markdown("<h1 class='main-header'>Настройки</h1>", unsafe_allow_html=True)
    
    # Настройки API ВКонтакте
    st.markdown("<h2 class='sub-header'>Настройки API ВКонтакте</h2>", unsafe_allow_html=True)
    
    vk_token = st.text_input(
        "Токен доступа VK API",
        value=os.getenv('VK_ACCESS_TOKEN', ''),
        type="password"
    )
    
    # Настройки API OpenAI
    st.markdown("<h2 class='sub-header'>Настройки API OpenAI</h2>", unsafe_allow_html=True)
    
    openai_key = st.text_input(
        "API ключ OpenAI",
        value=os.getenv('OPENAI_API_KEY', ''),
        type="password"
    )
    
    openai_model = st.selectbox(
        "Модель OpenAI",
        options=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0
    )
    
    # Кнопка сохранения настроек
    if st.button("Сохранить настройки"):
        # В реальном приложении здесь бы обновлялся .env файл
        # Для демо просто обновим клиенты в сессии
        try:
            if vk_token:
                st.session_state.vk_client = VKAdsApiClient(access_token=vk_token)
                st.session_state.accounts = st.session_state.vk_client.get_accounts()
            
            if openai_key:
                st.session_state.openai_client = OpenAIClient(api_key=openai_key, model=openai_model)
            
            st.success("Настройки успешно сохранены!")
            
        except Exception as e:
            st.error(f"Ошибка при сохранении настроек: {e}")
    
    # Инструкции по получению API ключей
    with st.expander("Как получить токен доступа VK API"):
        st.markdown("""
        ### Получение токена доступа ВКонтакте
        
        1. Перейдите в рекламный кабинет ВКонтакте: [ads.vk.com](https://ads.vk.com/)
        2. Проверьте, что заполнены реквизиты:
           - Для юридических лиц — в разделе «Бюджет» (должны быть проверены модерацией)
           - Для физических лиц — в разделе «Настройки»
        3. Перейдите в раздел «Настройки» → «Доступ к API» и нажмите «Запросить доступ к API»
        4. Заполните ФИО и контакты сотрудника, отвечающего за использование API
        5. Нажмите «Запросить доступ»
        6. В разделе «Настройки» вы получите:
           - `client_id` — идентификатор приложения
           - `client_secret` — секрет приложения (сохраните его, повторно запросить невозможно)
        7. Для получения токена доступа выполните шаги согласно [официальной инструкции](https://ads.vk.com/doc/api/info/%D0%90%D0%B2%D1%82%D0%BE%D1%80%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F%20%D0%B2%20API)
        """)
    
    with st.expander("Как получить API ключ OpenAI"):
        st.markdown("""
        ### Получение API ключа OpenAI
        
        1. Зарегистрируйтесь на [платформе OpenAI](https://platform.openai.com/)
        2. Перейдите в раздел API Keys: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
        3. Нажмите "Create new secret key"
        4. Скопируйте и сохраните полученный ключ (его нельзя будет просмотреть снова)
        """)

# Главная функция приложения
def main():
    """Основная функция приложения"""
    # Инициализация состояния сессии
    init_session_state()
    
    # Отображение боковой панели
    render_sidebar()
    
    # Отображение выбранной страницы
    if st.session_state.current_page == "dashboard":
        render_page_dashboard()
    elif st.session_state.current_page == "campaigns":
        render_page_campaigns()
    elif st.session_state.current_page == "specialist":
        render_page_specialist()
    elif st.session_state.current_page == "reports":
        render_page_reports()
    elif st.session_state.current_page == "settings":
        render_page_settings()
    
    # Подвал
    st.markdown("""
    <div class="footer">
        SergD_VK_ADS_control © 2025 | Разработчик: <a href="https://t.me/sergei_dyshkant">Sergei Dyshkant</a>
    </div>
    """, unsafe_allow_html=True)

# Запуск приложения
if __name__ == "__main__":
    main()

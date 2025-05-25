"""
Клиент для работы с рекламным API ВКонтакте.
Отвечает за авторизацию и взаимодействие с API.
"""
import os
import requests
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)

class VKAdsApiClient:
    """
    Клиент для работы с рекламным API ВКонтакте.
    Обеспечивает доступ к методам для работы с рекламными кампаниями, объявлениями и статистикой.
    """
    
    API_VERSION = '5.131'
    API_BASE_URL = 'https://api.vk.com/method/'
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Инициализация клиента VK API.
        
        Args:
            access_token: Токен доступа к API ВКонтакте. Если не указан, берется из переменных окружения.
        """
        load_dotenv()
        self.access_token = access_token or os.getenv('VK_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError('Не указан токен доступа к API ВКонтакте. Укажите его в .env файле или при создании клиента.')
        
        logger.info("VK API клиент инициализирован")
    
    def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполняет запрос к API ВКонтакте.
        
        Args:
            method: Имя метода API
            params: Параметры запроса
            
        Returns:
            Результат запроса в виде словаря
        """
        url = f"{self.API_BASE_URL}{method}"
        params.update({
            'access_token': self.access_token,
            'v': self.API_VERSION
        })
        
        logger.debug(f"Выполняется запрос к {method} с параметрами: {params}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                error_msg = f"Ошибка API VK: {data['error']['error_msg']}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            return data['response'] if 'response' in data else data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к API VK: {e}")
            raise
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Получает список рекламных аккаунтов пользователя.
        
        Returns:
            Список рекламных аккаунтов
        """
        return self._make_request('ads.getAccounts', {})
    
    def get_campaigns(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Получает список кампаний для указанного рекламного аккаунта.
        
        Args:
            account_id: Идентификатор рекламного аккаунта
            
        Returns:
            Список рекламных кампаний
        """
        return self._make_request('ads.getCampaigns', {'account_id': account_id})
    
    def get_ads(self, account_id: int, campaign_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Получает список объявлений.
        
        Args:
            account_id: Идентификатор рекламного аккаунта
            campaign_ids: Список идентификаторов кампаний (если None, то для всех кампаний)
            
        Returns:
            Список объявлений
        """
        params = {'account_id': account_id}
        if campaign_ids:
            params['campaign_ids'] = ','.join(map(str, campaign_ids))
        
        return self._make_request('ads.getAds', params)
    
    def get_statistics(self, account_id: int, ids_type: str, ids: List[int], 
                      period: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """
        Получает статистику показателей эффективности для объявлений, кампаний или клиентов.
        
        Args:
            account_id: Идентификатор рекламного аккаунта
            ids_type: Тип запрашиваемых объектов (ad, campaign, client, office)
            ids: Список идентификаторов объектов
            period: Период статистики (day, week, month, year, overall)
            date_from: Начальная дата в формате YYYY-MM-DD
            date_to: Конечная дата в формате YYYY-MM-DD
            
        Returns:
            Статистика для указанных объектов
        """
        params = {
            'account_id': account_id,
            'ids_type': ids_type,
            'ids': ','.join(map(str, ids)),
            'period': period,
            'date_from': date_from,
            'date_to': date_to
        }
        
        return self._make_request('ads.getStatistics', params)
    
    def get_budget(self, account_id: int) -> Dict[str, Any]:
        """
        Получает текущий бюджет рекламного аккаунта.
        
        Args:
            account_id: Идентификатор рекламного аккаунта
            
        Returns:
            Информация о бюджете
        """
        return self._make_request('ads.getBudget', {'account_id': account_id})
    
    def get_demographics(self, account_id: int, ids_type: str, ids: List[int], 
                        period: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """
        Получает демографическую статистику для указанных объявлений или кампаний.
        
        Args:
            account_id: Идентификатор рекламного аккаунта
            ids_type: Тип запрашиваемых объектов (ad, campaign)
            ids: Список идентификаторов объектов
            period: Период статистики (day, month, overall)
            date_from: Начальная дата в формате YYYY-MM-DD
            date_to: Конечная дата в формате YYYY-MM-DD
            
        Returns:
            Демографическая статистика
        """
        params = {
            'account_id': account_id,
            'ids_type': ids_type,
            'ids': ','.join(map(str, ids)),
            'period': period,
            'date_from': date_from,
            'date_to': date_to
        }
        
        return self._make_request('ads.getDemographics', params)


# Пример использования
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Создание клиента
        client = VKAdsApiClient()
        
        # Получение списка аккаунтов
        accounts = client.get_accounts()
        print(f"Найдено {len(accounts)} рекламных аккаунтов")
        
        if accounts:
            account_id = accounts[0]['account_id']
            
            # Получение кампаний
            campaigns = client.get_campaigns(account_id)
            print(f"Найдено {len(campaigns)} рекламных кампаний")
            
            # Получение бюджета
            budget = client.get_budget(account_id)
            print(f"Бюджет аккаунта: {budget}")
            
    except Exception as e:
        print(f"Произошла ошибка: {e}")

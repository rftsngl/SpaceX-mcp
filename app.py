"""SpaceX MCP - Ana uygulama modülü."""

import requests
import json
from typing import Dict, Any, Optional

class SpaceXAPI:
    """SpaceX API ile iletişim kuran sınıf."""
    
    BASE_URL = "https://api.spacexdata.com/v5"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
    
    def get_latest_launch(self) -> Optional[Dict[str, Any]]:
        """En son fırlatma bilgilerini çeker."""
        try:
            response = self.session.get(f"{self.BASE_URL}/launches/latest")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API çağrısı başarısız: {e}")
            return None
    
    def get_upcoming_launches(self, limit: int = 5) -> Optional[Dict[str, Any]]:
        """Yaklaşan fırlatmaları çeker."""
        try:
            response = self.session.get(f"{self.BASE_URL}/launches/upcoming", 
                                      params={"limit": limit})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API çağrısı başarısız: {e}")
            return None
    
    def get_company_info(self) -> Optional[Dict[str, Any]]:
        """SpaceX şirket bilgilerini çeker."""
        try:
            response = self.session.get(f"{self.BASE_URL}/company")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API çağrısı başarısız: {e}")
            return None

def format_launch_data(launch_data: Dict[str, Any]) -> str:
    """Fırlatma verilerini okunabilir formata dönüştürür."""
    if not launch_data:
        return "Fırlatma verisi bulunamadı."
    
    flight_number = launch_data.get('flight_number', 'Bilinmiyor')
    name = launch_data.get('name', 'Bilinmiyor')
    date = launch_data.get('date_utc', 'Bilinmiyor')
    success = launch_data.get('success')
    details = launch_data.get('details', 'Detay yok')
    
    status = "Başarılı" if success else "Başarısız" if success is False else "Devam ediyor"
    
    return f"""🚀 SpaceX Fırlatma Bilgisi

📊 Uçuş Numarası: {flight_number}
🎯 Misyon Adı: {name}
📅 Tarih: {date}
✅ Durum: {status}
📝 Detaylar: {details}
"""

# Global SpaceX API instance
spacex_api = SpaceXAPI() 
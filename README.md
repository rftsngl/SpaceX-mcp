# SpaceX MCP

SpaceX API verilerini MCP (Model Context Protocol) üzerinden sunan dinamik server uygulaması.

## 📋 Özellikler

- **Dinamik API çağrıları** - SpaceX API'den canlı veri çeker
- **MCP Protocol desteği** - STDIO üzerinden MCP protokolü
- **Çoklu tool desteği** - En son fırlatma, yaklaşan fırlatmalar ve şirket bilgileri
- **Standart MCP mimarisi** - Modern MCP server implementasyonu

## 🚀 Kurulum

1. Repoyu klonlayın:
```bash
git clone https://github.com/rftsngl/SpaceX-mcp.git
cd SpaceX-mcp
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

## 📖 Kullanım

### Lokal çalıştırma
```bash
python server.py
```

### Docker ile çalıştırma
```bash
docker build -t spacex-mcp .
docker run spacex-mcp
```

### Smithery ile deployment
```bash
smithery deploy
```

## 🛠️ Mevcut Tools

1. **get_latest_launch** - En son SpaceX fırlatma bilgilerini alır
2. **get_upcoming_launches** - Yaklaşan fırlatmaları listeler (limit parametresi ile)
3. **get_company_info** - SpaceX şirket bilgilerini getirir

## 📁 Proje Yapısı

```
spacex-mcp/
├── app.py              # Ana uygulama logic'i ve SpaceX API sınıfı
├── server.py           # MCP server implementasyonu (STDIO)
├── requirements.txt    # Python bağımlılıkları
├── Dockerfile         # Konteyner konfigürasyonu
├── smithery.yaml      # Smithery deployment konfigürasyonu
└── README.md          # Bu dosya
```

## 🔧 Gereksinimler

- Python 3.9+
- requests
- Internet bağlantısı (SpaceX API için)

## 📝 MCP Protocol

Bu server MCP (Model Context Protocol) STDIO implementasyonu kullanır:
- Input: JSONRPC 2.0 formatında stdin
- Output: JSONRPC 2.0 formatında stdout
- Tools: SpaceX API endpoint'leri

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

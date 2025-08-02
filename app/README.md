# ZalupiX - Google Sheets Events API

API для работы с событиями из Google Sheets с поддержкой Telegram бота.

## Архитектура

```
API Layer (Controllers)
    ↓
Service Layer (SchedulerService) ← Бизнес-логика
    ↓
Data Layer (GridScheduler) ← Доступ к данным
    ↓
External API (Google Sheets)
```

## Запуск

### Полный запуск (API + Telegram бот)
```bash
python3 main.py
```

### Только API сервер (для разработки)
```bash
python3 run_api.py
```

### Через uvicorn напрямую
```bash
python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /health` - Проверка состояния API
- `GET /schedule` - Получение расписания событий (с кэшированием)
- `GET /schedule?refresh=true` - Принудительное обновление кэша

## Документация API

После запуска сервера доступна по адресу: http://localhost:8000/docs

## Graceful Shutdown

Приложение поддерживает graceful shutdown при получении сигналов SIGINT или SIGTERM.
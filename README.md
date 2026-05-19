# Планирование производства — серверная версия

Веб-приложение для планирования швейного производства. Работает в браузере, данные хранятся в SQLite на сервере и доступны всем сотрудникам одновременно.

---

## Как это работает

- Все открывают одну ссылку в браузере — `http://адрес-сервера:8000/`
- Данные хранятся в SQLite на сервере, а не у каждого локально
- `Plan.html` не изменён — Django при раздаче незаметно вставляет скрипт синхронизации

---

## Требования к серверу

- Linux (Ubuntu, Debian, CentOS — любой)
- Python 3.10 или новее
- Доступ по SSH
- Открытый порт 8000 (или настроить nginx — см. ниже)

Проверить версию Python:
```bash
python3 --version
```

---

## Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/gurevivan/plan_platform.git
cd plan_platform
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 3. Создать базу данных

```bash
venv/bin/python manage.py makemigrations app
venv/bin/python manage.py migrate
```

После этого в папке появится файл `db.sqlite3` — это и есть база данных.

### 4. Запустить сервер

```bash
venv/bin/python manage.py runserver 0.0.0.0:8000
```

Открыть в браузере: `http://IP-адрес-сервера:8000/`

---

## Запуск в фоне (чтобы не останавливалось при закрытии SSH)

### Вариант А — screen (простой)

```bash
# Установить screen если нет
sudo apt install screen   # Ubuntu/Debian
sudo yum install screen   # CentOS

# Запустить в фоне
screen -S plan
cd plan_platform
venv/bin/python manage.py runserver 0.0.0.0:8000

# Отключиться от screen (сервер продолжает работать)
# Нажать: Ctrl+A, потом D

# Вернуться к логам
screen -r plan
```

### Вариант Б — systemd (надёжный, запускается автоматически при перезагрузке)

Создать файл сервиса:
```bash
sudo nano /etc/systemd/system/plan.service
```

Вставить содержимое (заменить `/home/ваш_пользователь/plan_platform` на реальный путь):
```ini
[Unit]
Description=Plan Platform
After=network.target

[Service]
User=ваш_пользователь
WorkingDirectory=/home/ваш_пользователь/plan_platform
ExecStart=/home/ваш_пользователь/plan_platform/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Запустить:
```bash
sudo systemctl daemon-reload
sudo systemctl enable plan      # автозапуск при перезагрузке
sudo systemctl start plan       # запустить сейчас
sudo systemctl status plan      # проверить статус
```

Посмотреть логи:
```bash
sudo journalctl -u plan -f
```

---

## Настройка nginx (если нужен порт 80 вместо 8000)

Установить nginx:
```bash
sudo apt install nginx   # Ubuntu/Debian
```

Создать конфиг:
```bash
sudo nano /etc/nginx/sites-available/plan
```

Вставить:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Подключить и перезапустить:
```bash
sudo ln -s /etc/nginx/sites-available/plan /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Теперь сайт открывается по `http://IP-адрес-сервера/` без указания порта.

---

## Обновление приложения

Когда вышла новая версия `Plan.html`:

```bash
cd plan_platform
git pull
sudo systemctl restart plan   # или: screen -r plan → Ctrl+C → снова запустить
```

Данные в `db.sqlite3` при обновлении не затрагиваются.

---

## Резервная копия данных

База данных — это один файл `db.sqlite3`. Чтобы сделать резервную копию:

```bash
cp db.sqlite3 db.sqlite3.backup-$(date +%Y-%m-%d)
```

Можно поставить в cron чтобы делалось автоматически каждый день:
```bash
crontab -e
```
Добавить строку:
```
0 3 * * * cp /home/ваш_пользователь/plan_platform/db.sqlite3 /home/ваш_пользователь/backups/db-$(date +\%Y-\%m-\%d).sqlite3
```

---

## Перенос данных из старой версии (если использовали Plan.html локально)

Если раньше работали с `Plan.html` напрямую и хотите перенести данные на сервер:

1. Открыть старый `Plan.html` в браузере
2. Зайти в приложение → найти кнопку **Экспорт** → скачать `data.json`
3. Открыть новый сервер в браузере: `http://адрес-сервера:8000/`
4. Зайти в приложение → **Импорт** → выбрать скачанный `data.json`

После импорта данные окажутся в SQLite и будут доступны всем.

---

## Структура проекта

```
plan_platform/
├── Plan.html              # Основное приложение (не изменяется)
├── manage.py              # Django точка входа
├── requirements.txt       # Python зависимости
├── plan_project/
│   ├── settings.py        # Настройки Django
│   └── urls.py            # Маршруты
└── app/
    ├── models.py          # Модель хранения данных (SQLite)
    ├── views.py           # Логика раздачи страницы и API
    └── migrations/        # Миграции базы данных
```

---

## Частые проблемы

**Ошибка "Address already in use"**
```bash
# Найти и остановить процесс занявший порт 8000
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Страница не открывается с другого компьютера**
- Проверить что порт 8000 открыт в firewall:
```bash
sudo ufw allow 8000   # Ubuntu
sudo firewall-cmd --add-port=8000/tcp --permanent && sudo firewall-cmd --reload   # CentOS
```

**Данные не сохраняются**
- Открыть консоль браузера (F12 → Console) и проверить нет ли ошибок
- Проверить логи сервера в терминале

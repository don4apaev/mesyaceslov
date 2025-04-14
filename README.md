# Месяцеслов

Проект реализует бота для Telegram и VK, который ежедневно выполняет рассылку по подписавшимся пользователям, а так же делает размещение в группе/канале с информацией о дне согласно месяцеслову.

Источники:
- Некрылова, А.Ф. Русский традиционный календарь на каждый день и для каждого дома. - СПб.: Азбука-классика, 2007.

## Установка

Приложение предполагает исполнение в виртуальной среде pipenv:

```console
pipenv install
```

## Запуск

Приложение использует информацию из переменных окружения:
- `VK_BOT_MS_TOKEN` - токен бота для VK;
- `VK_API_MS_TOKEN` и `VK_MS_GROUP_ID` - токен и ID группы в VK;
- `TG_MS_TOKEN` - токен бота в Telegram; он же используется для управления каналом.

При первом запуске создаётся файл базы данных пользователей `users.db`. В нём вручную надо указать админа, выставив ему поле `admin` в `True`. Для настройки времени публикации в группе\канале используется запись с `id` 0, и соответствующим `type` (0 для VK и 1 для Telegram). Их так же надо создать в ручную.

```console
pipenv run python main.py
```
# Media Controller

Учебный frontend-heavy Django-проект: мультимедийный плеер с плейлистами, глобальным player bar, persistent audio и анимированной виниловой пластинкой.

## Стек

- Python
- Django
- SQLite
- Django templates
- HTML
- CSS
- JavaScript

## Возможности

- список треков и плейлистов;
- отдельные страницы плейлистов;
- глобальный нижний player bar;
- непрерывное воспроизведение при переходах внутри сайта;
- сохранение текущего трека, очереди, громкости и прогресса в `localStorage`;
- виниловая анимация, связанная с состоянием плеера;
- поиск по названию и исполнителю;
- адаптивная тёмная тема;
- Django admin для локального редактирования треков и плейлистов;
- статический экспорт для GitHub Pages.

## Локальный запуск

```powershell
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_tracks
python manage.py runserver
```

Открыть приложение:

```text
http://127.0.0.1:8000/
```

## Суперпользователь

```powershell
python manage.py createsuperuser
```

Админка:

```text
http://127.0.0.1:8000/admin/
```

## Аудиофайлы

Файлы лежат в:

```text
media/audio/
```

Чтобы добавить новый трек локально:

1. Положите `.mp3` в `media/audio/`.
2. Откройте Django admin.
3. Создайте запись `Track`.
4. Укажите `title`, `artist` и `audio_file`.

Для GitHub Pages аудиофайлы должны быть закоммичены в репозиторий, потому что Pages отдаёт только статические файлы.

## Демо-данные

```powershell
python manage.py seed_tracks
```

Команда создаёт записи для треков, которые уже лежат в `media/audio/`, и удаляет старые учебные заглушки без файлов.

## Статическая сборка

GitHub Pages не запускает Python и Django backend. Поэтому проект публикуется как статический сайт: Django используется только как генератор HTML из templates.

Локальная сборка:

```powershell
python manage.py migrate
python manage.py seed_tracks
python manage.py export_static_site --output site --base-path /REPOSITORY/
python scripts/copy-404.py
```

Результат появится в папке:

```text
site/
```

Внутри будут:

- `index.html`;
- `404.html`;
- `playlist/<id>/index.html`;
- `static/`;
- `media/`;
- `.nojekyll`.

## GitHub Pages

Проект настроен для автоматического деплоя через GitHub Actions.

Workflow:

```text
.github/workflows/deploy.yml
```

Он выполняет:

1. `checkout`;
2. установку Python;
3. `pip install -r requirements.txt`;
4. `python manage.py migrate --noinput`;
5. `python manage.py seed_tracks`;
6. `python manage.py export_static_site`;
7. загрузку `site/` как Pages artifact;
8. деплой через `actions/deploy-pages`.

После push в `main` сайт будет доступен по адресу:

```text
https://USERNAME.github.io/REPOSITORY/
```

В настройках репозитория GitHub нужно включить Pages и выбрать source: **GitHub Actions**.

## Ограничения GitHub Pages

На GitHub Pages нет Django backend, поэтому:

- воспроизведение музыки работает;
- поиск работает;
- переходы между сгенерированными страницами работают;
- player bar и persistent audio работают;
- винил работает;
- созданные на момент сборки плейлисты отображаются;
- создание, удаление и редактирование плейлистов через формы доступно только в локальной Django-версии.

В статической версии формы не отправляются на backend; интерфейс покажет поясняющее сообщение.

## Структура

```text
media_player_project/
├── manage.py
├── media_player_project/
│   ├── settings.py
│   └── urls.py
├── player/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── forms.py
│   ├── management/
│   │   └── commands/
│   │       ├── seed_tracks.py
│   │       └── export_static_site.py
│   ├── templates/player/
│   └── static/player/
├── media/audio/
├── scripts/copy-404.py
└── .github/workflows/deploy.yml
```

## Проверка

```powershell
python manage.py test
python manage.py export_static_site --output site --base-path /REPOSITORY/
```

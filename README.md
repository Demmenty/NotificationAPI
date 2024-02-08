# Notification Management API

Сервис API для управления рассылками.

## Technologies

Python, Django Rest Framework, PostgreSQL, Celery, Redis, Docker 

## Installation

- create .env file in root with your settings according to .env.example
- install docker

- build and run application with its dependencies
```
docker-compose up -d --build
```

- create admin if needed
```
docker exec -it api python manage.py createsuperuser
```

### Completed additions

3. подготовить docker-compose для запуска всех сервисов проекта одной командой
5. сделать так, чтобы по адресу /docs/ открывалась страница со Swagger UI и в нём отображалось описание разработанного API.
6. реализовать администраторский Web UI для управления рассылками и получения статистики по отправленным сообщениям
7. обеспечить интеграцию с внешним OAuth2 сервисом авторизации для административного интерфейса.
8. реализовать дополнительный сервис, который раз в сутки отправляет статистику по обработанным рассылкам на email
9. Необходимо организовать обработку ошибок и откладывание запросов при неуспехе для последующей повторной отправки.
12. обеспечить подробное логирование на всех этапах обработки запросов, чтобы при эксплуатации была возможность найти в логах всю информацию по id рассылки, id сообщения, id клиента

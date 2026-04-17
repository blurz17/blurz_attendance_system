from celery import Celery
from asgiref.sync import async_to_sync
from core.services.mailserver.service import send_email, mail

app = Celery()

app.config_from_object('core.services.celery.celery_config')


@app.task()
def bg_send_mail(rec: list[str], sub: str, html_path: str, data_var: dict = None):
    message = send_email(
        recepients=rec,
        subject=sub,
        html_message_path=html_path,
        data_variables=data_var,
    )
    async_to_sync(mail.send_message)(message)
    print("Email is sent")

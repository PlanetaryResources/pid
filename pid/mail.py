# -*- coding: utf-8 -*-

from flask import current_app
from flask_login import current_user
from flask_mail import Message
from pid.extensions import celery, mail
from pid.utils import check_connection


def send_email(subject, recipients, text_body, html_body, sender=None):
    smtp_server_reachable = check_connection(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
    if current_app.config['ENV'] is 'dev':
        # If in dev, overwrite recipient with DEV_EMAIL setting
        recipients = [current_app.config['DEV_EMAIL']]
    if smtp_server_reachable:
        # TODO: Find a better solution for this. Should store emails in a queue in DB maybe
        send_email_via_celery.delay(subject, recipients, text_body, html_body, sender=sender)


@celery.task
def send_email_via_celery(subject, recipients, text_body, html_body, sender=None):
    if sender:
        msg = Message(subject, sender=sender, recipients=recipients)
    else:
        msg = Message(subject, recipients=recipients)  # Use default sender
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

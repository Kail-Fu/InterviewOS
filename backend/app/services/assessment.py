import asyncio
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import Settings
from app.services.aws_clients import s3_client, ses_client
from app.services.email_templates import assessment_invite_email, assessment_reminder_email


def generate_assessment_download_link(settings: Settings) -> str:
    if settings.storage_provider == "local":
        return f"{settings.app_base_url}/assets/{settings.local_assessment_filename}"

    s3 = s3_client(settings)
    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.assessment_bucket,
            "Key": settings.assessment_object_key,
        },
        ExpiresIn=settings.presigned_url_expiration_seconds,
    )


def _sender_email(settings: Settings) -> str:
    return settings.ses_from_email or settings.email_from


def _send_via_console(to_email: str, subject: str, body: str) -> None:
    print("\n=== InterviewOS Email (console provider) ===")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(body)
    print("=== End Email ===\n")


def _send_via_smtp(to_email: str, subject: str, html_body: str, text_body: str, settings: Settings) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _sender_email(settings)
    msg["To"] = to_email
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password or "")
            server.send_message(msg)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password or "")
        server.send_message(msg)


def send_assessment_email(
    to_email: str,
    instructions_link: str,
    settings: Settings,
    *,
    is_resend: bool = False,
) -> None:
    content = assessment_invite_email(instructions_link=instructions_link, is_resend=is_resend)

    if settings.email_provider == "console":
        _send_via_console(to_email, content.subject, content.text_body)
        return

    if settings.email_provider == "smtp":
        _send_via_smtp(to_email, content.subject, content.html_body, content.text_body, settings)
        return

    msg = MIMEMultipart()
    msg["Subject"] = content.subject
    msg["From"] = _sender_email(settings)
    msg["To"] = to_email
    msg.attach(MIMEText(content.html_body, "html"))

    ses = ses_client(settings)
    ses.send_raw_email(
        Source=_sender_email(settings),
        Destinations=[to_email],
        RawMessage={"Data": msg.as_string()},
    )


def send_reminder_email(to_email: str, settings: Settings) -> None:
    content = assessment_reminder_email()

    if settings.email_provider == "console":
        _send_via_console(to_email, content.subject, content.text_body)
        return

    if settings.email_provider == "smtp":
        _send_via_smtp(to_email, content.subject, content.html_body, content.text_body, settings)
        return

    ses = ses_client(settings)
    ses.send_email(
        Source=_sender_email(settings),
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": content.subject},
            "Body": {
                "Text": {
                    "Data": content.text_body
                }
            },
        },
    )


async def schedule_reminder_email(to_email: str, settings: Settings) -> None:
    await asyncio.sleep(settings.reminder_delay_seconds)
    send_reminder_email(to_email, settings)

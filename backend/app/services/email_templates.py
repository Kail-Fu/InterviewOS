from dataclasses import dataclass


@dataclass(frozen=True)
class EmailContent:
    subject: str
    html_body: str
    text_body: str


def _layout(title: str, body_html: str) -> str:
    return f"""
    <html>
      <body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;color:#111;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:24px 12px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#fff;border:1px solid #e5e7eb;border-radius:12px;">
                <tr>
                  <td style="padding:24px 24px 8px 24px;">
                    <p style="margin:0;font-size:12px;letter-spacing:0.12em;color:#6b7280;text-transform:uppercase;">InterviewOS</p>
                    <h1 style="margin:10px 0 0 0;font-size:24px;line-height:1.2;color:#111;">{title}</h1>
                  </td>
                </tr>
                <tr>
                  <td style="padding:20px 24px 24px 24px;font-size:15px;line-height:1.65;color:#111;">
                    {body_html}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def assessment_invite_email(*, instructions_link: str, is_resend: bool = False) -> EmailContent:
    subject = "Your InterviewOS Assessment"
    if is_resend:
        subject = "Reminder: Your InterviewOS Assessment"

    intro = (
        "Thanks for applying. Your assessment link is ready."
        if not is_resend
        else "This is a reminder to complete your assessment."
    )

    html_body = _layout(
        "Assessment Instructions",
        f"""
        <p style="margin:0 0 12px 0;">Hi,</p>
        <p style="margin:0 0 12px 0;">{intro}</p>
        <p style="margin:0 0 16px 0;">
          <strong>Time limit:</strong> 60 minutes<br/>
          <strong>Recording:</strong> Please record your screen and camera
        </p>
        <p style="margin:0 0 20px 0;">
          <a href="{instructions_link}" target="_blank" style="display:inline-block;background:#111;color:#fff;text-decoration:none;padding:10px 16px;border-radius:8px;font-weight:600;">Open assessment</a>
        </p>
        <p style="margin:0;">Good luck!<br/>The InterviewOS Team</p>
        """,
    )

    text_body = (
        "Hi,\n\n"
        f"{intro}\n\n"
        "Time limit: 60 minutes\n"
        "Recording: Please record your screen and camera\n"
        f"Instructions: {instructions_link}\n\n"
        "Good luck!\n"
        "The InterviewOS Team"
    )

    return EmailContent(subject=subject, html_body=html_body, text_body=text_body)


def assessment_reminder_email() -> EmailContent:
    subject = "15 Minutes Left - InterviewOS Assessment"
    text_body = (
        "Hi,\n\n"
        "This is your reminder for the InterviewOS assessment.\n\n"
        "Please wrap up your work, stop recording, zip your project, "
        "and submit according to the instructions.\n\n"
        "Good luck!"
    )

    html_body = _layout(
        "Reminder",
        """
        <p style="margin:0 0 12px 0;">Hi,</p>
        <p style="margin:0 0 12px 0;">This is your reminder for the InterviewOS assessment.</p>
        <p style="margin:0 0 12px 0;">
          Please wrap up your work, stop recording, zip your project, and submit according to the instructions.
        </p>
        <p style="margin:0;">Good luck!<br/>The InterviewOS Team</p>
        """,
    )

    return EmailContent(subject=subject, html_body=html_body, text_body=text_body)

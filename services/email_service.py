import logging


def send_email(to_email: str, subject: str, body: str) -> None:
    """Minimal email sending stub logging the intended message."""
    logging.getLogger("Thronestead.Email").info(
        "Sending email to %s with subject %s: %s", to_email, subject, body
    )

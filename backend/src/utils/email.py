import ssl
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.core.config_app import settings
from src.core.config_log import logger


class EmailService:
    """Сервис для подготовки и отправки системных уведомлений по Email"""

    @staticmethod
    def _render_email_html(title: str, user_full_name: str, content_html: str, button_url: str = None, button_text: str = None, token: str = None, ttl: str = None) -> str:
        """Генерирует HTML для письма. Все параметры, кроме title/content_html/user_full_name – опциональны"""
        theme = {
            'bg': '#FDF3E2',
            'card': '#ffffff',
            'stripe': '#F97316',
            'border': '#FCE8D0',
            'accent': '#E67E22',
            'text': '#8b5a2b',
            'subtext': '#5b4a3a',
            'secondary': '#e5d5b3'
        }
        button_block = ''
        if button_url and button_text:
            button_block = f"""
                <tr>
                    <td style=\"text-align:center;\">
                        <a href=\"{button_url}\" style=\"display:inline-block; padding:12px 20px; background:{theme['accent']}; color:#ffffff; text-decoration:none; border-radius:10px; font-size:16px; font-weight:700;\">{button_text}</a>
                    </td>
                </tr>
            """
        token_block = ''
        if token:
            token_block = f"""
                <tr>
                    <td style=\"padding:14px 0; text-align:center;\">
                        <div style=\"padding: 10px 14px; background:{theme['bg']}; border:1px dashed {theme['accent']}; color:{theme['text']}; margin: 0px 28px; font-family:monospace; font-size:16px; letter-spacing:1px; border-radius:10px;\">{token}</div>
                    </td>
                </tr>
            """
        ttl_block = ''
        if ttl:
            ttl_block = f"""
                <tr>
                    <td style=\"text-align:center; color:{theme['subtext']}; font-size:12px; padding-bottom:16px;\">Действует: {ttl}</td>
                </tr>
            """
        return f"""
            <html>
            <body style=\"margin:0; padding:0; font-family:'Inter', 'Arial', sans-serif; background:{theme['bg']}; color:{theme['text']};\">
              <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:{theme['bg']};\">
                <tr><td align=\"center\" style=\"padding:40px 12px;\">
                  <table width=\"480\" cellpadding=\"0\" cellspacing=\"0\" style=\"max-width:480px; background:{theme['card']}; border-radius:16px; border:1px solid {theme['border']}; overflow:hidden;\">
                    <tr><td style=\"background:{theme['stripe']}; text-align:center; padding:22px 16px;\"><h1 style=\"margin:0; font-size:28px; color:#fff;\">{title}</h1></td></tr>
                    <tr><td style=\"padding:24px 28px 0px 28px;\"><p style=\"margin:0 0 16px; font-size:16px; color:{theme['text']};\">Здравствуйте, <strong>{user_full_name}</strong></p><div style=\"font-size:14px; color:{theme['subtext']}; line-height:1.6;\">{content_html}</div></td></tr>
                    {button_block}
                    {token_block}
                    {ttl_block}
                    <tr><td style=\"background:{theme['secondary']}; padding:16px 20px; text-align:center; color:{theme['text']}; font-size:11px;\">Это автоматическое письмо – отвечать не нужно.</td></tr>
                  </table>
                </td></tr>
              </table>
            </body>
            </html>
        """

    @staticmethod
    async def send_email(to: str, subject: str, body: str, html: bool = True) -> bool:
        """
        Отправка письма через SMTP.
        Возвращает True при успехе, False при ошибке.
        НЕ работает с БД внутри – caller сам решает, что делать при ошибке.
        """
        message = MIMEMultipart()
        message["From"] = settings.SMTP_FROM
        message["To"] = to 
        message["Subject"] = subject
        content_type = "html" if html else "plain"
        message.attach(MIMEText(body, content_type, "utf-8"))
        context = ssl.create_default_context()
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_SERVER,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_SSL,
                start_tls=settings.SMTP_USE_STARTTLS,
                timeout=15, 
                tls_context=context
            )
            logger.info(f"[Email] Письмо успешно отправлено {to}")
            return True
        except Exception as e:
            logger.error(f"[Email] Не удалось отправить письмо по адресу {to}: {e}")
            return False 

    @staticmethod
    async def send_verification_email(user_email: str, user_full_name: str, token: str) -> None:
        """Отправляет письмо для подтверждения почты"""
        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        ttl_seconds = settings.VERIFICATION_TTL_SECONDS
        human_ttl = (
            f"{ttl_seconds // 3600} ч." if ttl_seconds % 3600 == 0 
            else f"{ttl_seconds // 60} м."
        )
        subject = "Подтверждение почты"
        content_html = (
            "<p style='margin:0 0 16px;'>Для подтверждения почты – нажмите кнопку ниже:</p>"
        )
        body = EmailService._render_email_html(
            title="Подтверждение почты",
            user_full_name=user_full_name,
            content_html=content_html,
            button_url=verify_link,
            button_text="Подтвердить почту",
            token=token,
            ttl=human_ttl,
        )
        await EmailService.send_email(user_email, subject, body)

    @staticmethod
    async def send_restore_email(user_email: str, user_full_name: str, token: str, expires_at: str) -> None:
        """Отправляет письмо для восстановления удаленного аккаунта"""
        restore_link = f"{settings.FRONTEND_URL}/recovery-account?token={token}"
        ttl_seconds = settings.DELETE_USER_TTL_SECONDS
        human_ttl = (
            f"{ttl_seconds // 3600} ч." if ttl_seconds % 3600 == 0 
            else f"{ttl_seconds // 60} м."
        )
        subject = "Восстановление аккаунта"
        content_html = (
            "<p style='margin:0 0 16px;'>Ваш аккаунт удален. Если вы хотите восстановить его – нажмите кнопку ниже:</p>"
            "<p style='margin:0 0 16px;'>Если вы не отдавали такого запроса – просто проигнорируйте это письмо.</p>"
        )
        body = EmailService._render_email_html(
            title="Восстановление аккаунта",
            user_full_name=user_full_name,
            content_html=content_html,
            button_url=restore_link,
            button_text="Восстановить аккаунт",
            token=token,
            ttl=human_ttl
        )
        await EmailService.send_email(user_email, subject, body)

    @staticmethod
    async def send_profile_reset_notification(user_email: str, user_full_name: str, login: str) -> bool:
        """Отправляет письмо при изменении администратором профиля пользователя"""
        subject = "Ваш профиль был изменен администратором"
        content_html = (
            "<p style='margin:0 0 16px;'>Ваш профиль был изменен администратором.</p>"
            "<p style='margin:0 0 16px;'>Скорее всего он нарушал правила сервиса.</p>"
            "<p style='margin:0 0 16px;'>Ваш действующий логин:</p>"
        )
        body = EmailService._render_email_html(
            title="Профиль изменен",
            user_full_name=user_full_name,
            content_html=content_html,
            token=login
        )
        return await EmailService.send_email(user_email, subject, body)

    @staticmethod
    async def send_pet_profile_reset_notification(user_email: str, user_full_name: str, pet_name: str) -> bool:
        """Отправляет письмо при изменении администратором питомца"""
        subject = f"Профиль питомца {pet_name} был изменен"

        content_html = (
            f"<p style='margin:0 0 16px;'>Профиль питомца <strong>{pet_name}</strong> был изменен администратором.</p>"
            "<p style='margin:0 0 16px;'>Скорее всего он нарушал правила сервиса.</p>"
        )
        body = EmailService._render_email_html(
            title=f"Профиль питомца {pet_name} изменен",
            user_full_name=user_full_name,
            content_html=content_html,
        )
        return await EmailService.send_email(user_email, subject, body)

    @staticmethod
    async def send_pet_restore_email(user_email: str, user_full_name: str, pet_name: str, token: str, expires_at: str) -> None:
        """Отправляет письмо для восстановления удаленного питомца"""
        restore_link = f"{settings.FRONTEND_URL}/pets"
        ttl_seconds = settings.TOKEN_TTL_SECONDS
        human_ttl = (
            f"{ttl_seconds // 3600} ч." if ttl_seconds % 3600 == 0 
            else f"{ttl_seconds // 60} м."
        )
        subject = f"Восстановление питомца {pet_name}"
        content_html = (
            f"<p style='margin:0 0 16px;'>Питомец <strong>{pet_name}</strong> был удалён. Если вы хотите восстановить его – нажмите кнопку ниже:</p>"
            "<p style='margin:0 0 16px;'>Если вы не удаляли питомца, просто проигнорируйте это письмо.</p>"
        )
        body = EmailService._render_email_html(
            title=f"Восстановление питомца {pet_name}",
            user_full_name=user_full_name,
            content_html=content_html,
            button_url=restore_link,
            button_text="Восстановить питомца",
            token=token,
            ttl=human_ttl
        )
        await EmailService.send_email(user_email, subject, body)

    @staticmethod
    async def send_reset_password_email(user_email: str, user_full_name: str, token: str, expires_at: str) -> None:
        """Отправляет инструкцию по сбросу пароля"""
        ttl_seconds = settings.RESET_PASSWORD_TTL_SECONDS
        human_ttl = (
            f"{ttl_seconds // 3600} ч." if ttl_seconds % 3600 == 0 
            else f"{ttl_seconds // 60} м."
        )
        subject = "Сброс пароля"
        content_html = (
            "<p style='margin:0 0 16px;'>Чтобы установить новый пароль – нажмите кнопку ниже:</p>"
            "<p style='margin:0 0 16px;'>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>"
        )
        body = EmailService._render_email_html(
            title="Сброс пароля",
            user_full_name=user_full_name,
            content_html=content_html,
            token=token,
            ttl=human_ttl
        )
        await EmailService.send_email(user_email, subject, body)
        
    @staticmethod
    async def send_delete_email(user_email: str, user_full_name: str) -> None:
        """Отправляет уведомление о том, что аккаунт был удалён"""
        subject = "Ваш аккаунт был удалён"
        content_html = (
            "<p style='margin:0 0 16px;'>Ваш аккаунт был удалён без возможности самостоятельного восстановления.</p>"
            "<p style='margin:0 0 16px;'>Если вы считаете, что это ошибка, обратитесь в службу поддержки.</p>"
        )
        body = EmailService._render_email_html(
            title="Аккаунт удален",
            user_full_name=user_full_name,
            content_html=content_html,
            button_url=f"{settings.FRONTEND_URL}/",
            button_text="Зайти в PetCore"
        )
        await EmailService.send_email(user_email, subject, body)


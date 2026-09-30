import os
from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path
from io import BytesIO

try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    
try:
    from icalendar import Calendar, Event
    ICS_AVAILABLE = True
except ImportError:
    ICS_AVAILABLE = False

from src.core.config_log import logger
from src.core.config_app import settings


class PetPhotoService:
    """Сервис для работы с фотографиями питомцев"""
    
    UPLOAD_DIR = Path("uploads/pets")
    PHOTO_PREFIX = "pets"
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "svg"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @classmethod
    def ensure_upload_dir(cls):
        """Создать директорию для загрузок если ее нет"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_allowed_extensions() -> set:
        """Получить список разрешенных расширений"""
        return PetPhotoService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """Проверить расширение файла"""
        if "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in PetPhotoService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Проверить размер файла"""
        return file_size <= PetPhotoService.MAX_FILE_SIZE
    
    @staticmethod
    def generate_pet_photo_filename(user_id: int, pet_id: int, original_filename: str) -> str:
        """Сгенерировать имя файла для фото питомца"""
        ext = original_filename.rsplit(".", 1)[1].lower()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"pet_{user_id}_{pet_id}_{timestamp}.{ext}"
    
    @staticmethod
    async def save_pet_photo(file_content: bytes, filename: str) -> str:
        """Сохранить фото питомца"""
        PetPhotoService.ensure_upload_dir()
        
        filepath = PetPhotoService.UPLOAD_DIR / filename
        
        try:
            with open(filepath, "wb") as f:
                f.write(file_content)
            
            logger.info(f"[PetImages] Фото питомца сохранено: {filepath} (размер: {len(file_content)} байт)")
            return filename
        except Exception as e:
            logger.error(f"[PetImages] Ошибка при сохранении фото {filename}: {type(e).__name__}: {str(e)}")
            raise
    
    @staticmethod
    async def delete_pet_photo(filename: str) -> bool:
        """Удалить фото питомца"""
        if filename == "pet-standart.png":
            logger.warning("[PetImages] Попытка удалить стандартное фото")
            return False
        
        filepath = PetPhotoService.UPLOAD_DIR / filename
        
        if filepath.exists():
            try:
                filepath.unlink()
                logger.info(f"[PetImages] Фото питомца удалено: {filepath}")
                return True
            except Exception as e:
                logger.error(f"[PetImages] Ошибка при удалении фото: {e}")
                return False
        
        return False
    
    @staticmethod
    def get_pet_photo_path(filename: str) -> Optional[Path]:
        """Получить путь к фото питомца"""
        filepath = PetPhotoService.UPLOAD_DIR / filename
        if filepath.exists():
            return filepath
        return None


class MedicalEventExportService:
    """Сервис для экспорта медицинских событий"""
    
    EXPORT_DIR = Path("uploads/exports")
    
    @classmethod
    def ensure_export_dir(cls):
        """Создать директорию для экспортов"""
        cls.EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _translate_medical_action_type(type_action: Optional[str]) -> str:
        """Перевод типа медицинского действия на русский"""
        mapping = {
            'inspection': 'Осмотр',
            'tests': 'Анализы',
            'diagnostics': 'Диагностика',
            'complex': 'Комплекс мероприятий',
            'parasite_treatment': 'Обработка от паразитов',
            'surgery': 'Операция',
            'treatment_course': 'Курс лечения',
            'dentistry': 'Стоматология',
            'grooming': 'Груминг',
            'other': 'Прочее'
        }
        if not type_action:
            return '—'
        return mapping.get(type_action.lower(), type_action)

    @staticmethod
    def _translate_medical_status(status: Optional[str]) -> str:
        """Перевод статуса медицинского события на русский"""
        mapping = {
            'planned': 'Запланировано',
            'completed': 'Завершено',
            'overdue': 'Просрочено'
        }
        if not status:
            return '—'
        return mapping.get(status.lower(), status)

    @staticmethod
    def export_medical_history_to_pdf(
        pet_name: str,
        events: List,
        user_name: str = "Пользователь"
    ) -> BytesIO:
        if not PDF_AVAILABLE:
            logger.error("[MedicalEventExportService] ReportLab не установлен")
            raise ImportError("PDF export requires reportlab: pip install reportlab")

        font_path = "Inter.ttf"
        main_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'

        try:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Inter', font_path))
                pdfmetrics.registerFont(TTFont('Inter-Bold', font_path))
                main_font = 'Inter'
                bold_font = 'Inter-Bold'
                logger.info("[MedicalEventExportService] Шрифт Inter загружен успешно")
            else:
                logger.warning(f"[MedicalEventExportService] Файл шрифта {font_path} не найден, используем встроенные шрифты")
        except Exception as e:
            logger.warning(f"[MedicalEventExportService] Не удалось загрузить шрифт {font_path}: {e}, используем встроенные шрифты")

        buffer = BytesIO()
        doc_title = "PetCore - Медицинская история питомца"
        if events and len(events) > 0:
            first_event_type = events[0].type_action.value if events[0].type_action else None
            if first_event_type:
                first_event_type_ru = MedicalEventExportService._translate_medical_action_type(first_event_type)
                doc_title = f"PetCore - {pet_name} - {first_event_type_ru}"
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch, title=doc_title)

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=bold_font,
            fontSize=18,
            textColor=colors.HexColor('#F97316'),
            spaceAfter=6,
            alignment=1,
            encoding='utf-8'
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=bold_font,
            fontSize=12,
            textColor=colors.HexColor('#F97316'),
            spaceAfter=12,
            spaceBefore=12,
            encoding='utf-8'
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=main_font,
            fontSize=10,
            encoding='utf-8'
        )

        story = []

        title_text = f"PetCore - Медицинский отчет"
        
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 0.2*inch))

        info_data = [
            ["Кличка питомца:", pet_name],
            ["Хозяин:", user_name],
            ["Дата генерации:", datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")]
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FDF3E2')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), main_font),
            ('FONTNAME', (0, 0), (0, -1), bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ENCODING', (0, 0), (-1, -1), 'utf-8')
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))

        story.append(Paragraph("История медицинских событий", heading_style))

        events_data = [["Дата", "Тип события", "Статус", "Описание", "Примечания"]]

        for event in events:
            date_str = event.date.strftime("%d.%m.%Y %H:%M") if event.date else "—"
            raw_event_type = event.type_action.value if event.type_action else None
            raw_status = event.status.value if event.status else None
            event_type = MedicalEventExportService._translate_medical_action_type(raw_event_type)
            status = MedicalEventExportService._translate_medical_status(raw_status)
            description = event.description or "—"
            notes = event.notes or "—"

            date_cell = Paragraph(date_str, normal_style)
            type_cell = Paragraph(event_type, normal_style)
            status_cell = Paragraph(status, normal_style)
            description_cell = Paragraph(description, normal_style)
            notes_cell = Paragraph(notes, normal_style)

            events_data.append([date_cell, type_cell, status_cell, description_cell, notes_cell])

        if len(events_data) == 1:
            story.append(Paragraph("Нет записей в медицинской истории", normal_style))
        else:
            events_table = Table(events_data, colWidths=[1.3*inch, 1.3*inch, 1.2*inch, 1.8*inch, 1.4*inch])
            events_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F97316')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), main_font),
                ('FONTNAME', (0, 0), (-1, 0), bold_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FCE8D0')]),
                ('ENCODING', (0, 0), (-1, -1), 'utf-8')
            ]))
            story.append(events_table)

        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def export_medical_events_to_ics(
        pet_name: str,
        events: List,
        user_email: str = settings.ADMIN_EMAIL
    ) -> BytesIO:
        """
        Экспортировать медицинские события в ICS (календарь)
        """
        if not ICS_AVAILABLE:
            logger.error("[MedicalEventExportService] icalendar не установлен, ICS экспорт недоступен")
            raise ImportError("ICS export requires icalendar: pip install icalendar pytz")
        
        cal = Calendar()
        cal.add('prodid', '-//PetCore//Medical Events//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', f'Медицинские события - {pet_name}')
        cal.add('x-wr-timezone', 'UTC')
        
        for event in events:
            vevent = Event()
            vevent.add('uid', f'{event.medical_history_id}@petcore.local')
            vevent.add('dtstamp', datetime.now(timezone.utc))
            
            if event.date:
                vevent.add('dtstart', event.date)
                vevent.add('dtend', event.date)
            
            raw_event_type = event.type_action.value if event.type_action else None
            raw_status = event.status.value if event.status else None
            event_type = MedicalEventExportService._translate_medical_action_type(raw_event_type) if raw_event_type else 'Медицинское событие'
            status_text = MedicalEventExportService._translate_medical_status(raw_status) if raw_status else 'Неизвестно'
            desc_text = event.description if event.description else 'Без описания'
            notes_text = event.notes if event.notes else 'Без примечаний'

            vevent.add('summary', f'PetCore - {pet_name} - {event_type}')
            
            description = f"Питомец: {pet_name}\n"
            description += f"Тип: {event_type}\n"
            description += f"Статус: {status_text}\n"
            
            if event.description:
                description += f"Описание: {desc_text}\n"
            if event.notes:
                description += f"Примечания: {notes_text}"
            
            vevent.add('description', description)
            vevent.add('location', 'Ветеринарная клиника')
            
            status_map = {
                'planned': 'TENTATIVE',
                'completed': 'CONFIRMED',
                'overdue': 'CONFIRMED'
            }
            vevent.add('status', status_map.get(event.status.value, 'TENTATIVE'))
            
            cal.add_component(vevent)
        
        buffer = BytesIO()
        buffer.write(cal.to_ical())
        buffer.seek(0)
        
        logger.info(f"[MedicalEventExportService] CS календарь сгенерирован для питомца '{pet_name}' с {len(events)} событиями")
        return buffer
    
    @staticmethod
    def save_export(content: BytesIO, filename: str, format_type: str = "pdf") -> str:
        """
        Сохранить экспорт в файл
        """
        MedicalEventExportService.ensure_export_dir()
        
        ext = f".{format_type}"
        full_filename = f"{filename}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{ext}"
        filepath = MedicalEventExportService.EXPORT_DIR / full_filename
        
        with open(filepath, "wb") as f:
            f.write(content.getvalue())
        
        logger.info(f"[MedicalEventExportService] Экспорт сохранен: {filepath}")
        return full_filename


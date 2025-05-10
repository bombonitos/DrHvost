from django import template

register = template.Library()

@register.filter
def filter_status(appointments, status):
    """Фильтрует записи по статусу"""
    return [appointment for appointment in appointments if appointment.status == status] 
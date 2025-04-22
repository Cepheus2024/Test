from datetime import timedelta

# Celery configuration
CELERY_IMPORTS = ('tasks',)
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Configure Celery Beat schedule
CELERYBEAT_SCHEDULE = {
    'send-daily-reminders': {
        'task': 'tasks.send_daily_reminders',
        'schedule': timedelta(days=1),
        'options': {'expires': 3600}
    },
    'send-monthly-reports': {
        'task': 'tasks.send_monthly_reports',
        'schedule': timedelta(days=30),  # This is an approximation, will run roughly monthly
        'options': {'expires': 7200}
    }
}

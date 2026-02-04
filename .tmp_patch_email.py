from pathlib import Path
p = Path('app/infrastructure/notifications/email_service.py')
text = p.read_text()
old = 'log.info('

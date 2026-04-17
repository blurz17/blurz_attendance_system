from core.db.config import config

broker_url = config.Redis_Url
result_backend = config.Redis_Url
broker_connection_retry_on_startup = True

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True
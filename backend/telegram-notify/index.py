'''
Business: Отправка Telegram уведомлений о новых рефералах и оформлении карт
Args: event с httpMethod, body (telegram_id, message, type); context с request_id
Returns: HTTP response с результатом отправки
'''

import json
import os
from typing import Dict, Any
import urllib.request
import urllib.parse

def send_telegram_message(telegram_id: int, message: str) -> bool:
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        return False
    
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {
        'chat_id': telegram_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=urllib.parse.urlencode(data).encode('utf-8'),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception:
        return False

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id, X-Auth-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        telegram_id = body.get('telegram_id')
        notification_type = body.get('type')
        data = body.get('data', {})
        
        if not telegram_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'telegram_id required'}),
                'isBase64Encoded': False
            }
        
        message = ''
        
        if notification_type == 'new_referral':
            referral_name = data.get('referral_name', 'Новый пользователь')
            message = f'''🎉 <b>Новый реферал!</b>

{referral_name} зарегистрировался по вашему промокоду.

💰 Вы получите <b>200₽</b>, как только он оформит карту Альфа-Банка.'''
        
        elif notification_type == 'card_issued':
            referral_name = data.get('referral_name', 'Пользователь')
            amount = data.get('amount', 200)
            message = f'''✅ <b>Карта оформлена!</b>

{referral_name} успешно оформил карту по вашему промокоду.

💸 На ваш баланс начислено <b>{amount}₽</b>!'''
        
        elif notification_type == 'custom':
            message = data.get('message', 'Уведомление от Альфа-Банка')
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Invalid notification type'}),
                'isBase64Encoded': False
            }
        
        success = send_telegram_message(telegram_id, message)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': success, 'message': 'Notification sent' if success else 'Failed to send'}),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }

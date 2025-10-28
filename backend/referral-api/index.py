'''
Business: API для реферальной системы Альфа Банка - регистрация пользователей, создание промокодов, начисление вознаграждений
Args: event с httpMethod, body, queryStringParameters; context с request_id
Returns: HTTP response с данными пользователя, промокодом и статистикой
'''

import json
import os
import random
import string
from typing import Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

@dataclass
class UserData:
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]

def generate_promo_code(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def convert_decimals(data):
    if isinstance(data, dict):
        return {k: convert_decimals(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimals(item) for item in data]
    elif isinstance(data, Decimal):
        return float(data)
    return data

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id, X-Auth-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'register':
                telegram_id = body.get('telegram_id')
                username = body.get('username')
                first_name = body.get('first_name')
                referrer_promo = body.get('referrer_promo')
                
                cursor.execute(
                    "SELECT id, telegram_id, username, first_name, promo_code, balance FROM users WHERE telegram_id = %s",
                    (telegram_id,)
                )
                existing_user = cursor.fetchone()
                
                if existing_user:
                    cursor.close()
                    conn.close()
                    user_data = convert_decimals(dict(existing_user))
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({
                            'user': user_data,
                            'message': 'User already exists'
                        }),
                        'isBase64Encoded': False
                    }
                
                promo_code = generate_promo_code()
                while True:
                    cursor.execute("SELECT id FROM users WHERE promo_code = %s", (promo_code,))
                    if not cursor.fetchone():
                        break
                    promo_code = generate_promo_code()
                
                cursor.execute(
                    "INSERT INTO users (telegram_id, username, first_name, promo_code) VALUES (%s, %s, %s, %s) RETURNING id, telegram_id, username, first_name, promo_code, balance",
                    (telegram_id, username, first_name, promo_code)
                )
                new_user = cursor.fetchone()
                
                if referrer_promo:
                    cursor.execute("SELECT telegram_id FROM users WHERE promo_code = %s", (referrer_promo,))
                    referrer = cursor.fetchone()
                    if referrer:
                        cursor.execute(
                            "INSERT INTO referrals (referrer_id, referred_id, promo_code) VALUES (%s, %s, %s)",
                            (referrer['telegram_id'], telegram_id, referrer_promo)
                        )
                
                conn.commit()
                cursor.close()
                conn.close()
                
                user_result = convert_decimals(dict(new_user))
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'user': user_result}),
                    'isBase64Encoded': False
                }
            
            elif action == 'issue_card':
                telegram_id = body.get('telegram_id')
                promo_code = body.get('promo_code')
                
                cursor.execute(
                    "UPDATE referrals SET card_issued = TRUE, card_issued_at = CURRENT_TIMESTAMP WHERE promo_code = %s AND referred_id = %s RETURNING referrer_id",
                    (promo_code, telegram_id)
                )
                referral = cursor.fetchone()
                
                if referral:
                    referrer_id = referral['referrer_id']
                    reward_amount = 200.00
                    
                    cursor.execute(
                        "UPDATE users SET balance = balance + %s WHERE telegram_id = %s",
                        (reward_amount, referrer_id)
                    )
                    
                    cursor.execute(
                        "INSERT INTO transactions (user_id, amount, type, description) VALUES (%s, %s, %s, %s)",
                        (referrer_id, reward_amount, 'referral_reward', f'Reward for referral {telegram_id}')
                    )
                    
                    cursor.execute(
                        "UPDATE referrals SET reward_paid = TRUE WHERE promo_code = %s AND referred_id = %s",
                        (promo_code, telegram_id)
                    )
                    
                    conn.commit()
                
                cursor.close()
                conn.close()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True, 'message': 'Card issued and reward credited'}),
                    'isBase64Encoded': False
                }
        
        elif method == 'GET':
            params = event.get('queryStringParameters', {})
            telegram_id = params.get('telegram_id')
            
            if not telegram_id:
                cursor.close()
                conn.close()
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'telegram_id required'}),
                    'isBase64Encoded': False
                }
            
            cursor.execute(
                "SELECT id, telegram_id, username, first_name, promo_code, balance FROM users WHERE telegram_id = %s",
                (int(telegram_id),)
            )
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'User not found'}),
                    'isBase64Encoded': False
                }
            
            cursor.execute(
                "SELECT COUNT(*) as total_referrals, COALESCE(SUM(CASE WHEN card_issued THEN 1 ELSE 0 END), 0) as cards_issued FROM referrals WHERE referrer_id = %s",
                (int(telegram_id),)
            )
            stats = cursor.fetchone()
            
            cursor.execute(
                "SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 10",
                (int(telegram_id),)
            )
            transactions = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            user_data = convert_decimals(dict(user))
            stats_data = convert_decimals(dict(stats)) if stats else {'total_referrals': 0, 'cards_issued': 0}
            transactions_data = convert_decimals([dict(t) for t in transactions])
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'user': user_data,
                    'stats': stats_data,
                    'transactions': transactions_data
                }),
                'isBase64Encoded': False
            }
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
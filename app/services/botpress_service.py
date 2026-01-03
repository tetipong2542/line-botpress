"""
Botpress service - Integration with Botpress webhook
"""
import requests
import hmac
import hashlib
from datetime import datetime
from flask import current_app


class BotpressService:
    """Service for Botpress integration"""

    @staticmethod
    def send_message_to_botpress(line_user_id, message, event_id=None):
        """
        Send message to Botpress webhook

        Args:
            line_user_id: LINE user ID
            message: Message text
            event_id: Optional event ID for idempotency

        Returns:
            Response from Botpress
        """
        webhook_url = current_app.config['BOTPRESS_WEBHOOK_URL']

        payload = {
            'type': 'text',
            'text': message,
            'userId': line_user_id,
            'channel': 'line',
            'eventId': event_id
        }

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Botpress error: {response.status_code}")
                return None

        except requests.RequestException as e:
            current_app.logger.error(f"Failed to send to Botpress: {str(e)}")
            return None

    @staticmethod
    def call_flask_api(endpoint, method='POST', data=None, line_user_id=None):
        """
        Call Flask API from Botpress (with HMAC signature)

        This is helper method for Botpress to call back to Flask API

        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request payload
            line_user_id: LINE user ID

        Returns:
            API response
        """
        bot_id = current_app.config['BOTPRESS_BOT_ID']
        bot_secret = current_app.config['BOT_HMAC_SECRET']
        timestamp = str(int(datetime.utcnow().timestamp()))

        # Build URL (assuming localhost in development)
        base_url = 'http://127.0.0.1:5000'
        url = f"{base_url}{endpoint}"

        # Prepare payload
        payload = data or {}
        if line_user_id:
            payload['line_user_id'] = line_user_id

        body = ''
        if payload:
            import json
            body = json.dumps(payload)

        # Generate HMAC
        message = f"{bot_id}:{timestamp}:{body}"
        signature = hmac.new(
            bot_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-BOT-ID': bot_id,
            'X-BOT-TS': timestamp,
            'X-BOT-HMAC': signature
        }

        try:
            if method == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            elif method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.request(method, url, json=payload, headers=headers, timeout=10)

            return response.json() if response.status_code < 400 else None

        except requests.RequestException as e:
            current_app.logger.error(f"Failed to call Flask API: {str(e)}")
            return None

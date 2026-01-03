"""
LINE webhook handler - Receives messages from LINE and forwards to Botpress
"""
from flask import Blueprint, request, jsonify, current_app
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from app.utils.security import require_line_signature
from app.services.botpress_service import BotpressService

bp = Blueprint('line', __name__, url_prefix='/line')


@bp.route('/webhook', methods=['POST'])
@require_line_signature()
def webhook():
    """
    LINE webhook endpoint
    Receives events from LINE and processes them
    """
    # Get request body
    body = request.get_data(as_text=True)

    try:
        events = json.loads(body).get('events', [])

        for event in events:
            if event.get('type') == 'message' and event['message'].get('type') == 'text':
                # Process text message
                line_user_id = event['source']['userId']
                message_text = event['message']['text']
                reply_token = event['replyToken']

                # Send to Botpress for processing
                response = BotpressService.send_message_to_botpress(
                    line_user_id=line_user_id,
                    message=message_text,
                    event_id=event.get('message', {}).get('id')
                )

                # Reply to LINE
                if response and response.get('reply'):
                    _send_line_reply(reply_token, response['reply'])

        return jsonify({'success': True})

    except Exception as e:
        current_app.logger.error(f"LINE webhook error: {str(e)}")
        return jsonify({
            'error': {
                'code': 'WEBHOOK_ERROR',
                'message': 'Failed to process webhook'
            }
        }), 500


def _send_line_reply(reply_token, text):
    """
    Send reply message to LINE

    Args:
        reply_token: LINE reply token
        text: Message text to send
    """
    try:
        line_bot_api = LineBotApi(current_app.config['LINE_CHANNEL_ACCESS_TOKEN'])
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=text)
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send LINE reply: {str(e)}")

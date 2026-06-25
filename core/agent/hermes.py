import asyncio
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
import queue


class NotificationChannel(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.channel_type = config.get('type', 'unknown')
        self.enabled = config.get('enabled', True)
        self._stats = config.get('stats', {'sent': 0, 'failed': 0})
    
    @abstractmethod
    async def send(self, message: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def test(self) -> bool:
        pass
    
    @property
    def stats(self) -> Dict[str, int]:
        return self._stats
    
    def increment_sent(self):
        self._stats['sent'] = self._stats.get('sent', 0) + 1
    
    def increment_failed(self):
        self._stats['failed'] = self._stats.get('failed', 0) + 1


class TelegramChannel(NotificationChannel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('bot_token', '')
        self.chat_id = config.get('chat_id', '')
    
    async def _resolve_username_if_needed(self) -> bool:
        """Helper to resolve Telegram username to numeric chat ID using getUpdates."""
        chat_id_str = str(self.chat_id).strip()
        if not chat_id_str:
            return False
        
        # A username starts with @ or contains letters/underscores
        is_username = chat_id_str.startswith('@') or any(c.isalpha() for c in chat_id_str)
        if not is_username:
            return True # Already a numeric chat ID
            
        username = chat_id_str.lstrip('@').lower()
        try:
            import httpx
            print(f"[Telegram] Attempting to resolve username '@{username}' to numeric Chat ID...")
            url_updates = f'https://api.telegram.org/bot{self.bot_token}/getUpdates'
            async with httpx.AsyncClient() as client:
                resp = await client.get(url_updates, timeout=10.0)
                if resp.status_code == 200:
                    updates_data = resp.json()
                    if updates_data.get('ok'):
                        for update in updates_data.get('result', []):
                            msg = update.get('message') or update.get('edited_message') or update.get('channel_post')
                            if not msg:
                                continue
                            
                            from_user = msg.get('from', {})
                            from_username = from_user.get('username', '')
                            
                            if from_username and from_username.lower() == username:
                                resolved_chat_id = msg.get('chat', {}).get('id')
                                if resolved_chat_id:
                                    print(f"[Telegram] Resolved username '{username}' to Chat ID: {resolved_chat_id}")
                                    self.chat_id = str(resolved_chat_id)
                                    self.config['chat_id'] = str(resolved_chat_id)
                                    
                                    # Persist to database
                                    channel_db_id = self.config.get('id')
                                    if channel_db_id:
                                        try:
                                            from core.storage.database import get_db, NotificationChannel as DBChannel
                                            db = get_db()
                                            session = db.get_session()
                                            db_channel = session.query(DBChannel).filter_by(id=channel_db_id).first()
                                            if db_channel:
                                                import json
                                                cfg = db_channel.config
                                                cfg['chat_id'] = str(resolved_chat_id)
                                                db_channel.config_json = json.dumps(cfg)
                                                session.commit()
                                            session.close()
                                        except Exception as db_err:
                                            print(f"[Telegram] Error saving resolved Chat ID to DB: {db_err}")
                                    return True
            return False
        except Exception as e:
            print(f"[Telegram] Error during username resolution: {e}")
            return False

    async def send(self, message: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        try:
            import httpx
            await self._resolve_username_if_needed()
            text = self._format_message(message, event_data)
            url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
                if resp.status_code == 200:
                    self.increment_sent()
                    return True
                self.increment_failed()
                return False
        except Exception as e:
            self.increment_failed()
            return False
    
    async def test(self) -> tuple[bool, str]:
        try:
            import httpx
            # 1. Verify the bot token is valid
            url_me = f'https://api.telegram.org/bot{self.bot_token}/getMe'
            async with httpx.AsyncClient() as client:
                resp_me = await client.get(url_me, timeout=5.0)
                if resp_me.status_code != 200:
                    err_msg = f"Bot token check failed (status: {resp_me.status_code})."
                    print(f"[Telegram-Test] {err_msg}")
                    return False, f"Invalid Bot Token. Telegram API returned: {resp_me.text}"
                
                # 2. Resolve username if username was provided
                chat_id_str = str(self.chat_id).strip()
                if not chat_id_str:
                    return False, "Chat ID or Username is missing."
                
                is_username = chat_id_str.startswith('@') or any(c.isalpha() for c in chat_id_str)
                if is_username:
                    resolved = await self._resolve_username_if_needed()
                    if not resolved:
                        username = chat_id_str.lstrip('@')
                        return False, (
                            f"Could not find any recent message from Telegram username '@{username}'. "
                            "You MUST send a message (e.g. '/start') to the bot in Telegram first, "
                            "so the bot can discover your Chat ID."
                        )
                
                # 3. Try sending a test message to verify the chat_id
                url_send = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
                payload = {
                    'chat_id': self.chat_id,
                    'text': '🧪 <b>AEGIS Notification Test</b>\n\nYour Telegram alert channel is configured and delivering successfully.',
                    'parse_mode': 'HTML'
                }
                resp_send = await client.post(url_send, json=payload, timeout=10.0)
                if resp_send.status_code != 200:
                    err_msg = f"sendMessage failed. Status: {resp_send.status_code}, Response: {resp_send.text}"
                    print(f"[Telegram-Test] {err_msg}")
                    return False, f"Failed to send message: {resp_send.text}. Verify that you have messaged the bot first."
            return True, "Test message sent successfully. Check your Telegram!"
        except Exception as e:
            print(f"[Telegram-Test] Error testing Telegram bot: {e}")
            return False, f"Internal error testing Telegram bot: {str(e)}"
    
    def _format_message(self, message: Dict[str, Any], event_data: Dict[str, Any]) -> str:
        template = self.config.get('template', 
            '<b>🚨 AEGIS Alert</b>\n\n<b>Camera:</b> {camera_name}\n<b>Event:</b> {event_type}\n<b>Time:</b> {timestamp}')
        
        replacements = {
            '{camera_name}': event_data.get('camera_name', 'Unknown'),
            '{event_type}': event_data.get('event_type', 'Alert'),
            '{description}': event_data.get('description', ''),
            '{confidence}': f"{event_data.get('confidence', 0) * 100:.0f}%",
            '{timestamp}': event_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        }
        
        text = template
        for key, value in replacements.items():
            text = text.replace(key, str(value))
        
        return text


class DiscordChannel(NotificationChannel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url', '')
    
    async def send(self, message: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        try:
            import httpx
            embed = {
                'title': f"🚨 {event_data.get('event_type', 'AEGIS Alert')}",
                'description': event_data.get('description', ''),
                'color': 0xEF4444 if event_data.get('severity') == 'critical' else 0xF59E0B,
                'fields': [
                    {'name': 'Camera', 'value': event_data.get('camera_name', 'Unknown'), 'inline': True},
                    {'name': 'Confidence', 'value': f"{event_data.get('confidence', 0) * 100:.0f}%", 'inline': True},
                    {'name': 'Time', 'value': event_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')), 'inline': False},
                ],
                'footer': {'text': 'AEGIS Video Analytics'}
            }
            payload = {'embeds': [embed]}
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload, timeout=10.0)
                if resp.status_code in (200, 204):
                    self.increment_sent()
                    return True
                self.increment_failed()
                return False
        except Exception:

            self.increment_failed()
            return False
    
    async def test(self) -> tuple[bool, str]:
        try:
            import httpx
            payload = {'content': '🧪 AEGIS Test Message'}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload, timeout=5.0)
                if resp.status_code in (200, 204):
                    return True, "Test message delivered to Discord successfully."
                return False, f"Discord webhook returned status code {resp.status_code}."
        except Exception as e:
            return False, f"Failed to connect to Discord: {str(e)}"


class WebhookChannel(NotificationChannel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get('url', '')
        self.method = config.get('method', 'POST').upper()
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
        self.body_template = config.get('body_template', {})
    
    async def send(self, message: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        try:
            import httpx
            body = self._build_body(event_data)
            async with httpx.AsyncClient() as client:
                kwargs = {'headers': self.headers, 'json': body} if self.method != 'GET' else {'headers': self.headers}
                resp = await client.request(self.method, self.url, **kwargs, timeout=10.0)
                if resp.status_code < 400:
                    self.increment_sent()
                    return True
                self.increment_failed()
                return False
        except Exception:

            self.increment_failed()
            return False
    
    async def test(self) -> tuple[bool, str]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.request(self.method, self.url, timeout=5.0)
                if resp.status_code < 400:
                    return True, f"Webhook test succeeded. Response status: {resp.status_code}."
                return False, f"Webhook returned status code {resp.status_code}."
        except Exception as e:
            return False, f"Webhook connection failed: {str(e)}"
    
    def _build_body(self, event_data: Dict[str, Any]) -> Dict:
        if callable(self.body_template):
            return self.body_template(event_data)
        
        body = {}
        for key, value in self.body_template.items():
            if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                body[key] = event_data.get(value[1:-1], '')
            else:
                body[key] = value
        return body


class SMSChannel(NotificationChannel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_sid = config.get('account_sid', '')
        self.auth_token = config.get('auth_token', '')
        self.from_number = config.get('from', '')
        self.to_number = config.get('to', '')
    
    async def send(self, message: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            body = f"AEGIS: {event_data.get('event_type', 'Alert')} - {event_data.get('camera_name', '')}"
            msg = client.messages.create(body=body, from_=self.from_number, to=self.to_number)
            if msg.sid:
                self.increment_sent()
                return True
            self.increment_failed()
            return False
        except Exception:

            self.increment_failed()
            return False
    
    async def test(self) -> tuple[bool, str]:
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            msg = client.messages.create(body='AEGIS SMS Test', from_=self.from_number, to=self.to_number)
            if msg.sid:
                return True, "SMS test message dispatched via Twilio."
            return False, "Twilio accepted the request but did not return a valid Message SID."
        except Exception as e:
            return False, f"Twilio SMS error: {str(e)}"


class WhatsAppChannel(NotificationChannel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_sid = config.get('account_sid', '')
        self.auth_token = config.get('auth_token', '')
        self.from_number = config.get('from', '')
        self.to_number = config.get('to', '')
    
    async def send(self, message: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            body = f"🚨 AEGIS Alert\n\nCamera: {event_data.get('camera_name', '')}\nEvent: {event_data.get('event_type', '')}\nDescription: {event_data.get('description', '')}"
            msg = client.messages.create(body=body, from_=f'whatsapp:{self.from_number}', to=f'whatsapp:{self.to_number}')
            if msg.sid:
                self.increment_sent()
                return True
            self.increment_failed()
            return False
        except Exception:

            self.increment_failed()
            return False
    
    async def test(self) -> tuple[bool, str]:
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            msg = client.messages.create(body='AEGIS WhatsApp Test', from_=f'whatsapp:{self.from_number}', to=f'whatsapp:{self.to_number}')
            if msg.sid:
                return True, "WhatsApp test message dispatched via Twilio."
            return False, "Twilio accepted the WhatsApp request but did not return a valid Message SID."
        except Exception as e:
            return False, f"Twilio WhatsApp error: {str(e)}"


class ChannelFactory:
    _channels = {
        'telegram': TelegramChannel,
        'discord': DiscordChannel,
        'webhook': WebhookChannel,
        'sms': SMSChannel,
        'whatsapp': WhatsAppChannel,
    }
    
    @classmethod
    def create(cls, channel_type: str, config: Dict[str, Any]) -> Optional[NotificationChannel]:
        channel_class = cls._channels.get(channel_type.lower())
        if channel_class:
            return channel_class(config)
        return None
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        return list(cls._channels.keys())


class TriggerEvaluator:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def evaluate(self, condition: str, frame_data: bytes, event_context: Dict[str, Any]) -> Dict[str, Any]:
        if self.llm_client and self._needs_llm_evaluation(condition):
            return await self._llm_evaluate(condition, frame_data, event_context)
        
        return self._rule_based_evaluate(condition, event_context)
    
    def _needs_llm_evaluation(self, condition: str) -> bool:
        llm_keywords = ['detect', 'identify', 'analyze', 'without', 'wearing', 'carrying', 'showing']
        return any(kw in condition.lower() for kw in llm_keywords)
    
    async def _llm_evaluate(self, condition: str, frame_data: bytes, event_context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""Analyze this camera frame and determine if the following condition is met:
        
Condition: {condition}

Camera: {event_context.get('camera_name', 'Unknown')}
Time: {event_context.get('timestamp', '')}

Provide a JSON response with:
{{
    "triggered": true/false,
    "confidence": 0.0-1.0,
    "description": "What was detected or observed",
    "severity": "info/warning/critical"
}}

Only respond with valid JSON."""

        result = await self.llm_client.analyze_image(frame_data, prompt)
        
        if result.get('success'):
            try:
                response_text = result.get('response', '')
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(response_text[start:end])
                    return {
                        'triggered': data.get('triggered', False),
                        'confidence': data.get('confidence', 0.0),
                        'description': data.get('description', ''),
                        'severity': data.get('severity', 'info')
                    }
            except Exception:

                pass
        
        return {'triggered': False, 'confidence': 0.0, 'description': '', 'severity': 'info'}
    
    def _rule_based_evaluate(self, condition: str, event_context: Dict[str, Any]) -> Dict[str, Any]:
        condition_lower = condition.lower()
        
        triggers = []
        if 'motion' in condition_lower:
            triggers.append('motion')
        if 'person' in condition_lower or 'people' in condition_lower:
            triggers.append('person')
        if 'vehicle' in condition_lower or 'car' in condition_lower:
            triggers.append('vehicle')
        
        severity = 'info'
        if 'critical' in condition_lower or 'emergency' in condition_lower:
            severity = 'critical'
        elif 'warning' in condition_lower or 'alert' in condition_lower:
            severity = 'warning'
        
        return {
            'triggered': len(triggers) > 0,
            'confidence': 0.8 if triggers else 0.0,
            'description': f"Condition matched: {condition}",
            'severity': severity
        }


class HermesAgent:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        from core.config import get_config
        self.config = get_config()
        self.check_interval = self.config.get('hermes.check_interval', 2)
        
        self._channels: Dict[int, NotificationChannel] = {}
        self._triggers: Dict[int, Dict] = {}
        self._running = False
        self._thread = None
        self._event_queue = queue.Queue(maxsize=100)
        self._event_callbacks: List[Callable] = []
        self._stats = {'triggers_active': 0, 'notifications_sent': 0, 'last_event': None, 'uptime': 0}
        self._start_time = time.time()
        
        self._load_channels()
        self._load_triggers()
        self.start()
    
    def _load_channels(self):
        from core.storage.database import get_db, NotificationChannel as DBChannel
        db = get_db()
        session = db.get_session()
        try:
            for ch in session.query(DBChannel).all():
                config_with_id = {**ch.config, 'id': ch.id}
                channel = ChannelFactory.create(ch.channel_type, config_with_id)
                if channel:
                    channel._stats = ch.channel_stats if ch.channel_stats else {'sent': 0, 'failed': 0}
                    self._channels[ch.id] = channel
        finally:
            session.close()
    
    def _load_triggers(self):
        from core.storage.database import get_db, Trigger as DBTrigger
        db = get_db()
        session = db.get_session()
        try:
            for trig in session.query(DBTrigger).all():
                self._triggers[trig.id] = {
                    'id': trig.id,
                    'name': trig.name,
                    'camera_id': trig.camera_id,
                    'condition_text': trig.condition_text,
                    'condition_config': trig.condition_config,
                    'notification_ids': trig.notification_ids_list,
                    'enabled': trig.enabled,
                    'capture_snapshot': trig.capture_snapshot,
                    'capture_clip': trig.capture_clip,
                    'clip_duration': trig.clip_duration
                }
        finally:
            session.close()
        self._stats['triggers_active'] = sum(1 for t in self._triggers.values() if t['enabled'])
    
    def add_channel(self, channel_type: str, config: Dict[str, Any]) -> int:
        from core.storage.database import get_db, NotificationChannel as DBChannel
        db = get_db()
        session = db.get_session()
        try:
            db_channel = DBChannel(
                name=config.get('name', f'{channel_type} Channel'),
                channel_type=channel_type,
                config_json=json.dumps(config),
                enabled=True
            )
            session.add(db_channel)
            session.commit()
            
            channel = ChannelFactory.create(channel_type, config)
            if channel:
                self._channels[db_channel.id] = channel
            
            return db_channel.id
        finally:
            session.close()
    
    def update_channel(self, channel_id: int, config: Dict[str, Any]):
        from core.storage.database import get_db, NotificationChannel as DBChannel
        db = get_db()
        session = db.get_session()
        try:
            db_channel = session.query(DBChannel).filter_by(id=channel_id).first()
            if db_channel:
                db_channel.config_json = json.dumps(config)
                session.commit()
                
                channel = ChannelFactory.create(db_channel.channel_type, config)
                if channel:
                    channel._stats = db_channel.channel_stats if db_channel.channel_stats else {'sent': 0, 'failed': 0}
                    self._channels[channel_id] = channel
        finally:
            session.close()
    
    def delete_channel(self, channel_id: int):
        from core.storage.database import get_db, NotificationChannel as DBChannel
        db = get_db()
        session = db.get_session()
        try:
            db_channel = session.query(DBChannel).filter_by(id=channel_id).first()
            if db_channel:
                session.delete(db_channel)
                session.commit()
            if channel_id in self._channels:
                del self._channels[channel_id]
        finally:
            session.close()
    
    def get_channel(self, channel_id: int) -> Optional[NotificationChannel]:
        return self._channels.get(channel_id)
    
    def get_all_channels(self) -> Dict[int, NotificationChannel]:
        return self._channels.copy()
    
    def add_trigger(self, trigger_data: Dict[str, Any]) -> int:
        from core.storage.database import get_db, Trigger as DBTrigger
        db = get_db()
        session = db.get_session()
        try:
            db_trigger = DBTrigger(
                name=trigger_data['name'],
                camera_id=trigger_data.get('camera_id'),
                condition_text=trigger_data['condition_text'],
                condition_config=trigger_data.get('condition_config', {}),
                notification_channel_ids=','.join(str(x) for x in trigger_data.get('notification_ids', [])),
                enabled=True,
                capture_snapshot=trigger_data.get('capture_snapshot', True),
                capture_clip=trigger_data.get('capture_clip', False),
                clip_duration=trigger_data.get('clip_duration', 30)
            )
            session.add(db_trigger)
            session.commit()
            
            trigger_data['id'] = db_trigger.id
            self._triggers[db_trigger.id] = trigger_data
            self._stats['triggers_active'] += 1
            
            return db_trigger.id
        finally:
            session.close()
    
    def update_trigger(self, trigger_id: int, trigger_data: Dict[str, Any]):
        from core.storage.database import get_db, Trigger as DBTrigger
        db = get_db()
        session = db.get_session()
        try:
            db_trigger = session.query(DBTrigger).filter_by(id=trigger_id).first()
            if db_trigger:
                db_trigger.name = trigger_data.get('name', db_trigger.name)
                db_trigger.condition_text = trigger_data.get('condition_text', db_trigger.condition_text)
                db_trigger.condition_config = trigger_data.get('condition_config', db_trigger.condition_config)
                if 'notification_ids' in trigger_data:
                    db_trigger.notification_channel_ids = ','.join(str(x) for x in trigger_data['notification_ids'])
                db_trigger.enabled = trigger_data.get('enabled', db_trigger.enabled)
                db_trigger.capture_snapshot = trigger_data.get('capture_snapshot', db_trigger.capture_snapshot)
                db_trigger.capture_clip = trigger_data.get('capture_clip', db_trigger.capture_clip)
                session.commit()
            
            if trigger_id in self._triggers:
                self._triggers[trigger_id].update(trigger_data)
        finally:
            session.close()
    
    def delete_trigger(self, trigger_id: int):
        from core.storage.database import get_db, Trigger as DBTrigger
        db = get_db()
        session = db.get_session()
        try:
            db_trigger = session.query(DBTrigger).filter_by(id=trigger_id).first()
            if db_trigger:
                if db_trigger.enabled:
                    self._stats['triggers_active'] -= 1
                session.delete(db_trigger)
                session.commit()
            if trigger_id in self._triggers:
                del self._triggers[trigger_id]
        finally:
            session.close()
    
    def get_all_triggers(self) -> Dict[int, Dict]:
        return self._triggers.copy()
    
    def toggle_trigger(self, trigger_id: int, enabled: bool):
        from core.storage.database import get_db, Trigger as DBTrigger
        db = get_db()
        session = db.get_session()
        try:
            db_trigger = session.query(DBTrigger).filter_by(id=trigger_id).first()
            if db_trigger:
                was_enabled = db_trigger.enabled
                db_trigger.enabled = enabled
                session.commit()
                
                if trigger_id in self._triggers:
                    self._triggers[trigger_id]['enabled'] = enabled
                
                if was_enabled and not enabled:
                    self._stats['triggers_active'] -= 1
                elif not was_enabled and enabled:
                    self._stats['triggers_active'] += 1
        finally:
            session.close()
    
    async def process_event(self, camera_id: int, frame_data: bytes, event_result: Dict[str, Any]):
        event = {
            'camera_id': camera_id,
            'frame_data': frame_data,
            'event_result': event_result,
            'timestamp': datetime.now().isoformat()
        }
        self._event_queue.put(event)
        self._stats['last_event'] = time.time()
        
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception:

                pass
    
    async def evaluate_triggers(self, camera_id: int, frame_data: bytes, event_context: Dict[str, Any]) -> List[Dict]:
        triggered = []
        
        for trigger_id, trigger in self._triggers.items():
            if not trigger.get('enabled', False):
                continue
            if trigger.get('camera_id') is not None and trigger.get('camera_id') != camera_id:
                continue
            
            from core.ai.llm_clients import get_llm_manager
            llm_manager = get_llm_manager()
            
            llm_client = None
            # 1. Try to find the first available external client (e.g. Gemini, OpenAI)
            for name, client in llm_manager.get_all_clients().items():
                if name not in ('ollama', 'lmstudio') and client.is_available():
                    llm_client = client
                    break
            
            # 2. If not found, check if LM Studio is available
            if not llm_client:
                lmstudio_client = llm_manager.get_client('lmstudio')
                if lmstudio_client and lmstudio_client.is_available():
                    llm_client = lmstudio_client
            
            # 3. Fallback to Ollama if available
            if not llm_client:
                ollama_client = llm_manager.get_client('ollama')
                if ollama_client and ollama_client.is_available():
                    llm_client = ollama_client
            
            evaluator = TriggerEvaluator(llm_client=llm_client)
            result = await evaluator.evaluate(trigger['condition_text'], frame_data, event_context)
            
            if result['triggered']:
                result['trigger_id'] = trigger_id
                result['trigger_name'] = trigger['name']
                triggered.append(result)
                
                await self._execute_actions(trigger, result, event_context)
        
        return triggered
    
    async def _execute_actions(self, trigger: Dict, result: Dict, event_context: Dict):
        from core.storage.storage_manager import get_storage
        storage = get_storage()
        
        snapshot_path = None
        clip_path = None
        
        if trigger.get('capture_snapshot') and event_context.get('frame_data'):
            snapshot_path = storage.save_snapshot(
                event_context.get('camera_id'),
                event_context['frame_data'],
                {'trigger_id': trigger['id'], 'trigger_name': trigger['name']}
            )
        
        event_context_with_paths = {
            **event_context,
            'snapshot_path': str(snapshot_path) if snapshot_path else None,
            'clip_path': str(clip_path) if clip_path else None
        }
        
        notification_ids = trigger.get('notification_ids', [])
        message = {
            'trigger_name': trigger['name'],
            'condition': trigger['condition_text'],
            'result': result
        }
        
        for notif_id in notification_ids:
            channel = self._channels.get(notif_id)
            if channel and channel.enabled:
                try:
                    success = await channel.send(message, {
                        **event_context_with_paths,
                        'event_type': trigger['name'],
                        'description': result.get('description', ''),
                        'confidence': result.get('confidence', 0),
                        'severity': result.get('severity', 'info')
                    })
                    if success:
                        self._stats['notifications_sent'] += 1
                except Exception:

                    pass

        # Save event to SQLite database
        try:
            from core.storage.database import get_db, Event as DBEvent
            db = get_db()
            session = db.get_session()
            db_event = DBEvent(
                camera_id=event_context.get('camera_id'),
                event_type=trigger['name'],
                description=result.get('description', ''),
                confidence=result.get('confidence', 0.0),
                severity=result.get('severity', 'info'),
                snapshot_path=str(snapshot_path) if snapshot_path else None,
                video_path=None,
                event_metadata=result
            )
            session.add(db_event)
            session.commit()
            session.close()
        except Exception as e:
            print(f"Error saving event to database: {e}")

        # Notify GUI in real-time
        event_result = {
            'event_type': trigger['name'],
            'description': result.get('description', ''),
            'confidence': result.get('confidence', 0.0),
            'severity': result.get('severity', 'info'),
            'camera_name': event_context.get('camera_name', 'Unknown'),
            'snapshot_path': str(snapshot_path) if snapshot_path else None,
            'clip_path': None
        }
        await self.process_event(trigger.get('camera_id'), event_context.get('frame_data'), event_result)
    
    async def test_channel(self, channel_id: int) -> tuple[bool, str]:
        channel = self._channels.get(channel_id)
        if channel:
            return await channel.test()
        return False, "Channel not found in Hermes Agent."
    
    def register_event_callback(self, callback: Callable):
        self._event_callbacks.append(callback)
    
    def get_stats(self) -> Dict:
        self._stats['uptime'] = int(time.time() - self._start_time)
        return self._stats.copy()
    
    def reload(self):
        self._load_channels()
        self._load_triggers()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        try:
            get_tunnel_manager().stop()
        except Exception:
            pass
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _analysis_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the main async orchestrator that manages analysis and Telegram polling
        loop.run_until_complete(self._async_orchestrator())

    async def _async_orchestrator(self):
        # Start the Telegram polling orchestrator as a background task
        telegram_task = asyncio.create_task(self._telegram_polling_orchestrator())
        
        from core.camera.capture import get_camera_manager
        print("[Hermes] Active async orchestrator started successfully.")
        
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                
                cam_mgr = get_camera_manager()
                cameras = cam_mgr.get_all_cameras()
                
                for camera_id, camera in cameras.items():
                    if not camera.get('enabled', True):
                        continue
                    
                    # Only evaluate triggers if there are active enabled triggers for this camera
                    has_triggers = any(
                        t.get('enabled', False) and (t.get('camera_id') is None or t.get('camera_id') == camera_id)
                        for t in self._triggers.values()
                    )
                    if not has_triggers:
                        continue
                        
                    frame_data = cam_mgr.get_frame_jpeg(camera_id)
                    if not frame_data:
                        continue
                        
                    event_context = {
                        'camera_id': camera_id,
                        'camera_name': camera['name'],
                        'frame_data': frame_data,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    await self.evaluate_triggers(camera_id, frame_data, event_context)
            except Exception as e:
                print(f"[Hermes] Error in async analysis loop: {e}")
                await asyncio.sleep(1)
                
        # Graceful cleanup of background tasks
        telegram_task.cancel()
        try:
            await telegram_task
        except asyncio.CancelledError:
            pass

    async def _telegram_polling_orchestrator(self):
        active_tasks = {} # token -> Task
        print("[Telegram-Control] Orchestrator is running and monitoring active bots...")
        
        while self._running:
            try:
                # Find all unique active bot tokens in configured Telegram channels
                bot_tokens = set()
                for ch in self._channels.values():
                    if ch.channel_type == 'telegram' and ch.enabled:
                        token = ch.config.get('bot_token')
                        if token:
                            bot_tokens.add(token)
                
                # Spin up polling loops for new tokens
                for token in bot_tokens:
                    if token not in active_tasks or active_tasks[token].done():
                        active_tasks[token] = asyncio.create_task(self._single_bot_polling_loop(token))
                
                # Stop polling loops for removed/disabled tokens
                for token in list(active_tasks.keys()):
                    if token not in bot_tokens:
                        active_tasks[token].cancel()
                        del active_tasks[token]
                        
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[Telegram-Control] Error in polling orchestrator: {e}")
                await asyncio.sleep(5)
                
        # Terminate all polling loops on shutdown
        for task in active_tasks.values():
            task.cancel()

    async def _single_bot_polling_loop(self, token: str):
        import httpx
        last_update_id = 0
        print(f"[Telegram-Control] Initiating polling listener for token {token[:10]}...")
        
        while self._running:
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                params = {"timeout": 10, "offset": last_update_id}
                
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, params=params, timeout=15.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('ok'):
                            for update in data.get('result', []):
                                update_id = update.get('update_id')
                                last_update_id = update_id + 1
                                
                                message = update.get('message')
                                if message:
                                    await self._handle_telegram_message(token, message)
                    elif resp.status_code == 401:
                        print(f"[Telegram-Control] Bot token {token[:10]} is unauthorized. Retrying in 30s...")
                        await asyncio.sleep(30)
                        
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Telegram-Control] Error polling bot {token[:10]}: {e}")
                await asyncio.sleep(5)

    async def _handle_telegram_message(self, token: str, message: dict):
        import httpx
        chat = message.get('chat', {})
        chat_id = chat.get('id')
        text = message.get('text', '').strip()
        from_user = message.get('from', {})
        username = from_user.get('username') or from_user.get('first_name', 'User')
        
        if not chat_id or not text:
            return
            
        print(f"[Telegram-Control] Processing command from @{username}: '{text}'")
        text_lower = text.lower()
        
        # Reply helper
        async def send_reply(reply_text: str):
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": reply_text,
                "parse_mode": "HTML"
            }
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(url, json=payload, timeout=10.0)
            except Exception as e:
                print(f"[Telegram-Control] Reply dispatch error: {e}")
        
        if text_lower.startswith('/start') or text_lower.startswith('/help'):
            help_msg = (
                "🤖 <b>AEGIS Edge Control Center</b>\n"
                f"Welcome, @{username}! I am your remote surveillance assistant.\n\n"
                "<b>Monitoring Commands:</b>\n"
                "• /status — Check system health, storage, and active streams\n"
                "• /cameras — List configured cameras and online status\n"
                "• /live or /preview — Generate a secure link to watch feeds on your phone\n"
                "• /triggers — List visual alert triggers\n\n"
                "<b>Control Commands:</b>\n"
                "• /toggle <code>[trigger_id]</code> — Enable or disable a visual trigger\n"
                "• /prune — Force immediate storage pruning to free up disk space\n"
            )
            await send_reply(help_msg)
            
        elif text_lower.startswith('/status'):
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            
            from core.storage.storage_manager import get_storage
            used, total, percentage = get_storage().get_usage()
            
            stats = self.get_stats()
            uptime_days = stats.get('uptime', 0) // 86400
            uptime_hours = (stats.get('uptime', 0) % 86400) // 3600
            uptime_mins = (stats.get('uptime', 0) % 3600) // 60
            
            status_msg = (
                "🖥️ <b>AEGIS System Status</b>\n\n"
                f"<b>Uptime:</b> {uptime_days}d {uptime_hours}h {uptime_mins}m\n"
                f"<b>CPU Load:</b> {cpu}%\n"
                f"<b>Memory Load:</b> {mem}%\n"
                f"<b>Disk Allocation:</b> {used/(1024**3):.2f} / {total/(1024**3):.2f} GB ({percentage}%)\n\n"
                f"<b>Active Triggers:</b> {stats.get('triggers_active', 0)}\n"
                f"<b>Alerts Sent:</b> {stats.get('notifications_sent', 0)}\n"
            )
            await send_reply(status_msg)
            
        elif text_lower.startswith('/cameras'):
            from core.camera.capture import get_camera_manager
            cam_mgr = get_camera_manager()
            cameras = cam_mgr.get_all_cameras()
            
            if not cameras:
                await send_reply("📷 No surveillance cameras configured.")
                return
                
            lines = ["📷 <b>Connected Cameras</b>\n"]
            for cid, cam in cameras.items():
                status = cam_mgr.get_source_status(cid)
                emoji = "🟢" if status == 'connected' else "🟡" if status == 'connecting' else "🔴"
                lines.append(f"• {emoji} <b>{cam['name']}</b> (ID: {cid}) — <i>{status}</i>")
            
            await send_reply("\n".join(lines))
            
        elif text_lower.startswith('/live') or text_lower.startswith('/preview') or text_lower.startswith('/stream'):
            await send_reply("🔄 <i>Establishing secure public tunnel...</i>")
            
            tunnel_url = await get_tunnel_manager().get_url()
            if not tunnel_url:
                await send_reply("❌ Tunnel connection failed. Ensure system SSH client is functioning.")
                return
                
            from core.camera.capture import get_camera_manager
            cam_mgr = get_camera_manager()
            cameras = cam_mgr.get_all_cameras()
            
            if not cameras:
                await send_reply("📷 No cameras configured to preview.")
                return
                
            lines = [
                "📱 <b>AEGIS Live Phone Preview</b>\n"
                "Secure temporary links to monitor live camera feeds on the go:\n"
            ]
            for cid, cam in cameras.items():
                lines.append(
                    f"• <b>{cam['name']}</b>:\n"
                    f"🔗 <a href='{tunnel_url}/api/cameras/{cid}/stream'>Watch Live stream</a>\n"
                )
            lines.append("\n<i>Note: Links will remain active as long as the server is running.</i>")
            await send_reply("\n".join(lines))
            
        elif text_lower.startswith('/triggers'):
            if not self._triggers:
                await send_reply("🔔 No visual triggers configured.")
                return
                
            lines = ["🔔 <b>Visual Alerts Triggers</b>\n"]
            for tid, trig in self._triggers.items():
                status = "🟢 Enabled" if trig.get('enabled') else "🔴 Disabled"
                lines.append(
                    f"• <b>[ID: {tid}] {trig.get('name')}</b>\n"
                    f"  Condition: <i>\"{trig.get('condition_text')}\"</i>\n"
                    f"  Status: {status}\n"
                )
            await send_reply("\n".join(lines))
            
        elif text_lower.startswith('/toggle'):
            parts = text.split()
            if len(parts) < 2:
                await send_reply("⚠️ Specify a trigger ID, e.g., <code>/toggle 1</code>")
                return
            try:
                trigger_id = int(parts[1])
                if trigger_id not in self._triggers:
                    await send_reply(f"❌ Trigger ID {trigger_id} not found.")
                    return
                
                trig = self._triggers[trigger_id]
                new_state = not trig.get('enabled', False)
                self.toggle_trigger(trigger_id, new_state)
                
                status = "🟢 Enabled" if new_state else "🔴 Disabled"
                await send_reply(f"{status} trigger <b>'{trig['name']}'</b> (ID: {trigger_id}) successfully.")
            except ValueError:
                await send_reply("⚠️ Trigger ID must be a number, e.g., <code>/toggle 1</code>")
                
        elif text_lower.startswith('/prune') or text_lower.startswith('/clean'):
            await send_reply("🧹 <i>Pruning oldest surveillance data...</i>")
            try:
                from core.storage.storage_manager import get_storage
                cleaned_bytes = get_storage().clean_old_data()
                cleaned_mb = cleaned_bytes / (1024**2)
                await send_reply(f"🧹 <b>Prune Complete!</b>\nFreed <code>{cleaned_mb:.2f} MB</code> of storage space.")
            except Exception as e:
                await send_reply(f"❌ Error during storage pruning: {str(e)}")
        else:
            await send_reply("❓ Command not recognized. Send /help to see all remote control options.")


class TunnelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._process = None
        self._url = None
        self._lock = threading.Lock()
        self._starting = False
        
    async def get_url(self) -> Optional[str]:
        with self._lock:
            if self._url and self._process and self._process.poll() is None:
                return self._url
            
            if self._starting:
                return None
            self._starting = True
            
        try:
            self._url = await self._start_ssh_tunnel()
            return self._url
        finally:
            self._starting = False
            
    async def _start_ssh_tunnel(self) -> Optional[str]:
        self.stop()
        
        import subprocess
        import re
        import asyncio
        
        print("[Tunnel] Spinning up secure background SSH tunnel to localhost.run...")
        cmd = [
            "ssh", 
            "-o", "StrictHostKeyChecking=no", 
            "-R", "80:localhost:8000", 
            "nokey@localhost.run"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self._process = process
            
            loop = asyncio.get_running_loop()
            url = None
            start_time = time.time()
            
            while time.time() - start_time < 20:
                line = await loop.run_in_executor(None, process.stdout.readline)
                if not line:
                    break
                line_str = line.strip()
                print(f"[Tunnel Out] {line_str}")
                
                matches = re.findall(r'https?://[a-zA-Z0-9.-]+\.lhr\.life', line_str)
                if not matches:
                    matches = re.findall(r'https?://[a-zA-Z0-9.-]+\.lhr\.run', line_str)
                    
                if matches:
                    url = matches[0]
                    print(f"[Tunnel] Tunnel established at URL: {url}")
                    break
                    
                if process.poll() is not None:
                    print("[Tunnel] Tunnel connection process terminated early.")
                    break
                    
            return url
        except Exception as e:
            print(f"[Tunnel] Error establishing secure tunnel: {e}")
            return None
            
    def stop(self):
        if self._process:
            print("[Tunnel] Shutting down secure tunnel...")
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None
            self._url = None


_tunnel_manager = None

def get_tunnel_manager() -> TunnelManager:
    global _tunnel_manager
    if _tunnel_manager is None:
        _tunnel_manager = TunnelManager()
    return _tunnel_manager


def get_hermes() -> HermesAgent:
    return HermesAgent()
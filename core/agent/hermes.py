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
    
    async def send(self, message: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        try:
            import httpx
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
    
    async def test(self) -> bool:
        try:
            import httpx
            # 1. Verify the bot token is valid
            url_me = f'https://api.telegram.org/bot{self.bot_token}/getMe'
            async with httpx.AsyncClient() as client:
                resp_me = await client.get(url_me, timeout=5.0)
                if resp_me.status_code != 200:
                    print(f"[Telegram-Test] Bot token check failed. Status: {resp_me.status_code}, Response: {resp_me.text}")
                    return False
                
                # 2. Try sending a test message to verify the chat_id and that the conversation has started
                if self.chat_id:
                    url_send = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
                    payload = {
                        'chat_id': self.chat_id,
                        'text': '🧪 <b>AEGIS Notification Test</b>\n\nYour Telegram alert channel is configured and delivering successfully.',
                        'parse_mode': 'HTML'
                    }
                    resp_send = await client.post(url_send, json=payload, timeout=10.0)
                    if resp_send.status_code != 200:
                        print(f"[Telegram-Test] sendMessage failed for chat_id: {self.chat_id}. Status: {resp_send.status_code}, Response: {resp_send.text}")
                        return False
            return True
        except Exception as e:
            print(f"[Telegram-Test] Error testing Telegram bot: {e}")
            return False
    
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
    
    async def test(self) -> bool:
        try:
            import httpx
            payload = {'content': '🧪 AEGIS Test Message'}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload, timeout=5.0)
                return resp.status_code in (200, 204)
        except Exception:

            return False


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
    
    async def test(self) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.request(self.method, self.url, timeout=5.0)
                return resp.status_code < 400
        except Exception:

            return False
    
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
    
    async def test(self) -> bool:
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(body='AEGIS Test', from_=self.from_number, to=self.to_number)
            return True
        except Exception:

            return False


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
    
    async def test(self) -> bool:
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(body='AEGIS WhatsApp Test', from_=f'whatsapp:{self.from_number}', to=f'whatsapp:{self.to_number}')
            return True
        except Exception:

            return False


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
                channel = ChannelFactory.create(ch.channel_type, ch.config)
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
    
    async def test_channel(self, channel_id: int) -> bool:
        channel = self._channels.get(channel_id)
        if channel:
            return await channel.test()
        return False
    
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
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _analysis_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from core.camera.capture import get_camera_manager
        
        while self._running:
            try:
                time.sleep(self.check_interval)
                
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
                    
                    loop.run_until_complete(
                        self.evaluate_triggers(camera_id, frame_data, event_context)
                    )
            except Exception as e:
                print(f"Error in Hermes Agent analysis loop: {e}")
                time.sleep(1)


def get_hermes() -> HermesAgent:
    return HermesAgent()
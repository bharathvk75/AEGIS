import base64
import json
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from PIL import Image
import io


class BaseLLMClient(ABC):
    def __init__(self, endpoint: str, api_key: Optional[str] = None, model: Optional[str] = None):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.model = model
        self._connected = False
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @abstractmethod
    async def analyze_image(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_models(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        pass
    
    def _encode_image(self, image_data: bytes) -> str:
        return base64.b64encode(image_data).decode('utf-8')
    
    def _resize_image(self, image_data: bytes, max_size: int = 1024) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_data))
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(d * ratio) for d in img.size)
                img = img.resize(new_size, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format=img.format or 'JPEG')
            return buf.getvalue()
        except Exception:
            return image_data


class OllamaClient(BaseLLMClient):
    def __init__(self, host: str = "http://localhost:11434", model: str = "llava"):
        super().__init__(host, None, model)
        self.client = httpx.Client(base_url=self.endpoint, timeout=60.0)
    
    def is_available(self) -> bool:
        try:
            resp = self.client.get('/api/tags')
            self._connected = resp.status_code == 200
            return self._connected
        except Exception:
            self._connected = False
            return False
    
    def get_models(self) -> List[Dict[str, Any]]:
        try:
            resp = self.client.get('/api/tags')
            if resp.status_code == 200:
                data = resp.json()
                return [{'name': m['name'], 'size': m.get('size', 0), 'modified': m.get('modified_at', '')} 
                        for m in data.get('models', [])]
            return []
        except Exception:
            return []
    
    def pull_model(self, model: str, callback=None) -> bool:
        try:
            with self.client.stream('POST', '/api/pull', json={'name': model}) as resp:
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line)
                        if callback:
                            callback(data)
                        if data.get('status') == 'success':
                            return True
            return False
        except Exception:
            return False
    
    def delete_model(self, model: str) -> bool:
        try:
            resp = self.client.request('DELETE', '/api/delete', json={'name': model})
            return resp.status_code == 200
        except Exception:
            return False
    
    async def analyze_image(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        try:
            resized = self._resize_image(image_data, 1024)
            img_b64 = self._encode_image(resized)
            
            payload = {
                'model': self.model,
                'prompt': prompt,
                'images': [img_b64],
                'stream': False
            }
            async with httpx.AsyncClient(base_url=self.endpoint, timeout=120.0) as client:
                resp = await client.post('/api/generate', json=payload)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        'success': True,
                        'response': data.get('response', ''),
                        'model': self.model
                    }
                return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        try:
            payload = {
                'model': self.model,
                'messages': messages,
                'stream': False
            }
            async with httpx.AsyncClient(base_url=self.endpoint, timeout=120.0) as client:
                resp = await client.post('/api/chat', json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get('message', {}).get('content', '')
                return ''
        except Exception as e:
            return str(e)
    
    def close(self):
        self.client.close()


class LMStudioClient(BaseLLMClient):
    def __init__(self, host: str = "http://localhost:1234", model: str = "local-model"):
        super().__init__(f"{host}/v1", None, model)
        self.client = httpx.Client(base_url=self.endpoint, timeout=120.0)
    
    def is_available(self) -> bool:
        try:
            resp = self.client.get(f"{self.endpoint}/models")
            self._connected = resp.status_code == 200
            return self._connected
        except Exception:
            self._connected = False
            return False
    
    def get_models(self) -> List[Dict[str, Any]]:
        try:
            resp = self.client.get(f"{self.endpoint}/models")
            if resp.status_code == 200:
                data = resp.json()
                return [{'name': m.get('id', 'unknown'), 'size': 0} for m in data.get('data', [])]
            return []
        except Exception:
            return []
    
    async def analyze_image(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        try:
            resized = self._resize_image(image_data, 1024)
            img_b64 = self._encode_image(resized)
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt},
                            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}}
                        ]
                    }
                ],
                'max_tokens': 1000
            }
            async with httpx.AsyncClient(base_url=self.endpoint, timeout=120.0) as client:
                resp = await client.post('/chat/completions', json=payload)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        'success': True,
                        'response': data.get('choices', [{}])[0].get('message', {}).get('content', ''),
                        'model': self.model
                    }
                return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        try:
            payload = {
                'model': self.model,
                'messages': messages,
                'stream': False
            }
            async with httpx.AsyncClient(base_url=self.endpoint, timeout=120.0) as client:
                resp = await client.post('/chat/completions', json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return ''
        except Exception as e:
            return str(e)


class OpenAIClient(BaseLLMClient):
    def __init__(self, endpoint: str, api_key: str, model: str = "gpt-4o"):
        super().__init__(endpoint, api_key, model)
        self.client = httpx.Client(
            base_url=self.endpoint,
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=120.0
        )
    
    def is_available(self) -> bool:
        try:
            resp = self.client.get(f"{self.endpoint}/models")
            self._connected = resp.status_code == 200
            return self._connected
        except Exception:
            self._connected = False
            return False
    
    def get_models(self) -> List[Dict[str, Any]]:
        try:
            resp = self.client.get(f"{self.endpoint}/models")
            if resp.status_code == 200:
                data = resp.json()
                return [{'name': m.get('id', 'unknown'), 'size': 0} for m in data.get('data', [])]
            return []
        except Exception:
            return []
    
    async def analyze_image(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        try:
            resized = self._resize_image(image_data, 1024)
            img_b64 = self._encode_image(resized)
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt},
                            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}}
                        ]
                    }
                ],
                'max_tokens': 1000
            }
            async with httpx.AsyncClient(base_url=self.endpoint, headers={'Authorization': f'Bearer {self.api_key}'}, timeout=120.0) as client:
                resp = await client.post('/chat/completions', json=payload)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        'success': True,
                        'response': data.get('choices', [{}])[0].get('message', {}).get('content', ''),
                        'model': self.model
                    }
                return {'success': False, 'error': f'HTTP {resp.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        try:
            payload = {
                'model': self.model,
                'messages': messages,
                'stream': False
            }
            async with httpx.AsyncClient(base_url=self.endpoint, headers={'Authorization': f'Bearer {self.api_key}'}, timeout=120.0) as client:
                resp = await client.post('/chat/completions', json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return ''
        except Exception as e:
            return str(e)
    
    def close(self):
        self.client.close()


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        super().__init__("https://generativelanguage.googleapis.com", api_key, model)
        self.client = httpx.Client(timeout=120.0)
    
    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            resp = self.client.get(f"{self.endpoint}/v1beta/models?key={self.api_key}")
            self._connected = resp.status_code == 200
            return self._connected
        except Exception as e:
            print(f"Gemini API connection error: {e}")
            self._connected = False
            return False
    
    def get_models(self) -> List[Dict[str, Any]]:
        try:
            resp = self.client.get(f"{self.endpoint}/v1beta/models?key={self.api_key}")
            if resp.status_code == 200:
                data = resp.json()
                # Return list of models, filtering by 1.5/2.5 flash/pro models for relevance
                models = []
                for m in data.get('models', []):
                    name = m.get('name', '').split('/')[-1]
                    if 'gemini' in name:
                        models.append({'name': name, 'size': 0})
                return models if models else [{'name': self.model, 'size': 0}]
            else:
                print(f"Gemini API get_models returned {resp.status_code}: {resp.text}")
            return []
        except Exception as e:
            print(f"Gemini API get_models error: {e}")
            return []
    
    async def analyze_image(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        try:
            resized = self._resize_image(image_data, 1024)
            img_b64 = self._encode_image(resized)
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                url = f"{self.endpoint}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inlineData": {
                                        "mimeType": "image/jpeg",
                                        "data": img_b64
                                    }
                                }
                            ]
                        }
                    ]
                }
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = ""
                    try:
                        response_text = data['candidates'][0]['content']['parts'][0]['text']
                    except (KeyError, IndexError):
                        pass
                    return {
                        'success': True,
                        'response': response_text,
                        'model': self.model
                    }
                return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        try:
            contents = []
            for msg in messages:
                role = msg.get('role', 'user')
                if role == 'assistant':
                    role = 'model'
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get('content', '')}]
                })
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                url = f"{self.endpoint}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": contents
                }
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        return data['candidates'][0]['content']['parts'][0]['text']
                    except (KeyError, IndexError):
                        return ""
                return f"Error: {resp.status_code}"
        except Exception as e:
            return str(e)
    
    def close(self):
        self.client.close()


class LLMManager:
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
        self._clients = {}
        self._init_clients()
    
    def _init_clients(self):
        ollama_config = self.config.get_section('ollama')
        self._clients['ollama'] = OllamaClient(
            host=ollama_config.get('host', 'http://localhost:11434'),
            model=ollama_config.get('default_model', 'llava')
        )
        
        lm_config = self.config.get_section('lmstudio')
        self._clients['lmstudio'] = LMStudioClient(host=lm_config.get('host', 'http://localhost:1234'))
        
        for provider in self.config.get('external_ai.providers', []):
            if provider.get('enabled', True) and provider.get('api_key'):
                name = provider['name'].lower()
                if 'gemini' in name:
                    self._clients[name] = GeminiClient(
                        api_key=provider['api_key'],
                        model=provider.get('default_model', 'gemini-1.5-flash')
                    )
                else:
                    self._clients[name] = OpenAIClient(
                        endpoint=provider['endpoint'],
                        api_key=provider['api_key'],
                        model=provider.get('default_model', 'gpt-4o')
                    )
        
        # Load external providers from SQLite database
        try:
            from core.storage.database import get_db, Model as DBModel
            db = get_db()
            session = db.get_session()
            db_models = session.query(DBModel).filter_by(is_local=False, enabled=True).all()
            for db_model in db_models:
                prov_name = db_model.name.lower()
                if prov_name not in self._clients:
                    if 'gemini' in prov_name:
                        self._clients[prov_name] = GeminiClient(
                            api_key=db_model.api_key,
                            model=db_model.model_name if db_model.model_name else 'gemini-1.5-flash'
                        )
                    else:
                        self._clients[prov_name] = OpenAIClient(
                            endpoint=db_model.endpoint,
                            api_key=db_model.api_key,
                            model=db_model.model_name if db_model.model_name else 'default'
                        )
            session.close()
        except Exception as e:
            print(f"Error loading external models from database: {e}")
    
    def reload_clients(self):
        self._clients.clear()
        self._init_clients()
    
    def get_client(self, provider: str = 'ollama') -> Optional[BaseLLMClient]:
        return self._clients.get(provider.lower())
    
    def add_client(self, name: str, client: BaseLLMClient):
        self._clients[name.lower()] = client
    
    def get_all_clients(self) -> Dict[str, BaseLLMClient]:
        return self._clients.copy()
    
    def check_all_connected(self) -> Dict[str, bool]:
        return {name: client.is_available() for name, client in self._clients.items()}
    
    async def analyze_frame(self, image_data: bytes, prompt: str, provider: str = 'ollama') -> Dict[str, Any]:
        client = self.get_client(provider)
        if not client:
            return {'success': False, 'error': f'Provider {provider} not found'}
        if not client.is_available():
            return {'success': False, 'error': f'{provider} not available'}
        return await client.analyze_image(image_data, prompt)
    
    def get_all_models(self) -> Dict[str, List[Dict]]:
        result = {}
        for name, client in self._clients.items():
            models = client.get_models() if client.is_available() else []
            result[name] = models
        return result


def get_llm_manager() -> LLMManager:
    return LLMManager()
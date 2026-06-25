import customtkinter as ctk
import threading


class ModelsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._setup_style()
        self._create_widgets()
        self._refresh_thread = None
        self._running = True
    
    def _setup_style(self):
        from gui.theme import AEGISTheme
        self.configure(fg_color=AEGISTheme.get_color('primary_bg'))
    
    def _create_widgets(self):
        from gui.theme import AEGISTheme
        
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=20, pady=(15, 10))
        
        title = ctk.CTkLabel(
            header,
            text='AI Model Management',
            font=('Inter', 22, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        title.pack(side='left')
        
        refresh_btn = ctk.CTkButton(
            header,
            text='↻ Refresh',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            text_color=AEGISTheme.get_color('text_primary'),
            hover_color=AEGISTheme.get_color('hover'),
            width=90,
            height=32,
            corner_radius=6,
            command=self._refresh_models
        )
        refresh_btn.pack(side='right')
        
        content = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent',
            scrollbar_button_color=AEGISTheme.get_color('card_bg')
        )
        content.pack(fill='both', expand=True, padx=15, pady=10)
        
        self._create_ollama_section(content)
        self._create_lmstudio_section(content)
        self._create_external_section(content)
    
    def _create_ollama_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x', pady=(0, 15))
        
        header = ctk.CTkFrame(section, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(15, 5))
        
        icon = ctk.CTkLabel(
            header,
            text='🤖',
            font=('Inter', 18, 'normal')
        )
        icon.pack(side='left')
        
        title = ctk.CTkLabel(
            header,
            text='Local Models (Ollama)',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        title.pack(side='left', padx=8)
        
        self.ollama_status = ctk.CTkLabel(
            header,
            text='● Connecting...',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('warning')
        )
        self.ollama_status.pack(side='right')
        
        self.ollama_models_frame = ctk.CTkFrame(section, fg_color='transparent')
        self.ollama_models_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        pull_frame = ctk.CTkFrame(section, fg_color='transparent')
        pull_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        self.pull_entry = ctk.CTkEntry(
            pull_frame,
            placeholder_text='Enter model name (e.g., llava, qwen2-vl)',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=36,
            corner_radius=6
        )
        self.pull_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        pull_btn = ctk.CTkButton(
            pull_frame,
            text='Pull Model',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            text_color='white',
            width=100,
            height=36,
            corner_radius=6,
            command=self._pull_model
        )
        pull_btn.pack(side='right')
    
    def _create_lmstudio_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x', pady=(0, 15))
        
        header = ctk.CTkFrame(section, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(15, 10))
        
        icon = ctk.CTkLabel(
            header,
            text='🔗',
            font=('Inter', 18, 'normal')
        )
        icon.pack(side='left')
        
        title = ctk.CTkLabel(
            header,
            text='LM Studio Server',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        title.pack(side='left', padx=8)
        
        content = ctk.CTkFrame(section, fg_color='transparent')
        content.pack(fill='x', padx=15, pady=(0, 15))
        
        endpoint_frame = ctk.CTkFrame(content, fg_color='transparent')
        endpoint_frame.pack(fill='x')
        
        endpoint_label = ctk.CTkLabel(
            endpoint_frame,
            text='Endpoint:',
            font=('Inter', 12, 'normal'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        endpoint_label.pack(side='left', padx=(0, 10))
        
        self.lmstudio_entry = ctk.CTkEntry(
            endpoint_frame,
            placeholder_text='http://localhost:1234',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            width=280,
            height=36,
            corner_radius=6
        )
        self.lmstudio_entry.insert(0, 'http://localhost:1234')
        self.lmstudio_entry.pack(side='left', padx=(0, 10))
        
        connect_btn = ctk.CTkButton(
            endpoint_frame,
            text='Connect',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_accent'),
            hover_color='#5558E3',
            text_color='white',
            width=90,
            height=36,
            corner_radius=6,
            command=self._connect_lmstudio
        )
        connect_btn.pack(side='left')
        
        self.lmstudio_status = ctk.CTkLabel(
            content,
            text='Status: Not connected',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('text_muted')
        )
        self.lmstudio_status.pack(anchor='w', pady=(10, 0))
    
    def _create_external_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x')
        
        header = ctk.CTkFrame(section, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(15, 10))
        
        icon = ctk.CTkLabel(
            header,
            text='☁️',
            font=('Inter', 18, 'normal')
        )
        icon.pack(side='left')
        
        title = ctk.CTkLabel(
            header,
            text='External APIs (OpenAI-Compatible)',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        title.pack(side='left', padx=8)
        
        add_btn = ctk.CTkButton(
            header,
            text='+ Add Provider',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            text_color='white',
            width=110,
            height=32,
            corner_radius=6,
            command=self._show_add_provider_modal
        )
        add_btn.pack(side='right')
        
        self.providers_frame = ctk.CTkFrame(section, fg_color='transparent')
        self.providers_frame.pack(fill='x', padx=15, pady=(0, 15))
    
    def _refresh_models(self):
        threading.Thread(target=self._fetch_ollama_models, daemon=True).start()
    
    def _fetch_ollama_models(self):
        from core.ai.llm_clients import get_llm_manager
        
        try:
            manager = get_llm_manager()
            client = manager.get_client('ollama')
            
            if client and client.is_available():
                models = client.get_models()
                self.after(10, lambda: self._update_ollama_models(models, True))
            else:
                self.after(10, lambda: self._update_ollama_status(False))
        except Exception as e:
            self.after(10, lambda: self._update_ollama_status(False))
    
    def _update_ollama_models(self, models: list, connected: bool):
        from gui.theme import AEGISTheme
        
        self.ollama_status.configure(
            text='● Connected' if connected else '● Disconnected',
            text_color=AEGISTheme.get_color('success') if connected else AEGISTheme.get_color('error')
        )
        
        for widget in self.ollama_models_frame.winfo_children():
            widget.destroy()
        
        if not models:
            empty = ctk.CTkLabel(
                self.ollama_models_frame,
                text='No models installed. Pull a model to get started.',
                font=('Inter', 12, 'normal'),
                text_color=AEGISTheme.get_color('text_muted')
            )
            empty.pack(anchor='w', pady=10)
            return
        
        for model in models:
            self._create_model_item(self.ollama_models_frame, model['name'], 'ollama')
    
    def _update_ollama_status(self, connected: bool):
        from gui.theme import AEGISTheme
        
        self.ollama_status.configure(
            text='● Connected' if connected else '● Disconnected',
            text_color=AEGISTheme.get_color('success') if connected else AEGISTheme.get_color('error')
        )
    
    def _create_model_item(self, parent, name: str, provider: str):
        from gui.theme import AEGISTheme
        
        item = ctk.CTkFrame(
            parent,
            fg_color=AEGISTheme.get_color('secondary_bg'),
            corner_radius=8
        )
        item.pack(fill='x', pady=3, ipady=8)
        
        name_label = ctk.CTkLabel(
            item,
            text=f'📦 {name}',
            font=('Inter', 13, 'normal'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        name_label.pack(side='left', padx=10)
        
        delete_btn = ctk.CTkButton(
            item,
            text='Delete',
            font=('Inter', 11, 'normal'),
            fg_color='transparent',
            text_color=AEGISTheme.get_color('error'),
            hover_color=AEGISTheme.get_color('hover'),
            width=60,
            height=28,
            corner_radius=6,
            command=lambda: self._delete_model(name, provider)
        )
        delete_btn.pack(side='right', padx=10)
    
    def _delete_model(self, name: str, provider: str):
        from core.ai.llm_clients import get_llm_manager
        
        try:
            manager = get_llm_manager()
            client = manager.get_client(provider)
            if client:
                if provider == 'ollama':
                    client.delete_model(name)
            self._refresh_models()
        except Exception as e:
            print(f"Error deleting model: {e}")
    
    def _pull_model(self):
        model_name = self.pull_entry.get().strip()
        if not model_name:
            return
        
        threading.Thread(target=self._do_pull_model, args=(model_name,), daemon=True).start()
    
    def _do_pull_model(self, model_name: str):
        from core.ai.llm_clients import get_llm_manager
        
        try:
            manager = get_llm_manager()
            client = manager.get_client('ollama')
            if client:
                success = client.pull_model(model_name)
                if success:
                    self.after(10, lambda: self._refresh_models())
        except Exception as e:
            print(f"Error pulling model: {e}")
    
    def _connect_lmstudio(self):
        endpoint = self.lmstudio_entry.get().strip()
        if not endpoint:
            return
        
        from gui.theme import AEGISTheme
        self.lmstudio_status.configure(text='Status: Connecting...', text_color=AEGISTheme.get_color('warning'))
        
        threading.Thread(target=self._do_connect_lmstudio, args=(endpoint,), daemon=True).start()
    
    def _do_connect_lmstudio(self, endpoint: str):
        from core.ai.llm_clients import LMStudioClient, get_llm_manager
        from gui.theme import AEGISTheme
        
        try:
            client = LMStudioClient(host=endpoint)
            connected = client.is_available()
            
            if connected:
                manager = get_llm_manager()
                manager.add_client('lmstudio', client)
                self.after(10, lambda: self.lmstudio_status.configure(
                    text='Status: Connected',
                    text_color=AEGISTheme.get_color('success')
                ))
            else:
                self.after(10, lambda: self.lmstudio_status.configure(
                    text='Status: Connection failed',
                    text_color=AEGISTheme.get_color('error')
                ))
        except Exception as e:
            self.after(10, lambda: self.lmstudio_status.configure(
                text=f'Status: Error - {str(e)[:30]}',
                text_color=AEGISTheme.get_color('error')
            ))
    
    def _show_add_provider_modal(self):
        from gui.components.widgets import Modal
        modal = Modal(self, title='Add External Provider', width=450, height=350)
        content = modal.get_content_frame()
        
        from gui.theme import AEGISTheme
        
        provider_label = ctk.CTkLabel(
            content,
            text='Provider Name',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        provider_label.pack(anchor='w', pady=(0, 5))
        
        provider_entry = ctk.CTkEntry(
            content,
            placeholder_text='e.g., OpenAI, Anthropic',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=38,
            corner_radius=6
        )
        provider_entry.pack(fill='x', pady=(0, 12))
        
        endpoint_label = ctk.CTkLabel(
            content,
            text='API Endpoint',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        endpoint_label.pack(anchor='w', pady=(0, 5))
        
        endpoint_entry = ctk.CTkEntry(
            content,
            placeholder_text='https://api.openai.com/v1',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=38,
            corner_radius=6
        )
        endpoint_entry.pack(fill='x', pady=(0, 12))
        
        apikey_label = ctk.CTkLabel(
            content,
            text='API Key',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        apikey_label.pack(anchor='w', pady=(0, 5))
        
        apikey_entry = ctk.CTkEntry(
            content,
            placeholder_text='sk-...',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=38,
            corner_radius=6,
            show='*'
        )
        apikey_entry.pack(fill='x', pady=(0, 15))
        
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='x')
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text='Cancel',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            text_color=AEGISTheme.get_color('text_primary'),
            hover_color=AEGISTheme.get_color('hover'),
            width=100,
            height=36,
            corner_radius=6,
            command=modal.destroy
        )
        cancel_btn.pack(side='left')
        
        add_btn = ctk.CTkButton(
            btn_frame,
            text='Add Provider',
            font=('Inter', 12, 'bold'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            text_color='white',
            width=120,
            height=36,
            corner_radius=6,
            command=lambda: self._add_provider(
                provider_entry.get(),
                endpoint_entry.get(),
                apikey_entry.get()
            )
        )
        add_btn.pack(side='right')
    
    def _add_provider(self, name: str, endpoint: str, api_key: str):
        if not name or not endpoint or not api_key:
            return
        
        try:
            from core.ai.llm_clients import OpenAIClient, GeminiClient, get_llm_manager
            from core.storage.database import get_db, Model
            
            prov_name = name.lower()
            if 'gemini' in prov_name:
                client = GeminiClient(api_key=api_key)
            else:
                client = OpenAIClient(endpoint=endpoint, api_key=api_key)
                
            manager = get_llm_manager()
            manager.add_client(prov_name, client)
            
            db = get_db()
            session = db.get_session()
            model = Model(
                name=name,
                provider=prov_name,
                endpoint=endpoint,
                api_key=api_key,
                model_name='gemini-1.5-flash' if 'gemini' in prov_name else 'default',
                is_local=False,
                enabled=True
            )
            session.add(model)
            session.commit()
            session.close()
            
            self._update_providers_list()
        except Exception as e:
            print(f"Error adding provider: {e}")
    
    def _update_providers_list(self):
        from gui.theme import AEGISTheme
        
        for widget in self.providers_frame.winfo_children():
            widget.destroy()
        
        try:
            from core.storage.database import get_db, Model
            db = get_db()
            session = db.get_session()
            providers = session.query(Model).filter_by(is_local=False).all()
            session.close()
            
            for provider in providers:
                item = ctk.CTkFrame(
                    self.providers_frame,
                    fg_color=AEGISTheme.get_color('secondary_bg'),
                    corner_radius=8
                )
                item.pack(fill='x', pady=3, ipady=8)
                
                info = ctk.CTkLabel(
                    item,
                    text=f'☁️ {provider.name} - {provider.endpoint}',
                    font=('Inter', 12, 'normal'),
                    text_color=AEGISTheme.get_color('text_primary')
                )
                info.pack(side='left', padx=10)
                
                delete_btn = ctk.CTkButton(
                    item,
                    text='Remove',
                    font=('Inter', 11, 'normal'),
                    fg_color='transparent',
                    text_color=AEGISTheme.get_color('error'),
                    hover_color=AEGISTheme.get_color('hover'),
                    width=60,
                    height=28,
                    corner_radius=6,
                    command=lambda p=provider.id: self._remove_provider(p)
                )
                delete_btn.pack(side='right', padx=10)
        except Exception as e:
            print(f"Error updating providers list: {e}")
    
    def _remove_provider(self, provider_id: int):
        try:
            from core.storage.database import get_db, Model
            db = get_db()
            session = db.get_session()
            model = session.query(Model).filter_by(id=provider_id).first()
            if model:
                session.delete(model)
                session.commit()
            session.close()
            self._update_providers_list()
        except Exception as e:
            print(f"Error removing provider: {e}")
    
    def on_show(self):
        self._running = True
        self._refresh_models()
        self._update_providers_list()
    
    def on_hide(self):
        self._running = False
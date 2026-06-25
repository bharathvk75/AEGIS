import customtkinter as ctk
import threading
import time


class AEGISApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self._configure_window()
        self._configure_appearance()
        self._create_layout()
        self._initialize_subsystems()
        self._start_background_tasks()
    
    def _configure_window(self):
        self.title('AEGIS - Edge Video Analytics')
        self.geometry('1400x800')
        self.minsize(1100, 700)
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - 1400) // 2
        y = (screen_h - 800) // 2
        self.geometry(f'+{x}+{y}')
        
        self.protocol('WM_DELETE_WINDOW', self._on_close)
    
    def _configure_appearance(self):
        from gui.theme import AEGISTheme
        AEGISTheme.apply()
    
    def _create_layout(self):
        from gui.components.sidebar import Sidebar, TitleBar
        
        self.title_bar = TitleBar(self)
        self.title_bar.pack(side='top', fill='x')
        self.title_bar.set_callbacks(
            minimize=self._on_minimize,
            close=self._on_close
        )
        
        main_container = ctk.CTkFrame(self, fg_color=self._get_color('primary_bg'))
        main_container.pack(side='top', fill='both', expand=True)
        
        self.sidebar = Sidebar(main_container, width=200)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.set_callback(self._on_nav_change)
        self.sidebar.update_status('● Starting...', self._get_color('warning'))
        
        self.content_frame = ctk.CTkFrame(main_container, fg_color=self._get_color('primary_bg'))
        self.content_frame.pack(side='left', fill='both', expand=True)
        
        self.status_bar = StatusBarView(self)
        self.status_bar.pack(side='bottom', fill='x')
        
        self._pages = {}
        self._current_page = None
        self._load_pages()
        
        self._navigate_to('dashboard')
    
    def _load_pages(self):
        from gui.pages.dashboard import DashboardPage
        from gui.pages.cameras import CamerasPage
        from gui.pages.models import ModelsPage
        from gui.pages.hermes import HermesPage
        from gui.pages.storage import StoragePage
        
        self._pages = {
            'dashboard': DashboardPage(self.content_frame),
            'cameras': CamerasPage(self.content_frame),
            'models': ModelsPage(self.content_frame),
            'hermes': HermesPage(self.content_frame),
            'storage': StoragePage(self.content_frame),
        }
    
    def _navigate_to(self, page_id: str):
        if self._current_page:
            page = self._pages.get(self._current_page)
            if page and hasattr(page, 'on_hide'):
                page.on_hide()
            page.pack_forget()
        
        self._current_page = page_id
        page = self._pages.get(page_id)
        if page:
            page.pack(fill='both', expand=True)
            if hasattr(page, 'on_show'):
                page.on_show()
        
        self.sidebar.set_active_page(page_id)
    
    def _on_nav_change(self, page_id: str):
        self._navigate_to(page_id)
    
    def _on_minimize(self):
        from core.config import get_config
        config = get_config()
        if config.get('app.min_to_tray', True):
            self.withdraw()
        else:
            self.iconify()
    
    def _on_close(self):
        self._cleanup()
        self.destroy()
    
    def _cleanup(self):
        try:
            from core.camera.capture import get_camera_manager
            cam_mgr = get_camera_manager()
            cam_mgr.stop_all()
        except Exception:

            pass
        try:
            from core.agent.hermes import get_hermes
            get_hermes().stop()
        except Exception:

            pass
    
    def _initialize_subsystems(self):
        def init():
            try:
                from core.storage.database import get_db
                db = get_db()
                _ = db.get_session()
                
                from core.config import get_config
                config = get_config()
                
                from core.storage.storage_manager import get_storage
                storage = get_storage()
                used, total, percentage = storage.get_usage()
                
                self.after(10, lambda: self.sidebar.update_storage(used / (1024**3), total / (1024**3), percentage))
                self.after(10, lambda: self.status_bar.update_storage(used / (1024**3), total / (1024**3), percentage))
                
                from core.ai.llm_clients import get_llm_manager
                manager = get_llm_manager()
                clients = manager.check_all_connected()
                
                ollama_connected = clients.get('ollama', False)
                lmstudio_connected = clients.get('lmstudio', False)
                gemini_connected = clients.get('gemini', False)
                
                any_connected = any(clients.values())
                
                if ollama_connected:
                    self.after(10, lambda: self.status_bar.update_ollama(True, config.get('ollama.default_model')))
                elif gemini_connected:
                    self.after(10, lambda: self.status_bar.update_ollama(True, 'Gemini 1.5'))
                elif lmstudio_connected:
                    self.after(10, lambda: self.status_bar.update_ollama(True, 'LM Studio'))
                else:
                    self.after(10, lambda: self.status_bar.update_ollama(False))
                
                if any_connected:
                    active_prov = 'Ollama' if ollama_connected else 'Gemini' if gemini_connected else 'LM Studio' if lmstudio_connected else 'AI'
                    self.after(10, lambda: self.sidebar.update_status(f'● System Ready ({active_prov})', self._get_color('success')))
                else:
                    self.after(10, lambda: self.sidebar.update_status('● AI Offline', self._get_color('error')))
                
                # Initialize Hermes Agent and register callback to update dashboard live event feed
                from core.agent.hermes import get_hermes
                hermes = get_hermes()
                
                def on_hermes_event(event):
                    result = event.get('event_result', {})
                    gui_event = {
                        'camera_name': result.get('camera_name', 'Unknown'),
                        'event_type': result.get('event_type', 'Alert'),
                        'description': result.get('description', ''),
                        'confidence': result.get('confidence', 0.0),
                        'severity': result.get('severity', 'info')
                    }
                    dashboard = self.get_dashboard()
                    if dashboard:
                        self.after(10, lambda: dashboard.add_event(gui_event))
                
                hermes.register_event_callback(on_hermes_event)
                
                from core.camera.capture import get_camera_manager
                cam_mgr = get_camera_manager()
                cam_mgr.start_all()
                
                self.after(10, lambda: self.status_bar.update_system('🟢 All Systems OK', self._get_color('success')))
                
                page = self._pages.get('dashboard')
                if page:
                    page.reload_cameras()
                    
            except Exception as e:
                print(f"Initialization error: {e}")
                self.after(10, lambda: self.sidebar.update_status('● Init Error', self._get_color('error')))
        
        threading.Thread(target=init, daemon=True).start()
    
    def _start_background_tasks(self):
        def background_loop():
            while True:
                try:
                    from core.config import get_config
                    config = get_config()
                    
                    from core.storage.storage_manager import get_storage
                    storage = get_storage()
                    used, total, percentage = storage.get_usage()
                    
                    self.after(10, lambda u=used, t=total, p=percentage: self.sidebar.update_storage(u / (1024**3), t / (1024**3), p))
                    self.after(10, lambda u=used, t=total, p=percentage: self.status_bar.update_storage(u / (1024**3), t / (1024**3), p))
                    
                    from core.ai.llm_clients import get_llm_manager
                    manager = get_llm_manager()
                    clients = manager.check_all_connected()
                    
                    ollama_connected = clients.get('ollama', False)
                    lmstudio_connected = clients.get('lmstudio', False)
                    gemini_connected = clients.get('gemini', False)
                    
                    if ollama_connected:
                        self.after(10, lambda: self.status_bar.update_ollama(True, config.get('ollama.default_model')))
                    elif gemini_connected:
                        self.after(10, lambda: self.status_bar.update_ollama(True, 'Gemini 1.5'))
                    elif lmstudio_connected:
                        self.after(10, lambda: self.status_bar.update_ollama(True, 'LM Studio'))
                    else:
                        self.after(10, lambda: self.status_bar.update_ollama(False))
                    
                except Exception:

                    pass
                
                time.sleep(10)
        
        threading.Thread(target=background_loop, daemon=True).start()
    
    def _get_color(self, key):
        from gui.theme import AEGISTheme
        return AEGISTheme.get_color(key)
    
    def get_dashboard(self):
        return self._pages.get('dashboard')


class StatusBarView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=32, **kwargs)
        self._setup_style()
        self._create_elements()
    
    def _setup_style(self):
        self.configure(height=32, corner_radius=0)
        from gui.theme import AEGISTheme
        self.configure(fg_color=AEGISTheme.get_color('secondary_bg'))
    
    def _create_elements(self):
        from gui.theme import AEGISTheme
        
        self.ollama_lbl = ctk.CTkLabel(
            self,
            text='🤖 Ollama: --',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('text_muted')
        )
        self.ollama_lbl.pack(side='left', padx=15)
        
        self.storage_lbl = ctk.CTkLabel(
            self,
            text='📊 Storage: --',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('text_muted')
        )
        self.storage_lbl.pack(side='left', padx=15)
        
        self.system_lbl = ctk.CTkLabel(
            self,
            text='🟢 Starting...',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('warning')
        )
        self.system_lbl.pack(side='right', padx=15)
    
    def update_ollama(self, connected: bool, model: str = None):
        from gui.theme import AEGISTheme
        
        if connected:
            text = f'🤖 Ollama: Connected'
            if model:
                text += f' ({model})'
            color = AEGISTheme.get_color('success')
        else:
            text = '🤖 Ollama: Offline'
            color = AEGISTheme.get_color('error')
        
        self.ollama_lbl.configure(text=text, text_color=color)
    
    def update_storage(self, used_gb: float, total_gb: float, percentage: float):
        self.storage_lbl.configure(text=f'📊 Storage: {used_gb:.1f}/{total_gb:.0f}GB ({percentage:.0f}%)')
    
    def update_system(self, status: str, color: str = None):
        from gui.theme import AEGISTheme
        if color is None:
            color = AEGISTheme.get_color('success')
        self.system_lbl.configure(text=status, text_color=color)
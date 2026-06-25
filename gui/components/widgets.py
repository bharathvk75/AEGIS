import customtkinter as ctk
import threading
import time
from typing import Dict, Callable, Optional, List
from datetime import datetime


class CameraTile(ctk.CTkFrame):
    def __init__(self, master, camera_id: int, name: str, **kwargs):
        super().__init__(master, **kwargs)
        self.camera_id = camera_id
        self.name = name
        self._setup_style()
        self._create_widgets()
        self._status = 'disconnected'
        self._fps = 0
        self._update_thread = None
        self._running = False
        self._image_label = None
        self._frame_callback = None
    
    def _setup_style(self):
        from gui.theme import AEGISTheme
        self.configure(
            fg_color=AEGISTheme.get_color('card_bg'),
            corner_radius=AEGISTheme.RADIUS['large']
        )
    
    def _create_widgets(self):
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.pack(fill='x', padx=12, pady=(10, 5))
        
        self.status_indicator = ctk.CTkLabel(
            self.header,
            text='●',
            font=('Inter', 12, 'bold'),
            text_color=self._get_color('error')
        )
        self.status_indicator.pack(side='left')
        
        self.name_label = ctk.CTkLabel(
            self.header,
            text=self.name,
            font=('Inter', 14, 'bold'),
            text_color=self._get_color('text_primary')
        )
        self.name_label.pack(side='left', padx=(8, 0))
        
        self.fps_label = ctk.CTkLabel(
            self.header,
            text='0 FPS',
            font=('Inter', 11, 'normal'),
            text_color=self._get_color('text_muted')
        )
        self.fps_label.pack(side='right')
        
        self.video_frame = ctk.CTkFrame(
            self,
            height=160,
            fg_color=self._get_color('primary_bg'),
            corner_radius=AEGISTheme.RADIUS['medium']
        )
        self.video_frame.pack(fill='both', expand=True, padx=12, pady=5)
        self.video_frame.pack_propagate(False)
        
        self.placeholder = ctk.CTkLabel(
            self.video_frame,
            text='📷\nNo Signal',
            font=('Inter', 16, 'normal'),
            text_color=self._get_color('text_muted')
        )
        self.placeholder.pack(expand=True)
        
        self.footer = ctk.CTkFrame(self, fg_color='transparent')
        self.footer.pack(fill='x', padx=12, pady=(5, 10))
        
        self.last_event = ctk.CTkLabel(
            self.footer,
            text='--',
            font=('Inter', 10, 'normal'),
            text_color=self._get_color('text_muted')
        )
        self.last_event.pack(side='left')
    
    def _get_color(self, key):
        from gui.theme import AEGISTheme
        return AEGISTheme.get_color(key)
    
    @property
    def status(self) -> str:
        return self._status
    
    @status.setter
    def status(self, value: str):
        self._status = value
        color = self._get_color('success') if value == 'connected' else self._get_color('error') if value == 'failed' else self._get_color('warning')
        self.status_indicator.configure(text='●', text_color=color)
        
        if value == 'connected':
            self.placeholder.configure(text='📷\nConnecting...')
        elif value == 'failed':
            self.placeholder.configure(text='⚠️\nConnection Failed')
        else:
            self.placeholder.configure(text='📷\nNo Signal')
    
    def set_frame_callback(self, callback: Callable):
        self._frame_callback = callback
    
    def update_frame(self, frame_data: bytes):
        if frame_data:
            try:
                from PIL import Image
                import io
                
                img = Image.open(io.BytesIO(frame_data))
                img = img.resize((320, 180), Image.LANCZOS)
                
                ctk_img = ctk.CTkImage(img, size=(320, 180))
                
                if self._image_label is None:
                    self._image_label = ctk.CTkLabel(self.video_frame, text='', image=ctk_img)
                    self._image_label.pack(expand=True)
                    self.placeholder.pack_forget()
                else:
                    self._image_label.configure(image=ctk_img)
                
                self.status = 'connected'
            except Exception as e:
                print(f"Error updating frame: {e}")
    
    def update_fps(self, fps: int):
        self._fps = fps
        self.fps_label.configure(text=f'{fps} FPS')
    
    def update_last_event(self, event_text: str):
        self.last_event.configure(text=event_text)
    
    def start_updates(self, frame_getter: Callable):
        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop, args=(frame_getter,), daemon=True)
        self._update_thread.start()
    
    def stop_updates(self):
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=1)
    
    def _update_loop(self, frame_getter: Callable):
        while self._running:
            try:
                frame_data = frame_getter(self.camera_id)
                if frame_data and self._frame_callback:
                    self._frame_callback(frame_data)
                time.sleep(0.1)
            except Exception:

                pass
    
    def set_placeholder(self, text: str):
        self.placeholder.configure(text=text)


class CameraGrid(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._tiles: Dict[int, CameraTile] = {}
        self._setup_style()
    
    def _setup_style(self):
        from gui.theme import AEGISTheme
        self.configure(fg_color='transparent')
    
    def add_camera(self, camera_id: int, name: str, **kwargs) -> CameraTile:
        if camera_id in self._tiles:
            return self._tiles[camera_id]
        
        tile = CameraTile(self, camera_id, name, fg_color='transparent')
        self._tiles[camera_id] = tile
        self._relayout()
        return tile
    
    def remove_camera(self, camera_id: int):
        if camera_id in self._tiles:
            self._tiles[camera_id].destroy()
            del self._tiles[camera_id]
            self._relayout()
    
    def get_tile(self, camera_id: int) -> Optional[CameraTile]:
        return self._tiles.get(camera_id)
    
    def get_all_tiles(self) -> Dict[int, CameraTile]:
        return self._tiles.copy()
    
    def clear(self):
        for tile in list(self._tiles.values()):
            tile.destroy()
        self._tiles.clear()
    
    def _relayout(self):
        pass
    
    def update_layout(self, columns: int = 2):
        tiles = list(self._tiles.values())
        for i, tile in enumerate(tiles):
            tile.grid(row=i // columns, column=i % columns, padx=8, pady=8, sticky='nsew')
        
        for i in range(columns):
            self.grid_columnconfigure(i, weight=1, uniform='camera_grid')


class EventFeed(ctk.CTkFrame):
    def __init__(self, master, max_items: int = 50, **kwargs):
        super().__init__(master, **kwargs)
        self.max_items = max_items
        self._events: List[Dict] = []
        self._setup_style()
        self._create_widgets()
        self._callbacks: List[Callable] = []
    
    def _setup_style(self):
        from gui.theme import AEGISTheme
        self.configure(
            fg_color=AEGISTheme.get_color('card_bg'),
            corner_radius=AEGISTheme.RADIUS['large']
        )
    
    def _create_widgets(self):
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(12, 8))
        
        title = ctk.CTkLabel(
            header,
            text='📜 Live Event Feed',
            font=('Inter', 14, 'bold'),
            text_color=self._get_color('text_primary')
        )
        title.pack(side='left')
        
        clear_btn = ctk.CTkButton(
            header,
            text='Clear',
            font=('Inter', 11, 'normal'),
            fg_color='transparent',
            text_color=self._get_color('text_muted'),
            hover_color=self._get_color('hover'),
            width=50,
            height=28,
            corner_radius=6,
            command=self.clear
        )
        clear_btn.pack(side='right')
        
        divider = ctk.CTkFrame(self, height=1, fg_color=self._get_color('border'))
        divider.pack(fill='x', padx=15)
        
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent',
            scrollbar_button_color=self._get_color('card_bg'),
            scrollbar_button_hover_color=self._get_color('hover')
        )
        self.scroll_frame.pack(fill='both', expand=True, padx=10, pady=(5, 10))
        self.scroll_frame.pack_propagate(False)
        
        self.empty_label = ctk.CTkLabel(
            self.scroll_frame,
            text='No events yet',
            font=('Inter', 12, 'normal'),
            text_color=self._get_color('text_muted')
        )
        self.empty_label.pack(pady=20)
    
    def _get_color(self, key):
        from gui.theme import AEGISTheme
        return AEGISTheme.get_color(key)
    
    def add_event(self, event: Dict):
        self._events.insert(0, {
            **event,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        if len(self._events) > self.max_items:
            self._events.pop()
        
        self._render_events()
        
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:

                pass
    
    def _render_events(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        if not self._events:
            self.empty_label.pack(pady=20)
            return
        
        self.empty_label.pack_forget()
        
        for event in self._events:
            self._create_event_item(event)
    
    def _create_event_item(self, event: Dict):
        severity = event.get('severity', 'info')
        severity_icons = {
            'critical': '🔴',
            'warning': '🟡',
            'info': '🟢'
        }
        severity_colors = {
            'critical': self._get_color('error'),
            'warning': self._get_color('warning'),
            'info': self._get_color('success')
        }
        
        item = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self._get_color('primary_bg'),
            corner_radius=8
        )
        item.pack(fill='x', pady=3, ipady=8)
        
        time_label = ctk.CTkLabel(
            item,
            text=f"[{event.get('timestamp', '--:--:--')}]",
            font=('Inter', 10, 'normal'),
            text_color=self._get_color('text_muted')
        )
        time_label.pack(anchor='w', padx=(10, 0), pady=(5, 0))
        
        content = ctk.CTkFrame(item, fg_color='transparent')
        content.pack(fill='x', padx=10, pady=(2, 0))
        
        icon = severity_icons.get(severity, '🟢')
        icon_label = ctk.CTkLabel(
            content,
            text=icon,
            font=('Inter', 11, 'normal')
        )
        icon_label.pack(side='left')
        
        desc = event.get('description', event.get('event_type', 'Event'))
        desc_label = ctk.CTkLabel(
            content,
            text=f"{event.get('camera_name', 'Camera')}: {desc}",
            font=('Inter', 12, 'normal'),
            text_color=self._get_color('text_primary')
        )
        desc_label.pack(side='left', padx=(5, 0))
        
        conf = event.get('confidence', 0)
        if conf > 0:
            conf_label = ctk.CTkLabel(
                content,
                text=f"({conf*100:.0f}%)",
                font=('Inter', 10, 'normal'),
                text_color=severity_colors.get(severity, self._get_color('text_muted'))
            )
            conf_label.pack(side='right')
    
    def clear(self):
        self._events.clear()
        self._render_events()
    
    def register_callback(self, callback: Callable):
        self._callbacks.append(callback)
    
    def get_events(self) -> List[Dict]:
        return self._events.copy()


class Modal(ctk.CTkToplevel):
    def __init__(self, master, title: str = '', width: int = 500, height: int = 400, **kwargs):
        super().__init__(master, **kwargs)
        self._configure_modal(master, title, width, height)
        self._create_header(title)
        self._content_frame = None
        self._result = None
    
    def _configure_modal(self, master, title: str, width: int, height: int):
        from gui.theme import AEGISTheme
        
        self.title(title)
        self.geometry(f'{width}x{height}')
        self.resizable(False, False)
        
        self.configure(fg_color=AEGISTheme.get_color('primary_bg'))
        self.transient(master.winfo_toplevel())
        self.grab_set()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f'+{x}+{y}')
        
        self.bind('<Escape>', lambda e: self.destroy())
    
    def _create_header(self, title: str):
        from gui.theme import AEGISTheme
        
        header = ctk.CTkFrame(self, fg_color=AEGISTheme.get_color('secondary_bg'), height=50)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        title_label.pack(side='left', padx=20, pady=10)
        
        close_btn = ctk.CTkButton(
            header,
            text='×',
            width=40,
            height=40,
            fg_color='transparent',
            text_color=AEGISTheme.get_color('text_muted'),
            hover_color=AEGISTheme.get_color('hover'),
            font=('Inter', 20, 'normal'),
            corner_radius=8,
            command=self.destroy
        )
        close_btn.pack(side='right', padx=10, pady=5)
    
    def get_content_frame(self) -> ctk.CTkFrame:
        if self._content_frame is None:
            from gui.theme import AEGISTheme
            self._content_frame = ctk.CTkFrame(self, fg_color='transparent')
            self._content_frame.pack(fill='both', expand=True, padx=20, pady=15)
        return self._content_frame
    
    def set_result(self, result):
        self._result = result
        self.destroy()
    
    def get_result(self):
        return self._result


class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=32, **kwargs)
        self._setup_style()
        self._create_elements()
    
    def _setup_style(self):
        from gui.theme import AEGISTheme
        self.configure(
            fg_color=AEGISTheme.get_color('secondary_bg'),
            height=32,
            corner_radius=0
        )
    
    def _create_elements(self):
        from gui.theme import AEGISTheme
        
        self.ollama_status = ctk.CTkLabel(
            self,
            text='🤖 Ollama: --',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('text_muted')
        )
        self.ollama_status.pack(side='left', padx=15)
        
        self.storage_status = ctk.CTkLabel(
            self,
            text='📊 Storage: --',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('text_muted')
        )
        self.storage_status.pack(side='left', padx=15)
        
        self.system_status = ctk.CTkLabel(
            self,
            text='🟢 System Ready',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('success')
        )
        self.system_status.pack(side='right', padx=15)
    
    def update_ollama(self, connected: bool, model: str = None):
        from gui.theme import AEGISTheme
        if connected:
            text = f'🤖 Ollama: Connected'
            if model:
                text += f' ({model})'
            color = AEGISTheme.get_color('success')
        else:
            text = '🤖 Ollama: Disconnected'
            color = AEGISTheme.get_color('error')
        self.ollama_status.configure(text=text, text_color=color)
    
    def update_storage(self, used_gb: float, total_gb: float, percentage: float):
        from gui.theme import AEGISTheme
        self.storage_status.configure(
            text=f'📊 Storage: {used_gb:.1f}/{total_gb:.0f}GB ({percentage:.0f}%)'
        )
    
    def update_system(self, status: str, color: str = None):
        from gui.theme import AEGISTheme
        if color is None:
            color = AEGISTheme.get_color('success')
        self.system_status.configure(text=f'{status}', text_color=color)
"""
AEGIS Dashboard — Premium Landing Page
Stat cards with animated counters, camera grid with status indicators,
and a live event feed with severity-tinted items.
"""
import customtkinter as ctk
import threading
import time
from datetime import datetime


class DashboardPage(ctk.CTkFrame):
    
    def __init__(self, master, **kwargs):
        from gui.theme import AEGISTheme as T
        super().__init__(master, fg_color=T.get_color('bg_base'), **kwargs)
        self._update_thread = None
        self._running = False
        self._build()
    
    def _build(self):
        from gui.theme import AEGISTheme as T
        
        # Scrollable container for the entire dashboard
        scroll = ctk.CTkScrollableFrame(
            self, fg_color='transparent',
            scrollbar_button_color=T.get_color('bg_surface'),
            scrollbar_button_hover_color=T.get_color('hover')
        )
        scroll.pack(fill='both', expand=True, padx=0, pady=0)
        
        # ── Page Header ──────────────────────────────────────────────────
        header = ctk.CTkFrame(scroll, fg_color='transparent')
        header.pack(fill='x', padx=28, pady=(24, 0))
        
        title_block = ctk.CTkFrame(header, fg_color='transparent')
        title_block.pack(side='left')
        
        ctk.CTkLabel(
            title_block, text='Dashboard',
            font=T.get_font('display'),
            text_color=T.get_color('text_primary')
        ).pack(anchor='w')
        
        ctk.CTkLabel(
            title_block, text='System overview and real-time monitoring',
            font=T.get_font('body_sm'),
            text_color=T.get_color('text_tertiary')
        ).pack(anchor='w', pady=(2, 0))
        
        # Live indicator in header
        live_badge = ctk.CTkFrame(header, fg_color=T.get_color('success_surface'),
                                   corner_radius=T.get_radius('pill'))
        live_badge.pack(side='right', pady=8)
        
        self._live_dot = ctk.CTkLabel(
            live_badge, text='●',
            font=('Inter', 8, 'normal'),
            text_color=T.get_color('success')
        )
        self._live_dot.pack(side='left', padx=(10, 4), pady=6)
        
        ctk.CTkLabel(
            live_badge, text='LIVE',
            font=T.get_font('overline'),
            text_color=T.get_color('success')
        ).pack(side='left', padx=(0, 10), pady=6)
        
        # ── Stat Cards Row ───────────────────────────────────────────────
        stats_row = ctk.CTkFrame(scroll, fg_color='transparent')
        stats_row.pack(fill='x', padx=28, pady=(20, 0))
        stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform='stat')
        
        self.stat_cards = {}
        stat_defs = [
            ('cameras',  'Active Cameras',    '0',   T.get_color('accent'),  T.get_color('accent_surface')),
            ('events',   'Events Today',      '0',   T.get_color('teal'),    T.get_color('teal_surface')),
            ('alerts',   'Active Alerts',     '0',   T.get_color('warning'), T.get_color('warning_surface')),
            ('uptime',   'System Uptime',     '—',   T.get_color('success'), T.get_color('success_surface')),
        ]
        
        for i, (key, label, default_val, accent_color, surface_color) in enumerate(stat_defs):
            card = self._build_stat_card(stats_row, label, default_val, accent_color, surface_color)
            card.grid(row=0, column=i, padx=(0, 12) if i < 3 else 0, sticky='nsew')
            self.stat_cards[key] = card
        
        # ── Main Content Grid ────────────────────────────────────────────
        content = ctk.CTkFrame(scroll, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=28, pady=(16, 24))
        content.grid_columnconfigure(0, weight=5)
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)
        
        # Camera grid (left)
        self.grid_frame = CameraGridView(content)
        self.grid_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 12))
        
        # Event feed (right)
        self.event_feed = EventFeed(content, max_items=30)
        self.event_feed.grid(row=0, column=1, sticky='nsew')
        
        # Start live dot pulse
        self._pulse_live_dot()
    
    def _build_stat_card(self, parent, label, value, accent_color, surface_color):
        from gui.theme import AEGISTheme as T
        from gui.animations import HoverMixin
        
        card = ctk.CTkFrame(parent, fg_color=T.get_color('bg_surface'),
                            corner_radius=T.get_radius('lg'))
        
        # Top accent line
        accent_line = ctk.CTkFrame(card, height=3, fg_color=accent_color,
                                    corner_radius=2)
        accent_line.pack(fill='x', padx=16, pady=(14, 0))
        
        # Value
        val_label = ctk.CTkLabel(
            card, text=value,
            font=T.get_font('stat_number'),
            text_color=T.get_color('text_primary')
        )
        val_label.pack(anchor='w', padx=16, pady=(12, 0))
        card._value_label = val_label
        
        # Label
        ctk.CTkLabel(
            card, text=label,
            font=T.get_font('caption'),
            text_color=T.get_color('text_tertiary')
        ).pack(anchor='w', padx=16, pady=(2, 16))
        
        # Hover effect
        HoverMixin.setup_hover(card, T.get_color('bg_surface'), T.get_color('bg_surface_alt'))
        
        return card
    
    def _pulse_live_dot(self):
        from gui.animations import pulse_dot
        from gui.theme import AEGISTheme as T
        pulse_dot(self._live_dot, T.get_color('success'), T.get_color('text_disabled'), duration=2000)
    
    # ── Public API ────────────────────────────────────────────────────────────
    
    def on_show(self):
        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
    
    def on_hide(self):
        self._running = False
    
    def _update_loop(self):
        while self._running:
            self._update_stats()
            time.sleep(3)
    
    def _update_stats(self):
        try:
            from core.camera.capture import get_camera_manager
            from core.storage.database import get_db, Event
            
            cam_mgr = get_camera_manager()
            cameras = cam_mgr.get_all_cameras()
            active = sum(1 for cid in cameras if cam_mgr.get_source_status(cid) == 'connected')
            
            db = get_db()
            session = db.get_session()
            today = datetime.now().date()
            ev_count = session.query(Event).filter(
                Event.created_at >= datetime.combine(today, datetime.min.time())
            ).count()
            
            alert_count = session.query(Event).filter(
                Event.created_at >= datetime.combine(today, datetime.min.time()),
                Event.severity.in_(['warning', 'critical'])
            ).count()
            session.close()
            
            # Thread-safe GUI updates
            self.after(10, lambda a=active, total=len(cameras): self.stat_cards['cameras']._value_label.configure(text=f'{a}/{total}'))
            self.after(10, lambda e=ev_count: self.stat_cards['events']._value_label.configure(text=str(e)))
            self.after(10, lambda al=alert_count: self.stat_cards['alerts']._value_label.configure(text=str(al)))
        except Exception:
            pass
    
    def add_camera_tile(self, camera_id: int, name: str):
        return self.grid_frame.add_camera(camera_id, name)
    
    def remove_camera_tile(self, camera_id: int):
        self.grid_frame.remove_camera(camera_id)
    
    def update_camera_status(self, camera_id: int, status: str):
        tile = self.grid_frame.get_tile(camera_id)
        if tile:
            tile.status = status
    
    def update_camera_frame(self, camera_id: int, frame_data: bytes):
        tile = self.grid_frame.get_tile(camera_id)
        if tile:
            tile.update_frame(frame_data)
    
    def add_event(self, event_data: dict):
        self.event_feed.add_event(event_data)
    
    def reload_cameras(self):
        self.grid_frame.clear()
        try:
            from core.camera.capture import get_camera_manager
            cam_mgr = get_camera_manager()
            for cam_id, cam in cam_mgr.get_all_cameras().items():
                tile = self.add_camera_tile(cam_id, cam['name'])
                tile.start_updates(cam_mgr.get_frame_jpeg)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# Camera Grid
# ══════════════════════════════════════════════════════════════════════════════

class CameraGridView(ctk.CTkFrame):
    
    def __init__(self, master, columns: int = 2, **kwargs):
        from gui.theme import AEGISTheme as T
        super().__init__(master, fg_color=T.get_color('bg_surface'),
                         corner_radius=T.get_radius('lg'), **kwargs)
        self.columns = columns
        self._tiles = {}
        self._build_header()
        self._content = ctk.CTkFrame(self, fg_color='transparent')
        self._content.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        for i in range(columns):
            self._content.grid_columnconfigure(i, weight=1, uniform='cam')
        
        self._build_empty_state()
    
    def _build_header(self):
        from gui.theme import AEGISTheme as T
        
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=16, pady=(14, 8))
        
        ctk.CTkLabel(
            header, text='Camera Feeds',
            font=T.get_font('heading_sm'),
            text_color=T.get_color('text_primary')
        ).pack(side='left')
        
        self._cam_count = ctk.CTkLabel(
            header, text='0 sources',
            font=T.get_font('caption'),
            text_color=T.get_color('text_tertiary')
        )
        self._cam_count.pack(side='right')
    
    def _build_empty_state(self):
        from gui.theme import AEGISTheme as T
        
        self._empty = ctk.CTkFrame(self._content, fg_color='transparent')
        self._empty.grid(row=0, column=0, columnspan=self.columns, sticky='nsew', pady=40)
        
        ctk.CTkLabel(
            self._empty, text='◎',
            font=('Inter', 36, 'normal'),
            text_color=T.get_color('text_disabled')
        ).pack()
        
        ctk.CTkLabel(
            self._empty, text='No camera feeds',
            font=T.get_font('body'),
            text_color=T.get_color('text_tertiary')
        ).pack(pady=(8, 2))
        
        ctk.CTkLabel(
            self._empty, text='Add cameras in the Cameras tab to see live feeds here',
            font=T.get_font('caption'),
            text_color=T.get_color('text_disabled')
        ).pack()
    
    def add_camera(self, camera_id: int, name: str):
        if camera_id in self._tiles:
            return self._tiles[camera_id]
        
        if self._empty.winfo_ismapped():
            self._empty.grid_forget()
        
        tile = CameraTileView(self._content, camera_id, name)
        self._tiles[camera_id] = tile
        self._relayout()
        self._cam_count.configure(text=f'{len(self._tiles)} source{"s" if len(self._tiles) != 1 else ""}')
        return tile
    
    def remove_camera(self, camera_id: int):
        if camera_id in self._tiles:
            self._tiles[camera_id].destroy()
            del self._tiles[camera_id]
            self._relayout()
            self._cam_count.configure(text=f'{len(self._tiles)} source{"s" if len(self._tiles) != 1 else ""}')
            if not self._tiles:
                self._build_empty_state()
    
    def get_tile(self, camera_id: int):
        return self._tiles.get(camera_id)
    
    def clear(self):
        for tile in list(self._tiles.values()):
            tile.destroy()
        self._tiles.clear()
    
    def _relayout(self):
        for i, tile in enumerate(self._tiles.values()):
            tile.grid(row=i // self.columns, column=i % self.columns,
                      padx=4, pady=4, sticky='nsew')
        rows = max(1, (len(self._tiles) + self.columns - 1) // self.columns)
        for r in range(rows):
            self._content.grid_rowconfigure(r, weight=1, uniform='cam_row')


class CameraTileView(ctk.CTkFrame):
    
    def __init__(self, master, camera_id: int, name: str, **kwargs):
        from gui.theme import AEGISTheme as T
        super().__init__(master, fg_color=T.get_color('bg_inset'),
                         corner_radius=T.get_radius('md'), **kwargs)
        self.camera_id = camera_id
        self.name = name
        self._status = 'connecting'
        self._build()
    
    def _build(self):
        from gui.theme import AEGISTheme as T
        
        # Header bar
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=10, pady=(8, 4))
        
        self._status_dot = ctk.CTkLabel(
            header, text='●',
            font=('Inter', 9, 'normal'),
            text_color=T.get_color('warning')
        )
        self._status_dot.pack(side='left')
        
        ctk.CTkLabel(
            header, text=self.name,
            font=T.get_font('caption'),
            text_color=T.get_color('text_secondary')
        ).pack(side='left', padx=(6, 0))
        
        self._fps_label = ctk.CTkLabel(
            header, text='— fps',
            font=T.get_font('caption_sm'),
            text_color=T.get_color('text_disabled')
        ).pack(side='right')
        
        # Video container
        self._video = ctk.CTkFrame(
            self, height=120,
            fg_color=T.get_color('bg_base'),
            corner_radius=T.get_radius('sm')
        )
        self._video.pack(fill='both', expand=True, padx=8, pady=(0, 8))
        self._video.pack_propagate(False)
        
        self._placeholder = ctk.CTkLabel(
            self._video, text='◎\nConnecting...',
            font=T.get_font('caption'),
            text_color=T.get_color('text_disabled')
        )
        self._placeholder.pack(expand=True)
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        from gui.theme import AEGISTheme as T
        self._status = value
        color_map = {
            'connected': T.get_color('success'),
            'failed':    T.get_color('error'),
        }
        self._status_dot.configure(text_color=color_map.get(value, T.get_color('warning')))
        
        if value == 'connected':
            self._placeholder.configure(text='')
        elif value == 'failed':
            self._placeholder.configure(text='✕\nFailed')
        else:
            self._placeholder.configure(text='◎\nConnecting...')
    
    def update_frame(self, frame_data: bytes):
        if not frame_data:
            return
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(frame_data))
            img = img.resize((280, 150), Image.LANCZOS)
            ctk_img = ctk.CTkImage(img, size=(280, 150))
            
            if not hasattr(self, '_img_label') or self._img_label is None:
                for w in self._video.winfo_children():
                    w.destroy()
                self._img_label = ctk.CTkLabel(self._video, text='', image=ctk_img)
                self._img_label.pack(expand=True)
            else:
                self._img_label.configure(image=ctk_img)
            self.status = 'connected'
        except Exception:
            pass
    
    def update_fps(self, fps: int):
        pass  # fps label already built inline
    
    def update_last_event(self, text: str):
        pass
    
    def start_updates(self, frame_getter):
        self._running = True
        import threading
        self._update_thread = threading.Thread(target=self._update_loop, args=(frame_getter,), daemon=True)
        self._update_thread.start()
    
    def stop_updates(self):
        self._running = False
        if hasattr(self, '_update_thread') and self._update_thread:
            self._update_thread.join(timeout=1)
            
    def _update_loop(self, frame_getter):
        import time
        while getattr(self, '_running', False):
            try:
                frame_data = frame_getter(self.camera_id)
                if frame_data:
                    self.after(0, lambda f=frame_data: self.update_frame(f))
                time.sleep(0.1)
            except Exception:
                pass
    
    def set_placeholder(self, text: str):
        self._placeholder.configure(text=text)


# ══════════════════════════════════════════════════════════════════════════════
# Event Feed
# ══════════════════════════════════════════════════════════════════════════════

class EventFeed(ctk.CTkFrame):
    
    SEVERITY_CONFIG = {
        'critical': {'icon': '●', 'color_key': 'error',   'surface_key': 'error_surface'},
        'warning':  {'icon': '●', 'color_key': 'warning', 'surface_key': 'warning_surface'},
        'info':     {'icon': '●', 'color_key': 'success', 'surface_key': 'success_surface'},
    }
    
    def __init__(self, master, max_items: int = 50, **kwargs):
        from gui.theme import AEGISTheme as T
        super().__init__(master, fg_color=T.get_color('bg_surface'),
                         corner_radius=T.get_radius('lg'), **kwargs)
        self.max_items = max_items
        self._events = []
        self._callbacks = []
        self._build()
    
    def _build(self):
        from gui.theme import AEGISTheme as T
        
        # Header
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=16, pady=(14, 0))
        
        ctk.CTkLabel(
            header, text='Event Feed',
            font=T.get_font('heading_sm'),
            text_color=T.get_color('text_primary')
        ).pack(side='left')
        
        ctk.CTkButton(
            header, text='Clear',
            font=T.get_font('button_sm'),
            fg_color='transparent',
            text_color=T.get_color('text_disabled'),
            hover_color=T.get_color('hover'),
            width=50, height=24,
            corner_radius=T.get_radius('sm'),
            command=self.clear
        ).pack(side='right')
        
        # Divider
        ctk.CTkFrame(self, height=1, fg_color=T.get_color('border_subtle')).pack(
            fill='x', padx=16, pady=(10, 0))
        
        # Scrollable event list
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color='transparent',
            scrollbar_button_color=T.get_color('bg_surface'),
            scrollbar_button_hover_color=T.get_color('hover')
        )
        self._scroll.pack(fill='both', expand=True, padx=8, pady=(8, 12))
        
        self._empty_label = ctk.CTkLabel(
            self._scroll, text='No events recorded',
            font=T.get_font('caption'),
            text_color=T.get_color('text_disabled')
        )
        self._empty_label.pack(pady=24)
    
    def add_event(self, event: dict):
        self._events.insert(0, {
            **event,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        if len(self._events) > self.max_items:
            self._events.pop()
        self._render()
        
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception:

                pass
    
    def _render(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        
        if not self._events:
            self._empty_label = ctk.CTkLabel(
                self._scroll, text='No events recorded',
                font=('Inter', 11, 'normal'),
                text_color='#464D66'
            )
            self._empty_label.pack(pady=24)
            return
        
        from gui.theme import AEGISTheme as T
        
        for event in self._events:
            self._build_event_item(event)
    
    def _build_event_item(self, event: dict):
        from gui.theme import AEGISTheme as T
        
        severity = event.get('severity', 'info')
        cfg = self.SEVERITY_CONFIG.get(severity, self.SEVERITY_CONFIG['info'])
        
        item = ctk.CTkFrame(
            self._scroll,
            fg_color=T.get_color('bg_inset'),
            corner_radius=T.get_radius('sm')
        )
        item.pack(fill='x', pady=2, ipady=6)
        
        # Left color stripe
        stripe = ctk.CTkFrame(item, width=3, fg_color=T.get_color(cfg['color_key']),
                               corner_radius=2)
        stripe.pack(side='left', fill='y', padx=(6, 8), pady=6)
        
        # Content
        content = ctk.CTkFrame(item, fg_color='transparent')
        content.pack(side='left', fill='both', expand=True, pady=4)
        
        # Top row — description
        desc = event.get('description', event.get('event_type', 'Event'))
        camera = event.get('camera_name', 'System')
        
        ctk.CTkLabel(
            content, text=f'{camera}: {desc}',
            font=T.get_font('caption'),
            text_color=T.get_color('text_secondary'),
            anchor='w'
        ).pack(anchor='w')
        
        # Bottom row — timestamp + confidence
        meta = ctk.CTkFrame(content, fg_color='transparent')
        meta.pack(anchor='w')
        
        ctk.CTkLabel(
            meta, text=event.get('timestamp', ''),
            font=T.get_font('caption_sm'),
            text_color=T.get_color('text_disabled')
        ).pack(side='left')
        
        conf = event.get('confidence', 0)
        if conf > 0:
            ctk.CTkLabel(
                meta, text=f'  ·  {conf*100:.0f}%',
                font=T.get_font('caption_sm'),
                text_color=T.get_color(cfg['color_key'])
            ).pack(side='left')
    
    def clear(self):
        self._events.clear()
        self._render()
    
    def register_callback(self, cb):
        self._callbacks.append(cb)
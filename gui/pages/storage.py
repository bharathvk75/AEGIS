import customtkinter as ctk
import threading


class StoragePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._setup_style()
        self._create_widgets()
        self._load_storage_data()
    
    def _setup_style(self):
        from gui.theme import AEGISTheme
        self.configure(fg_color=AEGISTheme.get_color('primary_bg'))
    
    def _create_widgets(self):
        from gui.theme import AEGISTheme
        
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            header,
            text='Storage Management',
            font=('Inter', 22, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(side='left')
        
        content = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent',
            scrollbar_button_color=AEGISTheme.get_color('card_bg')
        )
        content.pack(fill='both', expand=True, padx=15, pady=10)
        
        self._create_overview_section(content)
        self._create_breakdown_section(content)
        self._create_retention_section(content)
        self._create_volumes_section(content)
    
    def _create_overview_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x', pady=(0, 15))
        
        ctk.CTkLabel(
            section,
            text='💾 Storage Overview',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(anchor='w', padx=15, pady=(15, 10))
        
        self.usage_progress = ctk.CTkProgressBar(
            section,
            height=20,
            fg_color=AEGISTheme.get_color('secondary_bg'),
            progress_color=AEGISTheme.get_color('accent'),
            corner_radius=10
        )
        self.usage_progress.pack(fill='x', padx=15, pady=(0, 5))
        
        self.usage_label = ctk.CTkLabel(
            section,
            text='Used: 0 GB / 50 GB (0%)',
            font=('Inter', 12, 'normal'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        self.usage_label.pack(anchor='w', padx=15)
        
        settings = ctk.CTkFrame(section, fg_color='transparent')
        settings.pack(fill='x', padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            settings,
            text='Max Storage:',
            font=('Inter', 12, 'normal'),
            text_color=AEGISTheme.get_color('text_secondary')
        ).pack(side='left', padx=(0, 10))
        
        self.max_storage_slider = ctk.CTkSlider(
            settings,
            from_=5,
            to=500,
            number_of_steps=99,
            fg_color=AEGISTheme.get_color('secondary_bg'),
            progress_color=AEGISTheme.get_color('accent'),
            button_color=AEGISTheme.get_color('accent'),
            button_hover_color=AEGISTheme.get_color('accent_hover')
        )
        self.max_storage_slider.set(50)
        self.max_storage_slider.pack(side='left', padx=(0, 10))
        
        self.max_storage_label = ctk.CTkLabel(
            settings,
            text='50 GB',
            font=('Inter', 12, 'normal'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        self.max_storage_label.pack(side='left', padx=(0, 20))
        
        self.max_storage_slider.bind('<B1-Motion>', lambda e: self.max_storage_label.configure(text=f'{int(self.max_storage_slider.get())} GB'))
        
        self.auto_erase_switch = ctk.CTkSwitch(
            settings,
            text='Auto-Erase',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            progress_color=AEGISTheme.get_color('accent'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        self.auto_erase_switch.select()
        self.auto_erase_switch.pack(side='left')
        
        ctk.CTkButton(
            section,
            text='Save Settings',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            text_color='white',
            width=120,
            height=36,
            corner_radius=8,
            command=self._save_storage_settings
        ).pack(anchor='e', padx=15, pady=(10, 15))
    
    def _create_breakdown_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x', pady=(0, 15))
        
        ctk.CTkLabel(
            section,
            text='📁 Storage Breakdown',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(anchor='w', padx=15, pady=(15, 10))
        
        headers = ctk.CTkFrame(section, fg_color='transparent')
        headers.pack(fill='x', padx=15)
        
        for txt, w in [('Type', 1), ('Size', 0.8), ('Items', 0.6), ('Oldest', 1.5)]:
            ctk.CTkLabel(
                headers,
                text=txt,
                font=('Inter', 11, 'bold'),
                text_color=AEGISTheme.get_color('text_muted')
            ).pack(side='left', fill='x', expand=True)
        
        self.breakdown_items = ctk.CTkFrame(section, fg_color='transparent')
        self.breakdown_items.pack(fill='x', padx=15, pady=(5, 10))
        
        self._load_breakdown()
        
        btn_frame = ctk.CTkFrame(section, fg_color='transparent')
        btn_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        for label, cat in [('Clear Snapshots', 'snapshots'), ('Clear Clips', 'clips')]:
            ctk.CTkButton(
                btn_frame,
                text=label,
                font=('Inter', 11, 'normal'),
                fg_color=AEGISTheme.get_color('secondary_bg'),
                text_color=AEGISTheme.get_color('text_secondary'),
                hover_color=AEGISTheme.get_color('hover'),
                width=100,
                height=30,
                corner_radius=6,
                command=lambda c=cat: self._clear_category(c)
            ).pack(side='left', padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text='Clear All',
            font=('Inter', 11, 'normal'),
            fg_color=AEGISTheme.get_color('error'),
            text_color='white',
            hover_color='#DC2626',
            width=80,
            height=30,
            corner_radius=6,
            command=self._clear_all
        ).pack(side='right')
    
    def _create_retention_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x', pady=(0, 15))
        
        ctk.CTkLabel(
            section,
            text='⚙️ Retention Policies',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(anchor='w', padx=15, pady=(15, 15))
        
        retention_items = [
            ('snapshots', 'Snapshots:'),
            ('clips', 'Video Clips:'),
        ]
        
        self.retention_sliders = {}
        
        for key, label in retention_items:
            row = ctk.CTkFrame(section, fg_color='transparent')
            row.pack(fill='x', padx=15, pady=(0, 10))
            
            ctk.CTkLabel(
                row,
                text=label,
                font=('Inter', 12, 'normal'),
                text_color=AEGISTheme.get_color('text_secondary'),
                width=100
            ).pack(side='left')
            
            slider = ctk.CTkSlider(
                row,
                from_=1,
                to=30,
                number_of_steps=29,
                fg_color=AEGISTheme.get_color('secondary_bg'),
                progress_color=AEGISTheme.get_color('accent'),
                button_color=AEGISTheme.get_color('accent'),
                button_hover_color=AEGISTheme.get_color('accent_hover')
            )
            slider.set(7 if key == 'snapshots' else 3)
            slider.pack(side='left', fill='x', expand=True, padx=(0, 10))
            
            self.retention_sliders[key] = slider
            
            value_label = ctk.CTkLabel(
                row,
                text=f'{int(slider.get())} days',
                font=('Inter', 11, 'normal'),
                text_color=AEGISTheme.get_color('text_muted')
            )
            value_label.pack(side='right')
            
            slider.bind('<B1-Motion>', lambda e, s=slider, l=value_label, k=key: self._update_retention_label(s, l, k))
        
        ctk.CTkButton(
            section,
            text='Save Policies',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_accent'),
            hover_color='#5558E3',
            text_color='white',
            width=110,
            height=36,
            corner_radius=8,
            command=self._save_retention_policies
        ).pack(anchor='e', padx=15, pady=(5, 15))
    
    def _create_volumes_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x')
        
        ctk.CTkLabel(
            section,
            text='🗄️ Storage Locations',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(anchor='w', padx=15, pady=(15, 10))
        
        import os
        base_path = os.path.abspath('data/volumes')
        snapshots_path = os.path.join(base_path, 'snapshots')
        clips_path = os.path.join(base_path, 'clips')
        
        for label, path in [('Snapshots:', snapshots_path), ('Video Clips:', clips_path)]:
            row = ctk.CTkFrame(section, fg_color='transparent')
            row.pack(fill='x', padx=15, pady=(0, 8))
            
            ctk.CTkLabel(
                row,
                text=label,
                font=('Inter', 12, 'normal'),
                text_color=AEGISTheme.get_color('text_secondary'),
                width=100
            ).pack(side='left')
            
            ctk.CTkLabel(
                row,
                text=path,
                font=('Inter', 11, 'normal'),
                text_color=AEGISTheme.get_color('text_muted')
            ).pack(side='left')
        
        ctk.CTkButton(
            section,
            text='Open Folder',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            text_color=AEGISTheme.get_color('text_primary'),
            hover_color=AEGISTheme.get_color('hover'),
            width=100,
            height=32,
            corner_radius=6,
            command=self._open_volumes_folder
        ).pack(anchor='e', padx=15, pady=(10, 15))
    
    def _load_storage_data(self):
        try:
            from core.storage.storage_manager import get_storage
            storage = get_storage()
            
            used, total, percentage = storage.get_usage()
            self.usage_progress.set(percentage / 100)
            self.usage_label.configure(text=f'Used: {used / (1024**3):.1f} GB / {total / (1024**3):.0f} GB ({percentage:.0f}%)')
            self.max_storage_slider.set(total / (1024**3))
            self.max_storage_label.configure(text=f'{int(total / (1024**3))} GB')
            
            from core.config import get_config
            config = get_config()
            self.auto_erase_switch.select() if config.get('storage.auto_erase', True) else self.auto_erase_switch.deselect()
        except Exception as e:
            print(f"Error loading storage data: {e}")
    
    def _load_breakdown(self):
        from gui.theme import AEGISTheme
        
        for widget in self.breakdown_items.winfo_children():
            widget.destroy()
        
        try:
            from core.storage.storage_manager import get_storage
            storage = get_storage()
            breakdown = storage.get_breakdown()
            
            for cat, icon, size, count, oldest in [
                ('Snapshots', '📷', breakdown.get('snapshots', {}).get('size', 0), breakdown.get('snapshots', {}).get('count', 0), breakdown.get('snapshots', {}).get('oldest')),
                ('Video Clips', '🎬', breakdown.get('clips', {}).get('size', 0), breakdown.get('clips', {}).get('count', 0), breakdown.get('clips', {}).get('oldest'))
            ]:
                row = ctk.CTkFrame(self.breakdown_items, fg_color=AEGISTheme.get_color('secondary_bg'), corner_radius=6)
                row.pack(fill='x', pady=3, ipady=8)
                
                size_gb = size / (1024**3) if size else 0
                oldest_str = f"{oldest.get('days', 0)}d {oldest.get('hours', 0)}h ago" if oldest else 'Never'
                
                ctk.CTkLabel(
                    row,
                    text=f'{icon} {cat}',
                    font=('Inter', 11, 'normal'),
                    text_color=AEGISTheme.get_color('text_primary')
                ).pack(side='left', fill='x', expand=True, padx=10)
                
                ctk.CTkLabel(
                    row,
                    text=f'{size_gb:.1f} GB',
                    font=('Inter', 11, 'normal'),
                    text_color=AEGISTheme.get_color('text_secondary')
                ).pack(side='left', padx=5)
                
                ctk.CTkLabel(
                    row,
                    text=str(count),
                    font=('Inter', 11, 'normal'),
                    text_color=AEGISTheme.get_color('text_secondary')
                ).pack(side='left', padx=5)
                
                ctk.CTkLabel(
                    row,
                    text=oldest_str,
                    font=('Inter', 10, 'normal'),
                    text_color=AEGISTheme.get_color('text_muted')
                ).pack(side='left', padx=5)
        except Exception as e:
            print(f"Error loading breakdown: {e}")
    
    def _update_retention_label(self, slider, label, key):
        days = int(slider.get())
        label.configure(text=f'{days} days')
    
    def _save_storage_settings(self):
        try:
            from core.storage.storage_manager import get_storage
            from core.config import get_config
            
            storage = get_storage()
            max_gb = int(self.max_storage_slider.get())
            auto_erase = self.auto_erase_switch.get() == 1
            
            storage.update_settings(max_size_gb=max_gb, auto_erase=auto_erase)
            
            self.usage_progress.set(0)
            self.usage_label.configure(text=f'Used: 0 GB / {max_gb} GB (0%)')
            
            from gui.theme import AEGISTheme
        except Exception as e:
            print(f"Error saving storage settings: {e}")
    
    def _save_retention_policies(self):
        try:
            from core.storage.storage_manager import get_storage
            
            retention = {
                'snapshots_days': int(self.retention_sliders['snapshots'].get()),
                'clips_days': int(self.retention_sliders['clips'].get()),
                'logs_days': 30
            }
            
            storage = get_storage()
            storage.update_settings(retention=retention)
        except Exception as e:
            print(f"Error saving retention policies: {e}")
    
    def _clear_category(self, category: str):
        try:
            from core.storage.storage_manager import get_storage
            storage = get_storage()
            count = storage.clear_category(category)
            self._load_storage_data()
            self._load_breakdown()
        except Exception as e:
            print(f"Error clearing category: {e}")
    
    def _clear_all(self):
        try:
            from core.storage.storage_manager import get_storage
            storage = get_storage()
            storage.clear_category('snapshots')
            storage.clear_category('clips')
            self._load_storage_data()
            self._load_breakdown()
        except Exception as e:
            print(f"Error clearing all: {e}")
    
    def _open_volumes_folder(self):
        import os
        import subprocess
        path = os.path.abspath('data/volumes')
        if os.path.exists(path):
            subprocess.run(['explorer', path])
    
    def on_show(self):
        self._load_storage_data()
        self._load_breakdown()
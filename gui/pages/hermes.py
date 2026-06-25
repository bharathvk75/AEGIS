import customtkinter as ctk
import threading
import asyncio


class HermesPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._setup_style()
        self._create_widgets()
        self._load_data()
    
    def _setup_style(self):
        from gui.theme import AEGISTheme
        self.configure(fg_color=AEGISTheme.get_color('primary_bg'))
    
    def _create_widgets(self):
        from gui.theme import AEGISTheme
        
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=20, pady=(15, 10))
        
        title = ctk.CTkLabel(
            header,
            text='Hermes Agent - Smart Notification System',
            font=('Inter', 22, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        title.pack(side='left')
        
        content = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent',
            scrollbar_button_color=AEGISTheme.get_color('card_bg')
        )
        content.pack(fill='both', expand=True, padx=15, pady=10)
        
        self._create_status_section(content)
        self._create_triggers_section(content)
        self._create_channels_section(content)
    
    def _create_status_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x', pady=(0, 15))
        
        header = ctk.CTkFrame(section, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(15, 5))
        
        ctk.CTkLabel(
            header,
            text='🤖 Agent Status',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(side='left')
        
        self.agent_status = ctk.CTkLabel(
            header,
            text='◉ Active',
            font=('Inter', 12, 'normal'),
            text_color=AEGISTheme.get_color('success')
        )
        self.agent_status.pack(side='right')
        
        self.stats_frame = ctk.CTkFrame(section, fg_color='transparent')
        self.stats_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        self.stats_labels = {}
        stats = [
            ('triggers', 'Triggers Active'),
            ('notifications', 'Notifications Sent'),
            ('uptime', 'Uptime'),
        ]
        
        for i, (key, label) in enumerate(stats):
            col = ctk.CTkFrame(self.stats_frame, fg_color=AEGISTheme.get_color('secondary_bg'), corner_radius=8)
            col.pack(side='left', fill='both', expand=True, padx=(0, 8) if i < len(stats) - 1 else 0)
            
            self.stats_labels[key] = ctk.CTkLabel(
                col,
                text='0',
                font=('Inter', 24, 'bold'),
                text_color=AEGISTheme.get_color('accent')
            )
            self.stats_labels[key].pack(pady=(15, 0))
            
            ctk.CTkLabel(
                col,
                text=label,
                font=('Inter', 11, 'normal'),
                text_color=AEGISTheme.get_color('text_muted')
            ).pack(pady=(0, 10))
    
    def _create_triggers_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x', pady=(0, 15))
        
        header = ctk.CTkFrame(section, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(15, 5))
        
        ctk.CTkLabel(
            header,
            text='📋 Active Triggers',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(side='left')
        
        add_btn = ctk.CTkButton(
            header,
            text='+ Add Trigger',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            text_color='white',
            width=100,
            height=32,
            corner_radius=6,
            command=self._show_add_trigger_modal
        )
        add_btn.pack(side='right')
        
        self.triggers_list = ctk.CTkFrame(section, fg_color='transparent')
        self.triggers_list.pack(fill='x', padx=15, pady=(0, 10))
    
    def _create_channels_section(self, parent):
        from gui.theme import AEGISTheme
        
        section = ctk.CTkFrame(parent, fg_color=AEGISTheme.get_color('card_bg'), corner_radius=12)
        section.pack(fill='x')
        
        header = ctk.CTkFrame(section, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(15, 5))
        
        ctk.CTkLabel(
            header,
            text='📢 Notification Channels',
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(side='left')
        
        add_btn = ctk.CTkButton(
            header,
            text='+ Add Channel',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_accent'),
            hover_color='#5558E3',
            text_color='white',
            width=110,
            height=32,
            corner_radius=6,
            command=self._show_add_channel_modal
        )
        add_btn.pack(side='right')
        
        self.channels_grid = ctk.CTkFrame(section, fg_color='transparent')
        self.channels_grid.pack(fill='x', padx=15, pady=(0, 15))
    
    def _load_data(self):
        self._load_triggers()
        self._load_channels()
        self._update_stats()
    
    def _load_triggers(self):
        from gui.theme import AEGISTheme
        
        for widget in self.triggers_list.winfo_children():
            widget.destroy()
        
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            triggers = hermes.get_all_triggers()
            
            if not triggers:
                ctk.CTkLabel(
                    self.triggers_list,
                    text='No triggers configured. Add one to start receiving alerts.',
                    font=('Inter', 12, 'normal'),
                    text_color=AEGISTheme.get_color('text_muted')
                ).pack(pady=15)
                return
            
            for trigger_id, trigger in triggers.items():
                self._create_trigger_item(trigger)
        except Exception as e:
            print(f"Error loading triggers: {e}")
    
    def _create_trigger_item(self, trigger: dict):
        from gui.theme import AEGISTheme
        
        item = ctk.CTkFrame(
            self.triggers_list,
            fg_color=AEGISTheme.get_color('secondary_bg'),
            corner_radius=8
        )
        item.pack(fill='x', pady=4, ipady=10)
        
        header = ctk.CTkFrame(item, fg_color='transparent')
        header.pack(fill='x', padx=12, pady=(8, 3))
        
        status_color = AEGISTheme.get_color('success') if trigger.get('enabled') else AEGISTheme.get_color('text_muted')
        ctk.CTkLabel(
            header,
            text='🚨' if trigger.get('enabled') else '⏸',
            font=('Inter', 14, 'normal'),
            text_color=status_color
        ).pack(side='left')
        
        ctk.CTkLabel(
            header,
            text=trigger.get('name', 'Unnamed Trigger'),
            font=('Inter', 14, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack(side='left', padx=8)
        
        row2 = ctk.CTkFrame(item, fg_color='transparent')
        row2.pack(fill='x', padx=12, pady=(0, 8))
        
        ctk.CTkLabel(
            row2,
            text=f"Condition: {trigger.get('condition_text', '')[:50]}...",
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('text_secondary')
        ).pack(anchor='w')
        
        btn_frame = ctk.CTkFrame(item, fg_color='transparent')
        btn_frame.pack(fill='x', padx=12, pady=(0, 5))
        
        edit_btn = ctk.CTkButton(
            btn_frame,
            text='Edit',
            font=('Inter', 11, 'normal'),
            fg_color='transparent',
            text_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('hover'),
            width=60,
            height=28,
            corner_radius=6,
            command=lambda: self._show_edit_trigger_modal(trigger)
        )
        edit_btn.pack(side='left')
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text='Delete',
            font=('Inter', 11, 'normal'),
            fg_color='transparent',
            text_color=AEGISTheme.get_color('error'),
            hover_color=AEGISTheme.get_color('hover'),
            width=60,
            height=28,
            corner_radius=6,
            command=lambda: self._delete_trigger(trigger.get('id'))
        )
        delete_btn.pack(side='left', padx=8)
        
        toggle_text = 'Disable' if trigger.get('enabled') else 'Enable'
        toggle_btn = ctk.CTkButton(
            btn_frame,
            text=toggle_text,
            font=('Inter', 11, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_accent'),
            text_color='white',
            hover_color='#5558E3',
            width=70,
            height=28,
            corner_radius=6,
            command=lambda: self._toggle_trigger(trigger)
        )
        toggle_btn.pack(side='right')
    
    def _load_channels(self):
        from gui.theme import AEGISTheme
        
        for widget in self.channels_grid.winfo_children():
            widget.destroy()
        
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            channels = hermes.get_all_channels()
            
            if not channels:
                for txt, icon in [('Telegram', '📱'), ('Discord', '🌐'), ('SMS', '📞'), ('WhatsApp', '💬'), ('Webhook', '🔗')]:
                    self._create_channel_placeholder(txt, icon)
                return
            
            for channel_id, channel in channels.items():
                self._create_channel_item(channel_id, channel)
        except Exception as e:
            print(f"Error loading channels: {e}")
    
    def _create_channel_placeholder(self, name: str, icon: str):
        from gui.theme import AEGISTheme
        
        item = ctk.CTkFrame(
            self.channels_grid,
            fg_color=AEGISTheme.get_color('secondary_bg'),
            corner_radius=8
        )
        item.pack(side='left', fill='both', expand=True, padx=4, pady=8)
        
        ctk.CTkLabel(
            item,
            text=icon,
            font=('Inter', 24, 'normal')
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            item,
            text=name,
            font=('Inter', 12, 'normal'),
            text_color=AEGISTheme.get_color('text_secondary')
        ).pack()
        
        add_btn = ctk.CTkButton(
            item,
            text='+ Add',
            font=('Inter', 11, 'normal'),
            fg_color='transparent',
            text_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('hover'),
            width=60,
            height=26,
            corner_radius=6,
            command=lambda n=name.lower(): self._show_add_channel_modal(n)
        )
        add_btn.pack(pady=10)
    
    def _create_channel_item(self, channel_id: int, channel):
        from gui.theme import AEGISTheme
        
        type_icons = {
            'telegram': '📱',
            'discord': '🌐',
            'sms': '📞',
            'whatsapp': '💬',
            'webhook': '🔗'
        }
        
        item = ctk.CTkFrame(
            self.channels_grid,
            fg_color=AEGISTheme.get_color('secondary_bg'),
            corner_radius=8
        )
        item.pack(side='left', fill='both', expand=True, padx=4, pady=8)
        
        ctk.CTkLabel(
            item,
            text=type_icons.get(channel.channel_type, '📢'),
            font=('Inter', 24, 'normal')
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            item,
            text=channel.name,
            font=('Inter', 13, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        ).pack()
        
        stats = channel.stats
        sent = stats.get('sent', 0)
        ctk.CTkLabel(
            item,
            text=f"Sent: {sent}",
            font=('Inter', 10, 'normal'),
            text_color=AEGISTheme.get_color('text_muted')
        ).pack()
        
        btn_frame = ctk.CTkFrame(item, fg_color='transparent')
        btn_frame.pack(pady=10)
        
        edit_btn = ctk.CTkButton(
            btn_frame,
            text='Edit',
            font=('Inter', 10, 'normal'),
            fg_color='transparent',
            text_color=AEGISTheme.get_color('text_secondary'),
            hover_color=AEGISTheme.get_color('hover'),
            width=50,
            height=24,
            corner_radius=6,
            command=lambda: self._show_edit_channel_modal(channel_id, channel)
        )
        edit_btn.pack(side='left', padx=3)
        
        test_btn = ctk.CTkButton(
            btn_frame,
            text='Test',
            font=('Inter', 10, 'normal'),
            fg_color=AEGISTheme.get_color('success'),
            text_color='white',
            hover_color='#16A34A',
            width=50,
            height=24,
            corner_radius=6,
            command=lambda: self._test_channel(channel_id)
        )
        test_btn.pack(side='left', padx=3)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text='Del',
            font=('Inter', 10, 'normal'),
            fg_color=AEGISTheme.get_color('error'),
            text_color='white',
            hover_color='#DC2626',
            width=40,
            height=24,
            corner_radius=6,
            command=lambda: self._delete_channel(channel_id)
        )
        delete_btn.pack(side='left', padx=3)
    
    def _update_stats(self):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            stats = hermes.get_stats()
            
            self.stats_labels['triggers'].configure(text=str(stats.get('triggers_active', 0)))
            self.stats_labels['notifications'].configure(text=str(stats.get('notifications_sent', 0)))
            
            uptime = stats.get('uptime', 0)
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            self.stats_labels['uptime'].configure(text=f'{hours}h {minutes}m')
        except Exception:

            pass
    
    def _show_add_trigger_modal(self):
        modal = TriggerModal(self)
        modal.grab_set()
        self.wait_window(modal)
        result = modal.get_result()
        if result:
            self._save_trigger(result)
    
    def _show_edit_trigger_modal(self, trigger: dict):
        modal = TriggerModal(self, trigger=trigger)
        modal.grab_set()
        self.wait_window(modal)
        result = modal.get_result()
        if result:
            self._update_trigger(trigger['id'], result)
    
    def _save_trigger(self, data: dict):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            hermes.add_trigger(data)
            self._load_triggers()
            self._update_stats()
        except Exception as e:
            print(f"Error saving trigger: {e}")
    
    def _update_trigger(self, trigger_id: int, data: dict):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            hermes.update_trigger(trigger_id, data)
            self._load_triggers()
        except Exception as e:
            print(f"Error updating trigger: {e}")
    
    def _delete_trigger(self, trigger_id: int):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            hermes.delete_trigger(trigger_id)
            self._load_triggers()
            self._update_stats()
        except Exception as e:
            print(f"Error deleting trigger: {e}")
    
    def _toggle_trigger(self, trigger: dict):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            hermes.toggle_trigger(trigger['id'], not trigger.get('enabled', True))
            self._load_triggers()
            self._update_stats()
        except Exception as e:
            print(f"Error toggling trigger: {e}")
    
    def _show_add_channel_modal(self, channel_type: str = 'telegram'):
        modal = ChannelModal(self, channel_type=channel_type)
        modal.grab_set()
        self.wait_window(modal)
        result = modal.get_result()
        if result:
            self._save_channel(result)
    
    def _show_edit_channel_modal(self, channel_id: int, channel):
        modal = ChannelModal(self, channel_id=channel_id, channel=channel)
        modal.grab_set()
        self.wait_window(modal)
        result = modal.get_result()
        if result:
            self._update_channel(channel_id, result)
    
    def _save_channel(self, data: dict):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            hermes.add_channel(data['type'], data['config'])
            self._load_channels()
        except Exception as e:
            print(f"Error saving channel: {e}")
    
    def _update_channel(self, channel_id: int, data: dict):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            hermes.update_channel(channel_id, data)
            self._load_channels()
        except Exception as e:
            print(f"Error updating channel: {e}")
    
    def _delete_channel(self, channel_id: int):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            hermes.delete_channel(channel_id)
            self._load_channels()
        except Exception as e:
            print(f"Error deleting channel: {e}")
    
    def _test_channel(self, channel_id: int):
        threading.Thread(target=self._do_test_channel, args=(channel_id,), daemon=True).start()
    
    def _do_test_channel(self, channel_id: int):
        try:
            from core.agent.hermes import get_hermes
            hermes = get_hermes()
            success = asyncio.run(hermes.test_channel(channel_id))
            
            from gui.theme import AEGISTheme
            color = AEGISTheme.get_color('success') if success else AEGISTheme.get_color('error')
            text = 'Success!' if success else 'Failed'
            
            self.after(10, lambda: self._show_test_result(text, color))
        except Exception as e:
            self.after(10, lambda: self._show_test_result('Error', AEGISTheme.get_color('error')))
    
    def _show_test_result(self, text: str, color: str):
        from gui.theme import AEGISTheme
        popup = ctk.CTkToplevel(self)
        popup.title('Test Result')
        popup.geometry('300x150')
        popup.resizable(False, False)
        popup.configure(fg_color=AEGISTheme.get_color('primary_bg'))
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        x = (screen_w - 300) // 2
        y = (screen_h - 150) // 2
        popup.geometry(f'+{x}+{y}')
        
        ctk.CTkLabel(
            popup,
            text=text,
            font=('Inter', 20, 'bold'),
            text_color=color
        ).pack(expand=True, pady=(20, 10))
        
        ctk.CTkButton(
            popup,
            text='Close',
            command=popup.destroy,
            fg_color=AEGISTheme.get_color('secondary_bg'),
            text_color=AEGISTheme.get_color('text_primary'),
            hover_color=AEGISTheme.get_color('hover')
        ).pack(pady=(0, 20))
    
    def on_show(self):
        self._load_data()


class TriggerModal(ctk.CTkToplevel):
    def __init__(self, master, trigger: dict = None, **kwargs):
        super().__init__(master, **kwargs)
        self.trigger = trigger
        self._result = None
        self._configure_modal()
        self._create_content()
        
        if trigger:
            self._populate_fields()
    
    def _configure_modal(self):
        from gui.theme import AEGISTheme
        
        self.title('Create Trigger' if not self.trigger else 'Edit Trigger')
        self.geometry('550x500')
        self.resizable(False, False)
        self.configure(fg_color=AEGISTheme.get_color('primary_bg'))
        self.transient(self.master.winfo_toplevel())
        self.grab_set()
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - 550) // 2
        y = (screen_h - 500) // 2
        self.geometry(f'+{x}+{y}')
        
        self.bind('<Escape>', lambda e: self.destroy())
    
    def _create_content(self):
        from gui.theme import AEGISTheme
        
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(
            content,
            text='Trigger Name',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        ).pack(anchor='w', pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(
            content,
            placeholder_text='e.g., Factory Safety Alert',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=40,
            corner_radius=8
        )
        self.name_entry.pack(fill='x', pady=(0, 12))
        
        ctk.CTkLabel(
            content,
            text='Condition (Natural Language)',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        ).pack(anchor='w', pady=(0, 5))
        
        self.condition_text = ctk.CTkTextbox(
            content,
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=80,
            corner_radius=8
        )
        self.condition_text.insert('0.0', 'Alert me when a person is detected without a hard hat')
        self.condition_text.pack(fill='x', pady=(0, 12))
        
        ctk.CTkLabel(
            content,
            text='Capture Options',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        ).pack(anchor='w', pady=(0, 8))
        
        opt_frame = ctk.CTkFrame(content, fg_color='transparent')
        opt_frame.pack(fill='x', pady=(0, 15))
        
        self.capture_snapshot = ctk.CTkCheckBox(
            opt_frame,
            text='Save snapshot on trigger',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover')
        )
        self.capture_snapshot.select()
        self.capture_snapshot.pack(side='left', padx=(0, 20))
        
        self.capture_clip = ctk.CTkCheckBox(
            opt_frame,
            text='Record video clip',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover')
        )
        self.capture_clip.pack(side='left')
        
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        ctk.CTkButton(
            btn_frame,
            text='Cancel',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            text_color=AEGISTheme.get_color('text_primary'),
            hover_color=AEGISTheme.get_color('hover'),
            width=100,
            height=40,
            corner_radius=8,
            command=self.destroy
        ).pack(side='left')
        
        ctk.CTkButton(
            btn_frame,
            text='Create Trigger',
            font=('Inter', 13, 'bold'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            text_color='white',
            width=130,
            height=40,
            corner_radius=8,
            command=self._save
        ).pack(side='right')
    
    def _populate_fields(self):
        if self.trigger:
            self.name_entry.insert(0, self.trigger.get('name', ''))
            self.condition_text.delete('0.0', 'end')
            self.condition_text.insert('0.0', self.trigger.get('condition_text', ''))
            if not self.trigger.get('capture_snapshot', True):
                self.capture_snapshot.deselect()
            if self.trigger.get('capture_clip'):
                self.capture_clip.select()
    
    def _save(self):
        name = self.name_entry.get().strip()
        condition = self.condition_text.get('0.0', 'end').strip()
        
        if not name or not condition:
            return
        
        self._result = {
            'name': name,
            'condition_text': condition,
            'capture_snapshot': self.capture_snapshot.get() == 1,
            'capture_clip': self.capture_clip.get() == 1,
            'notification_ids': []
        }
        self.destroy()
    
    def get_result(self):
        return self._result


class ChannelModal(ctk.CTkToplevel):
    def __init__(self, master, channel_type: str = 'telegram', channel_id: int = None, channel = None, **kwargs):
        super().__init__(master, **kwargs)
        self.channel_type = channel_type
        self.channel_id = channel_id
        self.channel = channel
        self._result = None
        self._configure_modal()
        self._create_content()
    
    def _configure_modal(self):
        from gui.theme import AEGISTheme
        
        self.title(f'Add {self.channel_type.title()} Channel')
        self.geometry('450x380')
        self.resizable(False, False)
        self.configure(fg_color=AEGISTheme.get_color('primary_bg'))
        self.transient(self.master.winfo_toplevel())
        self.grab_set()
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - 450) // 2
        y = (screen_h - 380) // 2
        self.geometry(f'+{x}+{y}')
        
        self.bind('<Escape>', lambda e: self.destroy())
    
    def _create_content(self):
        from gui.theme import AEGISTheme
        
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(
            content,
            text='Channel Name',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        ).pack(anchor='w', pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(
            content,
            placeholder_text='e.g., Factory Alerts',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=38,
            corner_radius=8
        )
        self.name_entry.pack(fill='x', pady=(0, 12))
        
        self._create_channel_config(content)
        
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(15, 0))
        
        ctk.CTkButton(
            btn_frame,
            text='Cancel',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            text_color=AEGISTheme.get_color('text_primary'),
            hover_color=AEGISTheme.get_color('hover'),
            width=100,
            height=38,
            corner_radius=8,
            command=self.destroy
        ).pack(side='left')
        
        ctk.CTkButton(
            btn_frame,
            text='Save Channel',
            font=('Inter', 13, 'bold'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            text_color='white',
            width=120,
            height=38,
            corner_radius=8,
            command=self._save
        ).pack(side='right')
    
    def _create_channel_config(self, parent):
        from gui.theme import AEGISTheme
        
        if self.channel_type == 'telegram':
            ctk.CTkLabel(
                parent,
                text='Bot Token',
                font=('Inter', 12, 'bold'),
                text_color=AEGISTheme.get_color('text_secondary')
            ).pack(anchor='w', pady=(0, 5))
            
            self.bot_token = ctk.CTkEntry(
                parent,
                placeholder_text='123456:ABC-DEF...',
                font=('Inter', 12, 'normal'),
                fg_color=AEGISTheme.get_color('secondary_bg'),
                border_color=AEGISTheme.get_color('border'),
                text_color=AEGISTheme.get_color('text_primary'),
                height=38,
                corner_radius=8
            )
            self.bot_token.pack(fill='x', pady=(0, 12))
            
            ctk.CTkLabel(
                parent,
                text='Chat ID',
                font=('Inter', 12, 'bold'),
                text_color=AEGISTheme.get_color('text_secondary')
            ).pack(anchor='w', pady=(0, 5))
            
            self.chat_id = ctk.CTkEntry(
                parent,
                placeholder_text='@your_chat_id or 123456789',
                font=('Inter', 12, 'normal'),
                fg_color=AEGISTheme.get_color('secondary_bg'),
                border_color=AEGISTheme.get_color('border'),
                text_color=AEGISTheme.get_color('text_primary'),
                height=38,
                corner_radius=8
            )
            self.chat_id.pack(fill='x')
        
        elif self.channel_type == 'discord':
            ctk.CTkLabel(
                parent,
                text='Webhook URL',
                font=('Inter', 12, 'bold'),
                text_color=AEGISTheme.get_color('text_secondary')
            ).pack(anchor='w', pady=(0, 5))
            
            self.webhook_url = ctk.CTkEntry(
                parent,
                placeholder_text='https://discord.com/api/webhooks/...',
                font=('Inter', 12, 'normal'),
                fg_color=AEGISTheme.get_color('secondary_bg'),
                border_color=AEGISTheme.get_color('border'),
                text_color=AEGISTheme.get_color('text_primary'),
                height=38,
                corner_radius=8
            )
            self.webhook_url.pack(fill='x')
        
        elif self.channel_type in ('sms', 'whatsapp'):
            for label, key in [('Account SID', 'account_sid'), ('Auth Token', 'auth_token'), ('From Number', 'from'), ('To Number', 'to')]:
                ctk.CTkLabel(
                    parent,
                    text=label,
                    font=('Inter', 12, 'bold'),
                    text_color=AEGISTheme.get_color('text_secondary')
                ).pack(anchor='w', pady=(0, 5))
                
                entry = ctk.CTkEntry(
                    parent,
                    font=('Inter', 12, 'normal'),
                    fg_color=AEGISTheme.get_color('secondary_bg'),
                    border_color=AEGISTheme.get_color('border'),
                    text_color=AEGISTheme.get_color('text_primary'),
                    height=38,
                    corner_radius=8
                )
                entry.pack(fill='x', pady=(0, 8))
                setattr(self, key, entry)
        
        elif self.channel_type == 'webhook':
            ctk.CTkLabel(
                parent,
                text='Webhook URL',
                font=('Inter', 12, 'bold'),
                text_color=AEGISTheme.get_color('text_secondary')
            ).pack(anchor='w', pady=(0, 5))
            
            self.webhook_url = ctk.CTkEntry(
                parent,
                placeholder_text='https://api.example.com/alert',
                font=('Inter', 12, 'normal'),
                fg_color=AEGISTheme.get_color('secondary_bg'),
                border_color=AEGISTheme.get_color('border'),
                text_color=AEGISTheme.get_color('text_primary'),
                height=38,
                corner_radius=8
            )
            self.webhook_url.pack(fill='x', pady=(0, 12))
            
            ctk.CTkLabel(
                parent,
                text='Method',
                font=('Inter', 12, 'bold'),
                text_color=AEGISTheme.get_color('text_secondary')
            ).pack(anchor='w', pady=(0, 5))
            
            self.method = ctk.CTkOptionMenu(
                parent,
                values=['POST', 'GET', 'PUT'],
                font=('Inter', 12, 'normal'),
                fg_color=AEGISTheme.get_color('secondary_bg'),
                button_color=AEGISTheme.get_color('card_bg'),
                text_color=AEGISTheme.get_color('text_primary'),
                dropdown_fg_color=AEGISTheme.get_color('secondary_bg'),
                height=38,
                corner_radius=8
            )
            self.method.set('POST')
            self.method.pack(fill='x')
    
    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            return
        
        config = {'name': name, 'type': self.channel_type, 'enabled': True}
        
        if self.channel_type == 'telegram':
            config.update({'bot_token': self.bot_token.get().strip(), 'chat_id': self.chat_id.get().strip()})
        elif self.channel_type == 'discord':
            config.update({'webhook_url': self.webhook_url.get().strip()})
        elif self.channel_type in ('sms', 'whatsapp'):
            for key in ['account_sid', 'auth_token', 'from', 'to']:
                entry = getattr(self, key, None)
                if entry:
                    config[key] = entry.get().strip()
        elif self.channel_type == 'webhook':
            config.update({'url': self.webhook_url.get().strip(), 'method': self.method.get()})
        
        self._result = {'type': self.channel_type, 'config': config}
        self.destroy()
    
    def get_result(self):
        return self._result
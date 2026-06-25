import customtkinter as ctk
from typing import Optional, Callable
import json


class CamerasPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._setup_style()
        self._create_widgets()
        self._on_camera_select = None
        self._load_cameras()
    
    def _setup_style(self):
        from gui.theme import AEGISTheme
        self.configure(fg_color=AEGISTheme.get_color('primary_bg'))
    
    def _create_widgets(self):
        from gui.theme import AEGISTheme
        
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=20, pady=(15, 10))
        
        title = ctk.CTkLabel(
            header,
            text='Camera Management',
            font=('Inter', 22, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        title.pack(side='left')
        
        add_btn = ctk.CTkButton(
            header,
            text='+ Add Camera',
            font=('Inter', 13, 'bold'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            corner_radius=8,
            command=self._show_add_camera_modal
        )
        add_btn.pack(side='right')
        
        add_integrated_btn = ctk.CTkButton(
            header,
            text='+ Add Integrated Webcam',
            font=('Inter', 13, 'bold'),
            fg_color=AEGISTheme.get_color('secondary_accent'),
            hover_color='#5558E3',
            corner_radius=8,
            command=self._add_integrated_camera
        )
        add_integrated_btn.pack(side='right', padx=(0, 10))
        
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent',
            scrollbar_button_color=AEGISTheme.get_color('card_bg'),
            scrollbar_button_hover_color=AEGISTheme.get_color('hover')
        )
        self.scroll_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        self.camera_list = ctk.CTkFrame(self.scroll_frame, fg_color='transparent')
        self.camera_list.pack(fill='both', expand=True)
        
        self.empty_label = ctk.CTkLabel(
            self.camera_list,
            text='📷 No cameras configured\n\nClick "+ Add Camera" to add your first camera',
            font=('Inter', 14, 'normal'),
            text_color=AEGISTheme.get_color('text_muted')
        )
        self.empty_label.pack(pady=50)
    
    def _load_cameras(self):
        try:
            from core.storage.database import get_db, Camera
            db = get_db()
            session = db.get_session()
            cameras = session.query(Camera).all()
            session.close()
            
            if cameras:
                self.empty_label.pack_forget()
                for cam in cameras:
                    self._add_camera_item(cam)
        except Exception as e:
            print(f"Error loading cameras: {e}")
    
    def _add_camera_item(self, camera):
        from gui.theme import AEGISTheme
        
        item = ctk.CTkFrame(
            self.camera_list,
            fg_color=AEGISTheme.get_color('card_bg'),
            corner_radius=12
        )
        item.pack(fill='x', pady=5, ipady=10)
        
        header = ctk.CTkFrame(item, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(10, 5))
        
        icon_label = ctk.CTkLabel(
            header,
            text='📷',
            font=('Inter', 20, 'normal')
        )
        icon_label.pack(side='left')
        
        name_label = ctk.CTkLabel(
            header,
            text=camera.name,
            font=('Inter', 16, 'bold'),
            text_color=AEGISTheme.get_color('text_primary')
        )
        name_label.pack(side='left', padx=10)
        
        type_label = ctk.CTkLabel(
            header,
            text=camera.source_type.upper(),
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('accent')
        )
        type_label.pack(side='left', padx=5)
        
        status_label = ctk.CTkLabel(
            header,
            text='●',
            font=('Inter', 14, 'bold'),
            text_color=AEGISTheme.get_color('success')
        )
        status_label.pack(side='right')
        
        details = ctk.CTkFrame(item, fg_color='transparent')
        details.pack(fill='x', padx=15, pady=5)
        
        url_label = ctk.CTkLabel(
            details,
            text=f"URL: {camera.source_url[:50]}{'...' if len(camera.source_url) > 50 else ''}",
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        url_label.pack(anchor='w')
        
        btn_frame = ctk.CTkFrame(item, fg_color='transparent')
        btn_frame.pack(fill='x', padx=15, pady=(10, 5))
        
        edit_btn = ctk.CTkButton(
            btn_frame,
            text='Edit',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            text_color=AEGISTheme.get_color('text_primary'),
            hover_color=AEGISTheme.get_color('hover'),
            width=80,
            height=32,
            corner_radius=6,
            command=lambda: self._show_edit_camera_modal(camera)
        )
        edit_btn.pack(side='left', padx=(0, 10))
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text='Delete',
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('error'),
            text_color='white',
            hover_color='#DC2626',
            width=80,
            height=32,
            corner_radius=6,
            command=lambda: self._delete_camera(camera.id)
        )
        delete_btn.pack(side='left')
        
        toggle_text = 'Disable' if camera.enabled else 'Enable'
        toggle_btn = ctk.CTkButton(
            btn_frame,
            text=toggle_text,
            font=('Inter', 12, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_accent'),
            text_color='white',
            hover_color='#5558E3',
            width=80,
            height=32,
            corner_radius=6,
            command=lambda: self._toggle_camera(camera)
        )
        toggle_btn.pack(side='right')
    
    def _show_add_camera_modal(self):
        modal = CameraModal(self, title='Add Camera')
        modal.grab_set()
        self.wait_window(modal)
        
        result = modal.get_result()
        if result:
            self._save_camera(result)
            
    def _add_integrated_camera(self):
        self._save_camera({
            'name': 'Integrated Webcam',
            'source_type': 'usb',
            'source_url': '0',
            'fps': 10
        })
    
    def _show_edit_camera_modal(self, camera):
        modal = CameraModal(self, title='Edit Camera', camera=camera)
        modal.grab_set()
        self.wait_window(modal)
        
        result = modal.get_result()
        if result:
            self._update_camera(camera.id, result)
    
    def _save_camera(self, data: dict):
        try:
            from core.storage.database import get_db, Camera
            db = get_db()
            session = db.get_session()
            
            camera = Camera(
                name=data['name'],
                source_type=data['source_type'],
                source_url=data['source_url'],
                fps=data.get('fps', 10),
                enabled=True
            )
            session.add(camera)
            session.commit()
            camera_id = camera.id
            session.close()
            
            self._refresh_list()
            
            from core.camera.capture import get_camera_manager
            cam_mgr = get_camera_manager()
            cam_mgr.add_camera(camera_id, data['name'], data['source_type'], data['source_url'], data.get('fps', 10))
            
        except Exception as e:
            print(f"Error saving camera: {e}")
    
    def _update_camera(self, camera_id: int, data: dict):
        try:
            from core.storage.database import get_db, Camera
            db = get_db()
            session = db.get_session()
            
            camera = session.query(Camera).filter_by(id=camera_id).first()
            if camera:
                camera.name = data['name']
                camera.source_type = data['source_type']
                camera.source_url = data['source_url']
                camera.fps = data.get('fps', 10)
                session.commit()
            
            session.close()
            self._refresh_list()
            
        except Exception as e:
            print(f"Error updating camera: {e}")
    
    def _delete_camera(self, camera_id: int):
        try:
            from core.storage.database import get_db, Camera
            db = get_db()
            session = db.get_session()
            
            camera = session.query(Camera).filter_by(id=camera_id).first()
            if camera:
                session.delete(camera)
                session.commit()
            
            session.close()
            self._refresh_list()
            
            from core.camera.capture import get_camera_manager
            cam_mgr = get_camera_manager()
            cam_mgr.remove_camera(camera_id)
            
        except Exception as e:
            print(f"Error deleting camera: {e}")
    
    def _toggle_camera(self, camera):
        try:
            from core.storage.database import get_db, Camera
            db = get_db()
            session = db.get_session()
            
            cam = session.query(Camera).filter_by(id=camera.id).first()
            if cam:
                cam.enabled = not cam.enabled
                session.commit()
                
                from core.camera.capture import get_camera_manager
                cam_mgr = get_camera_manager()
                if cam.enabled:
                    cam_mgr.start_source(camera.id)
                else:
                    cam_mgr.stop_source(camera.id)
            
            session.close()
            self._refresh_list()
            
        except Exception as e:
            print(f"Error toggling camera: {e}")
    
    def _refresh_list(self):
        for widget in self.camera_list.winfo_children():
            widget.destroy()
        
        self._load_cameras()


class CameraModal(ctk.CTkToplevel):
    def __init__(self, master, title: str = 'Camera', camera=None, **kwargs):
        super().__init__(master, **kwargs)
        self.camera = camera
        self._result = None
        self._configure_modal(title)
        self._create_content()
        
        if camera:
            self._populate_fields()
    
    def _configure_modal(self, title: str):
        from gui.theme import AEGISTheme
        
        self.title(title)
        self.geometry('500x480')
        self.resizable(False, False)
        self.configure(fg_color=AEGISTheme.get_color('primary_bg'))
        self.transient(self.master.winfo_toplevel())
        self.grab_set()
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - 500) // 2
        y = (screen_h - 480) // 2
        self.geometry(f'+{x}+{y}')
        
        self.bind('<Escape>', lambda e: self.destroy())
    
    def _create_content(self):
        from gui.theme import AEGISTheme
        
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=25, pady=20)
        
        name_label = ctk.CTkLabel(
            content,
            text='Camera Name',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        name_label.pack(anchor='w', pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(
            content,
            placeholder_text='e.g., Factory Floor Camera',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=40,
            corner_radius=8
        )
        self.name_entry.pack(fill='x', pady=(0, 15))
        
        type_label = ctk.CTkLabel(
            content,
            text='Source Type',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        type_label.pack(anchor='w', pady=(0, 5))
        
        type_frame = ctk.CTkFrame(content, fg_color='transparent')
        type_frame.pack(fill='x', pady=(0, 15))
        
        self.source_type = ctk.StringVar(value='rtsp')
        
        for val, txt in [('rtsp', 'RTSP'), ('usb', 'USB'), ('file', 'Video File')]:
            btn = ctk.CTkRadioButton(
                type_frame,
                text=txt,
                variable=self.source_type,
                value=val,
                font=('Inter', 12, 'normal'),
                fg_color=AEGISTheme.get_color('accent'),
                hover_color=AEGISTheme.get_color('accent_hover')
            )
            btn.pack(side='left', padx=(0, 20))
        
        url_label = ctk.CTkLabel(
            content,
            text='Source URL / Device',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        url_label.pack(anchor='w', pady=(0, 5))
        
        self.url_entry = ctk.CTkEntry(
            content,
            placeholder_text='rtsp://192.168.1.100:554/stream',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            border_color=AEGISTheme.get_color('border'),
            text_color=AEGISTheme.get_color('text_primary'),
            height=40,
            corner_radius=8
        )
        self.url_entry.pack(fill='x', pady=(0, 15))
        
        fps_label = ctk.CTkLabel(
            content,
            text='FPS',
            font=('Inter', 12, 'bold'),
            text_color=AEGISTheme.get_color('text_secondary')
        )
        fps_label.pack(anchor='w', pady=(0, 5))
        
        self.fps_slider = ctk.CTkSlider(
            content,
            from_=1,
            to=30,
            number_of_steps=29,
            fg_color=AEGISTheme.get_color('secondary_bg'),
            progress_color=AEGISTheme.get_color('accent'),
            button_color=AEGISTheme.get_color('accent'),
            button_hover_color=AEGISTheme.get_color('accent_hover')
        )
        self.fps_slider.set(10)
        self.fps_slider.pack(fill='x', pady=(0, 5))
        
        self.fps_value = ctk.CTkLabel(
            content,
            text='10 FPS',
            font=('Inter', 11, 'normal'),
            text_color=AEGISTheme.get_color('text_muted')
        )
        self.fps_value.pack(anchor='w', pady=(0, 20))
        
        self.fps_slider.bind('<Motion>', lambda e: self.fps_value.configure(text=f'{int(self.fps_slider.get())} FPS'))
        
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text='Cancel',
            font=('Inter', 13, 'normal'),
            fg_color=AEGISTheme.get_color('secondary_bg'),
            text_color=AEGISTheme.get_color('text_primary'),
            hover_color=AEGISTheme.get_color('hover'),
            width=120,
            height=40,
            corner_radius=8,
            command=self.destroy
        )
        cancel_btn.pack(side='left')
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text='Save Camera',
            font=('Inter', 13, 'bold'),
            fg_color=AEGISTheme.get_color('accent'),
            hover_color=AEGISTheme.get_color('accent_hover'),
            text_color='white',
            width=140,
            height=40,
            corner_radius=8,
            command=self._save
        )
        save_btn.pack(side='right')
    
    def _populate_fields(self):
        if self.camera:
            self.name_entry.insert(0, self.camera.name)
            self.source_type.set(self.camera.source_type)
            self.url_entry.insert(0, self.camera.source_url)
            self.fps_slider.set(self.camera.fps)
            self.fps_value.configure(text=f'{self.camera.fps} FPS')
    
    def _save(self):
        name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()
        source_type = self.source_type.get()
        fps = int(self.fps_slider.get())
        
        if not name or not url:
            return
        
        self._result = {
            'name': name,
            'source_type': source_type,
            'source_url': url,
            'fps': fps
        }
        self.destroy()
    
    def get_result(self):
        return self._result
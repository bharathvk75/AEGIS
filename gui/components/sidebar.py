"""
AEGIS Premium Sidebar & TitleBar
Hand-crafted navigation with animated active indicator,
hover color transitions, and proper visual hierarchy.
"""
import customtkinter as ctk
from typing import Callable, Optional


class Sidebar(ctk.CTkFrame):
    
    NAV_ITEMS = [
        ('dashboard', 'Dashboard',    '⬡'),
        ('cameras',   'Cameras',      '◎'),
        ('models',    'AI Models',    '◇'),
        ('hermes',    'Hermes Agent', '△'),
        ('storage',   'Storage',      '▤'),
    ]
    
    def __init__(self, master, width: int = 240, **kwargs):
        from gui.theme import AEGISTheme as T
        super().__init__(master, width=width, corner_radius=0,
                         fg_color=T.get_color('bg_raised'), **kwargs)
        self.pack_propagate(False)
        self._callback = None
        self._active_page = None
        self._nav_buttons = {}
        self._nav_indicators = {}
        
        self._build_header()
        self._build_nav()
        self._build_footer()
    
    # ── Header ────────────────────────────────────────────────────────────────
    
    def _build_header(self):
        from gui.theme import AEGISTheme as T
        
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=24, pady=(28, 0))
        
        # Brand mark — accent square + wordmark
        brand = ctk.CTkFrame(header, fg_color='transparent')
        brand.pack(anchor='w')
        
        mark = ctk.CTkFrame(brand, width=6, height=28, fg_color=T.get_color('accent'),
                            corner_radius=3)
        mark.pack(side='left', padx=(0, 12))
        mark.pack_propagate(False)
        
        wordmark_container = ctk.CTkFrame(brand, fg_color='transparent')
        wordmark_container.pack(side='left')
        
        ctk.CTkLabel(
            wordmark_container, text='AEGIS',
            font=('Inter', 22, 'bold'),
            text_color=T.get_color('text_primary')
        ).pack(anchor='w')
        
        ctk.CTkLabel(
            wordmark_container, text='Edge Intelligence System',
            font=T.get_font('caption_sm'),
            text_color=T.get_color('text_tertiary')
        ).pack(anchor='w', pady=(0, 0))
        
        # Divider
        ctk.CTkFrame(
            self, height=1,
            fg_color=T.get_color('border_subtle')
        ).pack(fill='x', padx=20, pady=(20, 16))
    
    # ── Navigation ────────────────────────────────────────────────────────────
    
    def _build_nav(self):
        from gui.theme import AEGISTheme as T
        
        nav_container = ctk.CTkFrame(self, fg_color='transparent')
        nav_container.pack(fill='both', expand=True, padx=14)
        
        # Overline label
        ctk.CTkLabel(
            nav_container, text='MAIN MENU',
            font=T.get_font('overline'),
            text_color=T.get_color('text_disabled')
        ).pack(anchor='w', padx=10, pady=(0, 8))
        
        for item_id, label, icon in self.NAV_ITEMS:
            row = ctk.CTkFrame(nav_container, fg_color='transparent', height=T.get_height('nav_item'))
            row.pack(fill='x', pady=1)
            row.pack_propagate(False)
            
            # Left accent indicator (hidden by default)
            indicator = ctk.CTkFrame(
                row, width=3, fg_color='transparent',
                corner_radius=2
            )
            indicator.pack(side='left', fill='y', padx=(0, 0), pady=8)
            self._nav_indicators[item_id] = indicator
            
            # Button
            btn = ctk.CTkButton(
                row,
                text=f'  {icon}   {label}',
                anchor='w',
                font=T.get_font('nav'),
                fg_color='transparent',
                text_color=T.get_color('text_secondary'),
                hover_color=T.get_color('hover'),
                height=T.get_height('nav_item'),
                corner_radius=T.get_radius('md'),
                command=lambda pid=item_id: self._on_nav_click(pid)
            )
            btn.pack(side='left', fill='both', expand=True, padx=(4, 0))
            self._nav_buttons[item_id] = btn
            
            # Hover animation
            self._setup_button_hover(btn, item_id)
    
    def _setup_button_hover(self, btn, item_id):
        from gui.theme import AEGISTheme as T
        from gui.animations import Animator, ease_out_cubic
        
        def on_enter(e):
            if item_id != self._active_page:
                Animator.animate_color(btn, 'fg_color',
                    T.get_color('bg_raised'), T.get_color('hover'),
                    duration=150, easing=ease_out_cubic)
        
        def on_leave(e):
            if item_id != self._active_page:
                Animator.animate_color(btn, 'fg_color',
                    T.get_color('hover'), 'transparent',
                    duration=200, easing=ease_out_cubic)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
    
    # ── Footer ────────────────────────────────────────────────────────────────
    
    def _build_footer(self):
        from gui.theme import AEGISTheme as T
        
        # Divider
        ctk.CTkFrame(
            self, height=1,
            fg_color=T.get_color('border_subtle')
        ).pack(fill='x', padx=20, pady=(0, 12))
        
        footer = ctk.CTkFrame(self, fg_color='transparent')
        footer.pack(fill='x', padx=24, pady=(0, 20))
        
        # Status row
        status_row = ctk.CTkFrame(footer, fg_color='transparent')
        status_row.pack(fill='x')
        
        self._status_dot = ctk.CTkLabel(
            status_row, text='●',
            font=('Inter', 8, 'normal'),
            text_color=T.get_color('warning')
        )
        self._status_dot.pack(side='left', padx=(0, 6))
        
        self._status_text = ctk.CTkLabel(
            status_row, text='Initializing...',
            font=T.get_font('caption_sm'),
            text_color=T.get_color('text_tertiary')
        )
        self._status_text.pack(side='left')
        
        # Storage row
        self._storage_label = ctk.CTkLabel(
            footer, text='Storage: —',
            font=T.get_font('caption_sm'),
            text_color=T.get_color('text_disabled')
        )
        self._storage_label.pack(anchor='w', pady=(6, 0))
    
    # ── Public API ────────────────────────────────────────────────────────────
    
    def set_callback(self, callback: Callable):
        self._callback = callback
    
    def _on_nav_click(self, page_id: str):
        if self._callback:
            self._callback(page_id)
    
    def set_active_page(self, page_id: str):
        from gui.theme import AEGISTheme as T
        from gui.animations import Animator, ease_out_cubic
        
        prev = self._active_page
        self._active_page = page_id
        
        for nav_id, btn in self._nav_buttons.items():
            indicator = self._nav_indicators[nav_id]
            
            if nav_id == page_id:
                # Active state
                btn.configure(
                    font=T.get_font('nav_active'),
                    text_color=T.get_color('accent_glow'),
                    fg_color=T.get_color('accent_surface')
                )
                indicator.configure(fg_color=T.get_color('accent'))
            else:
                # Inactive state
                btn.configure(
                    font=T.get_font('nav'),
                    text_color=T.get_color('text_secondary'),
                    fg_color='transparent'
                )
                indicator.configure(fg_color='transparent')
    
    def update_status(self, text: str, color: str = None):
        from gui.theme import AEGISTheme as T
        if color is None:
            color = T.get_color('success')
        
        self._status_dot.configure(text_color=color)
        # Extract text without the dot prefix if present
        clean = text.lstrip('● ').strip()
        self._status_text.configure(text=clean)
        
        # Pulse the status dot
        from gui.animations import pulse_dot
        if 'Ready' in clean or 'OK' in clean:
            pulse_dot(self._status_dot, color, T.get_color('text_disabled'), duration=2000)
    
    def update_storage(self, used_gb: float, total_gb: float, percentage: float):
        self._storage_label.configure(
            text=f'Storage: {used_gb:.1f} / {total_gb:.0f} GB'
        )


# ══════════════════════════════════════════════════════════════════════════════
# Title Bar
# ══════════════════════════════════════════════════════════════════════════════

class TitleBar(ctk.CTkFrame):
    
    def __init__(self, master, **kwargs):
        from gui.theme import AEGISTheme as T
        super().__init__(master, height=T.get_height('title_bar'),
                         corner_radius=0,
                         fg_color=T.get_color('bg_raised'), **kwargs)
        self.pack_propagate(False)
        self._minimize_cb = None
        self._maximize_cb = None
        self._close_cb = None
        self._build()
    
    def _build(self):
        from gui.theme import AEGISTheme as T
        
        # Left — subtle breadcrumb
        left = ctk.CTkFrame(self, fg_color='transparent')
        left.pack(side='left', padx=16)
        
        ctk.CTkLabel(
            left, text='●',
            font=('Inter', 7, 'normal'),
            text_color=T.get_color('accent')
        ).pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(
            left, text='AEGIS',
            font=T.get_font('caption'),
            text_color=T.get_color('text_tertiary')
        ).pack(side='left')
        
        ctk.CTkLabel(
            left, text='·',
            font=T.get_font('caption'),
            text_color=T.get_color('text_disabled')
        ).pack(side='left', padx=6)
        
        ctk.CTkLabel(
            left, text='Edge Video Analytics',
            font=T.get_font('caption'),
            text_color=T.get_color('text_disabled')
        ).pack(side='left')
        
        # Right — window controls
        controls = ctk.CTkFrame(self, fg_color='transparent')
        controls.pack(side='right', padx=8)
        
        for icon, cb_name, hover_color in [
            ('─', '_minimize_cb', T.get_color('hover')),
            ('□', '_maximize_cb', T.get_color('hover')),
            ('×', '_close_cb',    T.get_color('error')),
        ]:
            btn = ctk.CTkButton(
                controls,
                text=icon,
                width=34, height=26,
                fg_color='transparent',
                text_color=T.get_color('text_tertiary'),
                hover_color=hover_color,
                corner_radius=T.get_radius('sm'),
                font=('Inter', 14, 'normal'),
                command=lambda n=cb_name: self._fire(n)
            )
            btn.pack(side='left', padx=1)
            
            # Animate hover for close button
            if icon == '×':
                self._setup_close_hover(btn, hover_color)
    
    def _setup_close_hover(self, btn, hover_color):
        from gui.theme import AEGISTheme as T
        
        def on_enter(e):
            btn.configure(text_color='#FFFFFF')
        def on_leave(e):
            btn.configure(text_color=T.get_color('text_tertiary'))
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
    
    def _fire(self, cb_name):
        cb = getattr(self, cb_name, None)
        if cb:
            cb()
    
    def set_callbacks(self, minimize=None, maximize=None, close=None):
        self._minimize_cb = minimize
        self._maximize_cb = maximize
        self._close_cb = close
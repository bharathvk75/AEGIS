"""
AEGIS Animation Engine
Smooth easing functions and animation primitives for CustomTkinter.
Provides fade, slide, scale, and color-lerp transitions using widget.after().
"""
import math
from typing import Callable, Optional, Any


# ── Easing Functions ──────────────────────────────────────────────────────────

def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_out_quart(t: float) -> float:
    return 1 - pow(1 - t, 4)

def ease_in_out_cubic(t: float) -> float:
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def ease_out_expo(t: float) -> float:
    return 1 if t == 1 else 1 - pow(2, -10 * t)

def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_out_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    c4 = (2 * math.pi) / 3
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def linear(t: float) -> float:
    return t


# ── Color Utilities ───────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f'#{r:02x}{g:02x}{b:02x}'

def lerp_color(color_a: str, color_b: str, t: float) -> str:
    r1, g1, b1 = hex_to_rgb(color_a)
    r2, g2, b2 = hex_to_rgb(color_b)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return rgb_to_hex(
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b))
    )


# ── Core Animation Controller ────────────────────────────────────────────────

class Animator:
    """
    Runs tween animations on any widget property using after() scheduling.
    
    Usage:
        Animator.animate(widget, 'fg_color', '#1a1a2e', '#6C63FF', 
                        duration=300, easing=ease_out_cubic)
    """
    _active_animations: dict = {}
    
    @classmethod
    def cancel(cls, widget, prop: str):
        key = (id(widget), prop)
        if key in cls._active_animations:
            widget.after_cancel(cls._active_animations[key])
            del cls._active_animations[key]
    
    @classmethod
    def animate_value(
        cls,
        widget,
        from_val: float,
        to_val: float,
        duration: int = 300,
        easing: Callable = ease_out_cubic,
        on_update: Callable = None,
        on_complete: Callable = None,
        prop_name: str = '_anim'
    ):
        key = (id(widget), prop_name)
        cls.cancel(widget, prop_name)
        
        fps = 60
        interval = max(1, 1000 // fps)
        total_frames = max(1, duration // interval)
        frame = [0]
        
        def step():
            if not widget.winfo_exists():
                return
            
            frame[0] += 1
            t = min(1.0, frame[0] / total_frames)
            eased = easing(t)
            current = from_val + (to_val - from_val) * eased
            
            if on_update:
                on_update(current)
            
            if t < 1.0:
                cls._active_animations[key] = widget.after(interval, step)
            else:
                if key in cls._active_animations:
                    del cls._active_animations[key]
                if on_complete:
                    on_complete()
        
        cls._active_animations[key] = widget.after(interval, step)
    
    @classmethod
    def animate_color(
        cls,
        widget,
        prop: str,
        from_color: str,
        to_color: str,
        duration: int = 250,
        easing: Callable = ease_out_cubic,
        on_complete: Callable = None
    ):
        def update(t_val):
            try:
                color = lerp_color(from_color, to_color, t_val)
                widget.configure(**{prop: color})
            except Exception:
                pass
        
        cls.animate_value(
            widget, 0.0, 1.0,
            duration=duration,
            easing=easing,
            on_update=update,
            on_complete=on_complete,
            prop_name=f'color_{prop}'
        )
    
    @classmethod
    def fade_in(cls, widget, duration: int = 400, easing: Callable = ease_out_cubic):
        """Simulate fade-in by animating fg_color from bg to target."""
        pass  # CTK doesn't support opacity; we use slide_in instead
    
    @classmethod
    def slide_in_y(
        cls,
        widget,
        start_offset: int = 20,
        duration: int = 350,
        easing: Callable = ease_out_cubic,
        delay: int = 0,
        on_complete: Callable = None
    ):
        """Slide a widget in from below by adjusting pady."""
        def do_slide():
            def update(val):
                try:
                    offset = int(val)
                    widget.configure(pady=(offset, 0))
                except Exception:
                    pass
            
            cls.animate_value(
                widget, start_offset, 0,
                duration=duration,
                easing=easing,
                on_update=update,
                on_complete=on_complete,
                prop_name='slide_y'
            )
        
        if delay > 0:
            widget.after(delay, do_slide)
        else:
            do_slide()


# ── Hover Animation Mixin ─────────────────────────────────────────────────────

class HoverMixin:
    """
    Mixin to add smooth hover color transitions to any CTk widget.
    
    Usage in __init__:
        HoverMixin.setup_hover(self, 
            normal_color='#1E2235', 
            hover_color='#252A3E',
            prop='fg_color')
    """
    
    @staticmethod
    def setup_hover(
        widget,
        normal_color: str,
        hover_color: str,
        prop: str = 'fg_color',
        duration: int = 180
    ):
        widget._hover_normal = normal_color
        widget._hover_target = hover_color
        widget._hover_prop = prop
        widget._hover_duration = duration
        widget._is_hovered = False
        
        widget.bind('<Enter>', lambda e: HoverMixin._on_enter(widget))
        widget.bind('<Leave>', lambda e: HoverMixin._on_leave(widget))
    
    @staticmethod
    def _on_enter(widget):
        widget._is_hovered = True
        Animator.animate_color(
            widget, widget._hover_prop,
            widget._hover_normal, widget._hover_target,
            duration=widget._hover_duration
        )
    
    @staticmethod
    def _on_leave(widget):
        widget._is_hovered = False
        Animator.animate_color(
            widget, widget._hover_prop,
            widget._hover_target, widget._hover_normal,
            duration=widget._hover_duration
        )


# ── Staggered Entrance ────────────────────────────────────────────────────────

def stagger_entrance(widgets: list, base_delay: int = 40, duration: int = 300):
    """Animate a list of widgets in sequence with staggered delays."""
    for i, widget in enumerate(widgets):
        Animator.slide_in_y(
            widget,
            start_offset=25,
            duration=duration,
            delay=i * base_delay,
            easing=ease_out_cubic
        )


# ── Pulse Animation ───────────────────────────────────────────────────────────

def pulse_dot(widget, color_a: str, color_b: str, prop: str = 'text_color', duration: int = 1200):
    """Creates a pulsing effect on a label (e.g., status dot)."""
    def to_b():
        if widget.winfo_exists():
            Animator.animate_color(widget, prop, color_a, color_b, duration=duration // 2,
                                   easing=ease_in_out_cubic, on_complete=to_a)
    
    def to_a():
        if widget.winfo_exists():
            Animator.animate_color(widget, prop, color_b, color_a, duration=duration // 2,
                                   easing=ease_in_out_cubic, on_complete=to_b)
    
    to_b()


def count_up(widget, target: int, duration: int = 800, prefix: str = '', suffix: str = ''):
    """Animates a label's text from 0 to target as a counting number."""
    def update(val):
        try:
            widget.configure(text=f'{prefix}{int(val)}{suffix}')
        except Exception:
            pass
    
    Animator.animate_value(
        widget, 0, target,
        duration=duration,
        easing=ease_out_expo,
        on_update=update,
        prop_name='count'
    )

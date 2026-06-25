"""
AEGIS Design System
Premium design tokens — spacing scale, radius scale, elevation, typography,
and a curated dark palette with warm undertones.
Every visual decision in the app flows through this file.
"""
import customtkinter as ctk


class AEGISTheme:
    
    # ── Color Palette ─────────────────────────────────────────────────────────
    # Carefully balanced dark palette with warm blue undertones.
    # No pure blacks, no pure whites, no neon primaries.
    
    COLORS = {
        # Surfaces (ordered by elevation — lowest to highest)
        'bg_base':         '#0C0E16',     # Deepest background — app window
        'bg_raised':       '#12141F',     # Sidebar, title bar, status bar
        'bg_surface':      '#1A1D2E',     # Cards, panels, modals
        'bg_surface_alt':  '#1F2337',     # Alternate surface / subtle contrast
        'bg_overlay':      '#252940',     # Hover states, input fields
        'bg_inset':        '#0F111A',     # Inset areas (video containers, code blocks)
        
        # Accent spectrum
        'accent':          '#7C6AFF',     # Primary action — rich periwinkle
        'accent_hover':    '#6B5CE6',     # Darker on hover
        'accent_muted':    '#5B4FCC',     # Pressed / active
        'accent_glow':     '#9B8FFF',     # Highlights, active nav text
        'accent_surface':  '#1D1A3A',     # Tinted surface for accent sections
        
        # Secondary accent
        'teal':            '#36D6B7',     # Secondary CTA — fresh teal
        'teal_hover':      '#2BBFA3',     # Hover
        'teal_muted':      '#1E8F7A',     # Subdued teal for backgrounds
        'teal_surface':    '#132E28',     # Tinted surface for teal sections
        
        # Semantic colors
        'success':         '#34D399',     # Soft emerald
        'success_surface': '#0F2922',     # Success background
        'warning':         '#FBBF24',     # Warm amber
        'warning_surface': '#2A2212',     # Warning background
        'error':           '#FB7185',     # Soft rose
        'error_surface':   '#2D1520',     # Error background
        
        # Text hierarchy (4 levels of emphasis)
        'text_primary':    '#ECEEF4',     # Headlines, high emphasis
        'text_secondary':  '#A3AAC2',     # Body text, labels
        'text_tertiary':   '#6B7394',     # Captions, hints, timestamps
        'text_disabled':   '#464D66',     # Disabled, inactive
        
        # Borders & dividers
        'border':          '#232840',     # Default border
        'border_subtle':   '#1C2035',     # Very subtle dividers
        'border_focus':    '#7C6AFF',     # Focus ring (= accent)
        
        # Interactive elements
        'hover':           '#252940',     # Generic hover lift
        'active':          '#2E3350',     # Active/pressed state
        'focus_ring':      '#7C6AFF40',  # Semi-transparent focus ring
    }
    
    # ── Typography ────────────────────────────────────────────────────────────
    # Strict type scale — every font usage should reference this.
    
    FONTS = {
        'display':        ('Inter', 28, 'bold'),     # Page titles
        'heading_lg':     ('Inter', 20, 'bold'),     # Section headers
        'heading_md':     ('Inter', 16, 'bold'),     # Card titles
        'heading_sm':     ('Inter', 14, 'bold'),     # Sub-section titles
        'body':           ('Inter', 13, 'normal'),   # Standard body text
        'body_sm':        ('Inter', 12, 'normal'),   # Smaller body
        'caption':        ('Inter', 11, 'normal'),   # Timestamps, hints
        'caption_sm':     ('Inter', 10, 'normal'),   # Micro text
        'overline':       ('Inter', 9, 'bold'),      # Section labels (ALL CAPS)
        'mono':           ('JetBrains Mono', 12, 'normal'),  # Code, IDs
        'mono_sm':        ('JetBrains Mono', 10, 'normal'),  # Small code
        'stat_number':    ('Inter', 32, 'bold'),     # Dashboard stat numbers
        'nav':            ('Inter', 13, 'normal'),   # Navigation items
        'nav_active':     ('Inter', 13, 'bold'),     # Active nav item
        'button':         ('Inter', 13, 'bold'),     # Button labels
        'button_sm':      ('Inter', 11, 'normal'),   # Small buttons
    }
    
    # ── Spacing Scale ─────────────────────────────────────────────────────────
    # Based on 4px grid. Use these values everywhere instead of magic numbers.
    
    SPACE = {
        'xxs': 2,
        'xs':  4,
        'sm':  8,
        'md':  12,
        'lg':  16,
        'xl':  20,
        'xxl': 24,
        'xxxl': 32,
        'section': 40,
    }
    
    # ── Border Radius ─────────────────────────────────────────────────────────
    
    RADIUS = {
        'xs':    4,
        'sm':    6,
        'md':    8,
        'lg':    12,
        'xl':    16,
        'xxl':   20,
        'pill':  100,
        
        # Legacy aliases for backward compatibility with widgets
        'medium': 8,
        'large':  12,
    }
    
    # ── Widget Heights ────────────────────────────────────────────────────────
    # Standardized heights for interactive elements.
    
    HEIGHT = {
        'input':      40,
        'input_sm':   34,
        'button':     40,
        'button_sm':  32,
        'button_xs':  26,
        'nav_item':   44,
        'status_bar': 30,
        'title_bar':  40,
    }
    
    # ── Icon Set ──────────────────────────────────────────────────────────────
    # Consistent icon mapping used throughout the app.
    
    ICONS = {
        'dashboard':  '⬡',
        'cameras':    '◎',
        'models':     '◇',
        'hermes':     '△',
        'storage':    '▤',
        'success':    '●',
        'warning':    '●',
        'error':      '●',
        'active':     '◉',
        'inactive':   '○',
        'add':        '+',
        'close':      '×',
        'minimize':   '─',
        'maximize':   '□',
        'refresh':    '↻',
        'chevron':    '›',
        'dot':        '·',
    }
    
    # ── Apply Global Appearance ───────────────────────────────────────────────
    
    @classmethod
    def apply(cls):
        ctk.set_appearance_mode('dark')
        ctk.set_default_color_theme('dark-blue')
    
    @classmethod
    def get_color(cls, key: str) -> str:
        # Support legacy key names for backward compatibility
        legacy_map = {
            'primary_bg':      'bg_base',
            'secondary_bg':    'bg_raised',
            'card_bg':         'bg_surface',
            'card_bg_alt':     'bg_surface_alt',
            'input_bg':        'bg_overlay',
            'text_muted':      'text_tertiary',
            'secondary_accent': 'teal',
        }
        key = legacy_map.get(key, key)
        return cls.COLORS.get(key, '#FFFFFF')
    
    @classmethod
    def get_font(cls, key: str) -> tuple:
        return cls.FONTS.get(key, cls.FONTS['body'])
    
    @classmethod
    def get_space(cls, key: str) -> int:
        return cls.SPACE.get(key, 12)
    
    @classmethod
    def get_radius(cls, key: str) -> int:
        return cls.RADIUS.get(key, 8)
    
    @classmethod
    def get_height(cls, key: str) -> int:
        return cls.HEIGHT.get(key, 40)
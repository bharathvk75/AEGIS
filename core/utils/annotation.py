import os
import cv2
import numpy as np
from datetime import datetime
from typing import Optional, Union

def annotate_snapshot(
    image_input: Union[str, np.ndarray],
    output_path: Optional[str] = None,
    camera_name: str = "Camera Feed",
    trigger_name: str = "Security Trigger",
    confidence: float = 0.85,
    severity: str = "warning",
    description: Optional[str] = None
) -> Optional[np.ndarray]:
    """
    Annotates a snapshot image with AEGIS V2 visual intelligence HUD overlays,
    timestamps, severity badges, and focus target frame.
    """
    try:
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                return None
            frame = cv2.imread(image_input)
        else:
            frame = image_input.copy()

        if frame is None or frame.size == 0:
            return None

        h, w, _ = frame.shape

        # Define color theme based on severity
        sev_lower = (severity or "info").lower()
        if sev_lower == "critical":
            badge_color = (68, 68, 239)    # Red BGR
            text_color = (255, 255, 255)
        elif sev_lower == "warning":
            badge_color = (11, 158, 245)   # Amber BGR
            text_color = (0, 0, 0)
        else:
            badge_color = (212, 182, 6)    # Cyan/Teal BGR
            text_color = (255, 255, 255)

        # 1. Overlay Top Bar Header (Semi-transparent black overlay)
        top_bar_height = max(50, int(h * 0.08))
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, top_bar_height), (15, 23, 42), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Bottom Bar for Description if available
        if description:
            bot_bar_height = max(40, int(h * 0.06))
            overlay_bot = frame.copy()
            cv2.rectangle(overlay_bot, (0, h - bot_bar_height), (w, h), (15, 23, 42), -1)
            cv2.addWeighted(overlay_bot, 0.75, frame, 0.25, 0, frame)

            # Draw Description Text
            desc_text = f"AI LOG: {description[:90]}..." if len(description) > 90 else f"AI LOG: {description}"
            cv2.putText(
                frame,
                desc_text,
                (15, h - int(bot_bar_height * 0.35)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (203, 213, 225),
                1,
                cv2.LINE_AA
            )

        # 2. Add AEGIS V2 Brand Badge & Timestamp
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title_text = f"AEGIS V2 | {camera_name.upper()} | {now_str}"
        cv2.putText(
            frame,
            title_text,
            (15, int(top_bar_height * 0.45)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        sub_text = f"RULE: {trigger_name}"
        cv2.putText(
            frame,
            sub_text,
            (15, int(top_bar_height * 0.85)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (148, 163, 184),
            1,
            cv2.LINE_AA
        )

        # 3. Add Severity & Confidence Badge (Top Right)
        conf_pct = int(confidence * 100) if confidence <= 1.0 else int(confidence)
        badge_text = f"{sev_lower.upper()} ({conf_pct}%)"
        (bw, bh), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        
        badge_x1 = w - bw - 30
        badge_y1 = int(top_bar_height * 0.2)
        badge_x2 = w - 15
        badge_y2 = int(top_bar_height * 0.8)

        cv2.rectangle(frame, (badge_x1, badge_y1), (badge_x2, badge_y2), badge_color, -1)
        cv2.putText(
            frame,
            badge_text,
            (badge_x1 + 8, badge_y1 + bh + 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            text_color,
            2,
            cv2.LINE_AA
        )

        # 4. Draw Center Focus Target Corners (Visual HUD Bounding Box)
        target_margin_w = int(w * 0.2)
        target_margin_h = int(h * 0.25) + top_bar_height // 2
        x1, y1 = target_margin_w, target_margin_h
        x2, y2 = w - target_margin_w, h - (target_margin_h // 2)

        line_len = min(w, h) // 12
        line_thickness = 2
        corner_color = badge_color

        # Top-left corner
        cv2.line(frame, (x1, y1), (x1 + line_len, y1), corner_color, line_thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + line_len), corner_color, line_thickness)
        # Top-right corner
        cv2.line(frame, (x2, y1), (x2 - line_len, y1), corner_color, line_thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + line_len), corner_color, line_thickness)
        # Bottom-left corner
        cv2.line(frame, (x1, y2), (x1 + line_len, y2), corner_color, line_thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - line_len), corner_color, line_thickness)
        # Bottom-right corner
        cv2.line(frame, (x2, y2), (x2 - line_len, y2), corner_color, line_thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - line_len), corner_color, line_thickness)

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, frame)

        return frame
    except Exception as e:
        print(f"[Annotation Error] Failed to annotate image: {e}")
        return None

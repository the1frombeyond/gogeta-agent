import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Pt


class PPTXHandler:
    """[BACKEND] Advanced PowerPoint / PPTX Engine with Premium Styling"""

    def __init__(self):
        pass

    def quick_view(self, path):
        """[BACKEND] Inventory deck layouts, text, and notes."""
        if not os.path.exists(path): return f"Error: Deck {path} not found."  # noqa: E701
        prs = Presentation(path)
        layouts = [f"{i}: {l.name}" for i, l in enumerate(prs.slide_layouts)]  # noqa: E741
        slides = []
        for i, slide in enumerate(prs.slides):
            text = [shape.text for shape in slide.shapes if hasattr(shape, "text")]
            notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
            slides.append({"slide": i+1, "layout": slide.slide_layout.name, "text_count": len(text), "has_notes": bool(notes)})

        return {
            "Layout Inventory": layouts,
            "Slide Count": len(prs.slides),
            "Slide Summaries": slides[:5]
        }

    def manifest(self, path, title_text, slides_content, template=None, bg_image=None):
        """[BACKEND] Create a premium deck from structured content."""
        prs = Presentation(template) if template else Presentation()

        # 1. Title Slide
        title_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_layout)

        # Apply Global Background
        if bg_image and os.path.exists(bg_image):
            slide.shapes.add_picture(bg_image, 0, 0, prs.slide_width, prs.slide_height)

        title = slide.shapes.title
        subtitle = slide.placeholders[1] if len(slide.placeholders) > 1 else None

        # STYLING: Premium Stark-Tech Red
        title.text = title_text
        self._apply_style(title, size=44, bold=True, color=RGBColor(255, 30, 30))

        if subtitle:
            subtitle.text = "ULTRAMAN | BEYONDER-DISCOVERY | STARK-TECH ?"
            self._apply_style(subtitle, size=24, italic=True, color=RGBColor(200, 200, 200))

        # 2. Content Slides
        for s_data in slides_content:
            layout_idx = s_data.get("layout_idx", 1)
            layout = prs.slide_layouts[layout_idx]
            slide = prs.slides.add_slide(layout)

            # Apply slide-specific background
            s_bg = s_data.get("bg_image", bg_image)
            if s_bg and os.path.exists(s_bg):
                 slide.shapes.add_picture(s_bg, 0, 0, prs.slide_width, prs.slide_height)

            if slide.shapes.title:
                slide.shapes.title.text = s_data.get("title", "Untitled Slide")
                self._apply_style(slide.shapes.title, size=36, bold=True, color=RGBColor(30, 144, 255))

            # Map body content
            body_text = s_data.get("body", "")
            if len(slide.placeholders) > 1:
                body = slide.placeholders[1]
                if hasattr(body, "text_frame"):
                    tf = body.text_frame
                    tf.word_wrap = True
                    if isinstance(body_text, list):
                        for line in body_text:
                            p = tf.add_paragraph()
                            p.text = "* " + str(line)
                            p.level = 0
                            self._apply_style(p, size=20, color=RGBColor(240, 240, 240))
                    else:
                        tf.text = str(body_text)
                        self._apply_style(tf.paragraphs[0], size=20, color=RGBColor(240, 240, 240))

        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        prs.save(path)
        return f"Premium Deck saved to {path} with {len(prs.slides)} slides."

    def _apply_style(self, target, size=18, bold=False, italic=False, color=None):
        """Apply uniform premium styling to a text object or paragraph."""
        try:
            if hasattr(target, "text_frame"):
                tf = target.text_frame
                if not tf.paragraphs: tf.add_paragraph()  # noqa: E701
                p = tf.paragraphs[0]
                run = p.runs[0] if p.runs else p.add_run()
            elif hasattr(target, "runs"):
                run = target.runs[0] if target.runs else target.add_run()
            else:
                return

            font = run.font
            font.name = 'Arial' # System safe
            font.size = Pt(size)
            font.bold = bold
            font.italic = italic
            if color: font.color.rgb = color  # noqa: E701
        except: pass  # noqa: E701, E722

    def audit(self, path):
        """[BACKEND] Deep QA for text overflow and placeholder mismatch."""
        if not os.path.exists(path): return "Error: Path not found."  # noqa: E701
        prs = Presentation(path)
        issues = []
        for i, slide in enumerate(prs.slides):
            for shape in slide.shapes:
                if hasattr(shape, "text") and len(shape.text) > 800:
                    issues.append(f"Slide {i+1}: Critical overflow ({len(shape.text)} chars).")
                if shape.is_placeholder and not shape.has_text_frame and shape.placeholder_format.type != 1:
                     issues.append(f"Slide {i+1}: Empty non-title placeholder ({shape.name}).")

        return {"issues": issues if issues else "CLEAN | NO OVERFLOW DETECTED."}

def pptx_quick_view(path): return PPTXHandler().quick_view(path)
def pptx_manifest(path, title, slides_content=None, content_list=None, template=None, bg_image=None):
    content = slides_content if slides_content is not None else content_list
    return PPTXHandler().manifest(path, title, content, template, bg_image)
def pptx_audit(path): return PPTXHandler().audit(path)

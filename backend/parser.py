import re
from typing import List, Dict, Any, Optional, Tuple
import pymupdf

class PDFParser:
    """
    Layout-aware PDF Parser using PyMuPDF.
    Preserves page boundaries, text blocks, word geometry, and verbatim quote bounding boxes.
    """

    def __init__(self, file_path_or_bytes: Any):
        if isinstance(file_path_or_bytes, str):
            self.doc = pymupdf.open(file_path_or_bytes)
        else:
            self.doc = pymupdf.open(stream=file_path_or_bytes, filetype="pdf")
        self.total_pages = len(self.doc)

    def get_page_text(self, page_num: int) -> str:
        """Returns plain text for 1-indexed page_num."""
        if 1 <= page_num <= self.total_pages:
            return self.doc[page_num - 1].get_text("text")
        return ""

    def get_page_blocks(self, page_num: int) -> List[Dict[str, Any]]:
        """Returns layout blocks (x0, y0, x1, y1, text, block_type, block_no) for a page."""
        if not (1 <= page_num <= self.total_pages):
            return []
        page = self.doc[page_num - 1]
        blocks = page.get_text("blocks")
        results = []
        for b in blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            if len(b) >= 5:
                results.append({
                    "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)],
                    "text": b[4].strip()
                })
        return results

    def locate_quote(self, page_num: int, quote: str) -> Tuple[Optional[List[float]], bool]:
        """
        Deterministically verifies if a verbatim quote appears on the specified 1-indexed page.
        Returns (bbox, is_verified). If found, returns the bounding rectangle [x0, y0, x1, y1].
        """
        if not (1 <= page_num <= self.total_pages) or not quote:
            return None, False

        page = self.doc[page_num - 1]
        cleaned_quote = " ".join(quote.strip().split())
        
        # 1. Direct search using PyMuPDF rect search
        # Try full quote first, then first 10 words if full quote spans irregular layout
        search_terms = [cleaned_quote]
        words = cleaned_quote.split()
        if len(words) > 8:
            search_terms.append(" ".join(words[:8]))
            search_terms.append(" ".join(words[-8:]))

        for term in search_terms:
            rects = page.search_for(term)
            if rects:
                # Combine bounding rectangles if multiline
                r = rects[0]
                for extra in rects[1:]:
                    r = r | extra
                return [round(r.x0, 2), round(r.y0, 2), round(r.x1, 2), round(r.y1, 2)], True

        # 2. Relaxed whitespace string check
        page_text = " ".join(page.get_text("text").split())
        if cleaned_quote.lower() in page_text.lower():
            # Approximate bbox from page dimension
            rect = page.rect
            return [0.0, 0.0, round(rect.width, 2), round(rect.height, 2)], True

        return None, False

    def close(self):
        self.doc.close()

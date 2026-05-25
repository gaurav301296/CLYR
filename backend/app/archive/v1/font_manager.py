import os
import urllib.request
import logging
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# Directory where fonts will be downloaded and cached
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")

# Mapping of language codes to their Noto Sans font family name
FONT_MAP = {
    "hi": "NotoSansDevanagari",
    "mr": "NotoSansDevanagari", # Marathi shares Devanagari
    "bn": "NotoSansBengali",
    "te": "NotoSansTelugu",
    "ta": "NotoSansTamil",
    "gu": "NotoSansGujarati",
    "kn": "NotoSansKannada",
    "ml": "NotoSansMalayalam",
    "pa": "NotoSansGurmukhi",
    "or": "NotoSansOriya"
}

# Keep track of registered fonts to avoid duplicate registration overhead
_registered_fonts = set()

def ensure_fonts(lang_code: str):
    """
    Downloads the Regular and Bold Noto Sans font files for the given language (if not already present)
    and registers them with ReportLab.
    """
    # Normalize language code
    lang = lang_code.lower().strip()
    
    # English uses built-in fonts (Helvetica)
    if lang == "en" or lang not in FONT_MAP:
        return "Helvetica", "Helvetica-Bold"
        
    font_family = FONT_MAP[lang]
    
    reg_font_name = font_family
    bold_font_name = f"{font_family}-Bold"
    
    # If already registered, return immediately
    if reg_font_name in _registered_fonts and bold_font_name in _registered_fonts:
        return reg_font_name, bold_font_name
        
    # Ensure font directory exists
    os.makedirs(FONTS_DIR, exist_ok=True)
    
    font_styles = [
        {"suffix": "Regular", "name": reg_font_name},
        {"suffix": "Bold", "name": bold_font_name}
    ]
    
    for style in font_styles:
        file_name = f"{font_family}-{style['suffix']}.ttf"
        local_path = os.path.join(FONTS_DIR, file_name)
        
        # Test if file exists but is corrupt before we check if we need to download.
        # This will delete any corrupt file on disk immediately.
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0 and style["name"] not in _registered_fonts:
            try:
                pdfmetrics.registerFont(TTFont(style["name"], local_path))
                _registered_fonts.add(style["name"])
                logger.info(f"Registered existing font {style['name']} with ReportLab")
            except Exception as e:
                logger.warning(f"Existing font {style['name']} is corrupt/unregistrable, deleting: {e}")
                try:
                    os.remove(local_path)
                except OSError as remove_err:
                    logger.error(f"Failed to remove corrupt file {local_path}: {remove_err}")

        # Download if file doesn't exist or is empty
        if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
            # Use jsDelivr CDN for stable, versioned font delivery
            # Falls back to GitHub raw if CDN fails
            url = f"https://cdn.jsdelivr.net/gh/notofonts/noto-fonts@main/hinted/ttf/{font_family}/{file_name}"
            from app.utils.ssrf import is_safe_url
            if not is_safe_url(url):
                logger.error(f"Font download URL failed SSRF check: {url}")
                return "Helvetica", "Helvetica-Bold"
            logger.info(f"Downloading font {file_name} from {url}...")
            temp_path = f"{local_path}.tmp"
            try:
                # Use User-Agent header to avoid HTTP 403 / CDN blocks
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                )
                with urllib.request.urlopen(req) as response:
                    with open(temp_path, "wb") as f:
                        f.write(response.read())
                
                # Check for minimum valid font size to reject error pages or empty data
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1000:
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    os.rename(temp_path, local_path)
                    logger.info(f"Successfully downloaded {file_name} to {local_path}")
                else:
                    raise ValueError(f"Downloaded font file {file_name} is empty or too small.")
            except Exception as e:
                logger.error(f"Failed to download font {file_name} from {url}: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                # Fallback to Helvetica if download fails
                return "Helvetica", "Helvetica-Bold"
        
        # Register font with ReportLab if we downloaded it or it hasn't been registered yet
        if style["name"] not in _registered_fonts:
            try:
                pdfmetrics.registerFont(TTFont(style["name"], local_path))
                _registered_fonts.add(style["name"])
                logger.info(f"Registered font {style['name']} with ReportLab")
            except Exception as e:
                logger.error(f"Failed to register font {style['name']}: {e}")
                # Remove the corrupt file to trigger redownload next time
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                        logger.info(f"Deleted corrupt font file {local_path}")
                    except OSError as remove_err:
                        logger.error(f"Failed to delete corrupt font file {local_path}: {remove_err}")
                # Fallback to Helvetica if registration fails
                return "Helvetica", "Helvetica-Bold"
                
    # Register font family for bold/normal linking in ReportLab
    if font_family not in _registered_fonts:
        try:
            pdfmetrics.registerFontFamily(font_family, normal=reg_font_name, bold=bold_font_name)
            _registered_fonts.add(font_family)
            logger.info(f"Registered font family {font_family} with ReportLab")
        except Exception as e:
            logger.error(f"Failed to register font family {font_family}: {e}")
            # Non-fatal error, we still return the font names
            
    return reg_font_name, bold_font_name

def get_font_names(lang_code: str):
    """
    Exposes the font pair for a given language code. Resolves and registers on first call.
    """
    return ensure_fonts(lang_code)

"""Icon service - handles random icon selection"""
import os
import random
from flask import current_app

SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}


def get_random_icon() -> str | None:
    """Get a random icon filename from the icons folder"""
    icons_dir = os.path.join(current_app.config['STATIC_DIR'], 'icons')
    
    if not os.path.exists(icons_dir):
        return None
    
    icons = [
        f for f in os.listdir(icons_dir)
        if os.path.isfile(os.path.join(icons_dir, f))
        and os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
    ]
    
    if not icons:
        return None
    
    return random.choice(icons)

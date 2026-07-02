import os
import json
from PIL import Image
from PIL.ExifTags import TAGS

# Supported Extensions
IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
TEXT_EXTS = ('.txt',)

def get_exif_string(image_path):
    """Extracts basic EXIF metadata and returns it as a searchable string."""
    exif_text = []
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            if exifdata:
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exifdata.get(tag_id)
                    # We only care about string data (descriptions, camera models, dates)
                    if isinstance(data, str) and data.strip():
                        exif_text.append(f"{tag}: {data.strip()}")
    except Exception as e:
        # Silently pass errors for files without EXIF or unreadable formats
        pass
    return " | ".join(exif_text)

def get_text_content(text_path):
    """Reads a text file and returns its content."""
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return ""

def build_index(root_dir='.'):
    index_data = {}

    # Walk through repository excluding hidden folders (like .git, .github)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prevent searching inside hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        
        # We don't want to process the root scripts folder if there are testing files there
        if 'scripts' in dirpath:
            continue

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in IMAGE_EXTS and ext not in TEXT_EXTS:
                continue
            
            base_name = os.path.splitext(filename)[0]
            rel_dir = os.path.relpath(dirpath, root_dir)
            if rel_dir == '.':
                rel_dir = ""
            
            # Create a unique grouping ID for the baseName within a folder
            item_id = f"{rel_dir}/{base_name}"
            
            if item_id not in index_data:
                index_data[item_id] = {
                    "baseName": base_name,
                    "dirName": rel_dir,
                    "textContents": "",
                    "imageMetadata": ""
                }
            
            file_path = os.path.join(dirpath, filename)

            # Append content based on type
            if ext in IMAGE_EXTS:
                exif_data = get_exif_string(file_path)
                if exif_data:
                    index_data[item_id]["imageMetadata"] += exif_data + " "
            elif ext in TEXT_EXTS:
                txt_content = get_text_content(file_path)
                if txt_content:
                    index_data[item_id]["textContents"] += txt_content + " "

    # Convert the dict to a flat list for Fuse.js
    output = list(index_data.values())
    
    # Clean up trailing spaces
    for item in output:
        item["textContents"] = item["textContents"].strip()
        item["imageMetadata"] = item["imageMetadata"].strip()

    # Write to JSON file
    out_path = os.path.join(root_dir, 'search_index.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, separators=(',', ':')) # Minified JSON
        
    print(f"Generated search_index.json with {len(output)} items.")

if __name__ == "__main__":
    build_index()
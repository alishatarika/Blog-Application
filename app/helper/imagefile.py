from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
import os
# ================= UPLOAD SETTINGS =================
UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# ================= HELPER FUNCTIONS =================
def delete_file_if_exists(file_path: Optional[str]):
    """Delete a file from static/uploads if it exists."""
    try:
        if file_path:
            absolute_path = Path(file_path.lstrip("/")) 
            if absolute_path.exists():
                absolute_path.unlink()
                print(f"Deleted old file: {absolute_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")


def save_upload_file(upload_file: UploadFile) -> Optional[str]:
    """Save uploaded file in static/uploads with date-time filename."""
    try:
        file_ext = os.path.splitext(upload_file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        timestamp = datetime.now().strftime("%d_%m_%y,%H.%M.%S") 
        safe_filename = upload_file.filename.replace(" ", "_")
        filename = f"{timestamp}_{safe_filename}"

        file_path = UPLOAD_DIR / filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return f"/static/uploads/{filename}"

    except Exception as e:
        print(f"Error saving file: {e}")
        return None
    finally:
        upload_file.file.close()
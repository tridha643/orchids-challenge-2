from PIL import Image
import io
from typing import Optional

class ImageProcessor:
    def __init__(self, target_width: int = 400):
        self.target_width = target_width
        
    async def process_hero_image(self, image_bytes: bytes) -> bytes:
        """Resize and optimize hero image for storage and prompt use"""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Calculate new dimensions maintaining aspect ratio
            original_width, original_height = image.size
            aspect_ratio = original_height / original_width
            new_height = int(self.target_width * aspect_ratio)
            
            # Resize image
            resized_image = image.resize((self.target_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to bytes with optimization
            output_buffer = io.BytesIO()
            resized_image.save(
                output_buffer, 
                format='PNG', 
                optimize=True,
                quality=85
            )
            
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"Image processing failed: {str(e)}")
            # Return original bytes if processing fails
            return image_bytes
    
    def get_image_dimensions(self, image_bytes: bytes) -> Optional[tuple]:
        """Get image dimensions without full processing"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return image.size
        except:
            return None 
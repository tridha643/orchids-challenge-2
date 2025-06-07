from supabase import create_client, Client
import asyncio
from typing import Union
import os
import mimetypes

class SupabaseStorage:
    def __init__(self, url: str, key: str, bucket_name: str = "rawsites"):
        self.client: Client = create_client(url, key)
        self.bucket_name = bucket_name
        
    async def upload_file(self, file_data: Union[bytes, str], file_path: str) -> str:
        """
        Upload file to Supabase Storage and return public URL
        """
        try:
            # Ensure bucket exists
            try:
                self.client.storage.get_bucket(self.bucket_name)
                print(f"✅ Bucket '{self.bucket_name}' exists")
            except Exception as bucket_error:
                print(f"🔄 Creating bucket '{self.bucket_name}'...")
                try:
                    self.client.storage.create_bucket(self.bucket_name, {"public": True})
                    print(f"✅ Created bucket '{self.bucket_name}'")
                except Exception as create_error:
                    print(f"❌ Failed to create bucket: {create_error}")
                    raise
            
            # Convert string to bytes if needed
            if isinstance(file_data, str):
                file_data = file_data.encode('utf-8')
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                if file_path.endswith('.html'):
                    content_type = 'text/html'
                elif file_path.endswith('.css'):
                    content_type = 'text/css'
                elif file_path.endswith('.png'):
                    content_type = 'image/png'
                else:
                    content_type = 'application/octet-stream'
            
            print(f"📤 Uploading {file_path} ({len(file_data)} bytes, {content_type})")
            
            # Upload file with proper options and cache control
            file_options = {
                "content-type": content_type,
                "upsert": "true"
            }
            
            # Add specific headers for HTML files to ensure proper rendering
            if content_type == 'text/html':
                file_options.update({
                    "cache-control": "public, max-age=3600",
                    "content-disposition": "inline"
                })
            
            result = self.client.storage.from_(self.bucket_name).upload(
                file=file_data,
                path=file_path,
                file_options=file_options
            )
            
            print(f"✅ Upload result: {result}")
            
            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            print(f"🔗 Public URL: {public_url}")
            
            return public_url
            
        except Exception as e:
            print(f"❌ Upload error details: {type(e).__name__}: {str(e)}")
            raise Exception(f"Upload failed for {file_path}: {str(e)}")
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from Supabase Storage"""
        try:
            result = self.client.storage.from_(self.bucket_name).download(file_path)
            return result
        except Exception as e:
            raise Exception(f"Download failed for {file_path}: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            self.client.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            print(f"Delete failed for {file_path}: {str(e)}")
            return False
    
    async def close(self):
        """Cleanup connection"""
        pass  # Supabase client handles connection cleanup 
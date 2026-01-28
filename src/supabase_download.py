import requests
import io
import pandas as pd
from typing import List, Dict, Any

def download_and_process_files(file_urls: List[str]) -> List[Dict[str, Any]]:
    """
    Download files from URLs and process them based on file type.
    
    Args:
        file_urls: List of public URLs to files in Supabase Storage
        
    Returns:
        List of dicts containing file metadata and content
    """
    processed_files = []
    
    for url in file_urls:
        try:
            # Download the file
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract filename from URL
            filename = url.split('/')[-1].split('?')[0]
            content_type = response.headers.get('content-type', '')
            
            file_data = {
                'filename': filename,
                'url': url,
                'size': len(response.content),
                'content_type': content_type,
                'content': None,
                'error': None
            }
            print(f"Downloading: {filename} ({file_data['size']} bytes)")
                
            file_data['content'] = response.content
            processed_files.append(file_data)
            print(f"✓ Successfully downloaded: {filename}")
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to download {url}: {str(e)}")
            processed_files.append({
                'filename': url.split('/')[-1],
                'url': url,
                'error': str(e)
            })
        except Exception as e:
            print(f"✗ Failed to process {url}: {str(e)}")
            processed_files.append({
                'filename': url.split('/')[-1],
                'url': url,
                'error': str(e)
            })
    
    return processed_files
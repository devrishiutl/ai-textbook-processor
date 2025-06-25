#!/usr/bin/env python3
"""
Batch processing script for multiple textbooks or image sets
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def process_batch_config(config_file):
    """Process multiple inputs from a JSON configuration file"""
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    results = []
    
    for item in config['inputs']:
        print(f"\n🚀 Processing: {item['name']}")
        print(f"📚 {item['subject']} - {item['standard']} - {item['chapter']}")
        
        # Build command
        cmd = [
            'python', 'main_docling.py',
            '--content', item['content'],
            '--standard', item['standard'],
            '--subject', item['subject'],
            '--chapter', item['chapter'],
            '--type', item.get('type', 'pdf')
        ]
        
        try:
            # Run the processing
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Success: {item['name']}")
                results.append({
                    'name': item['name'],
                    'status': 'success',
                    'output': result.stdout
                })
            else:
                print(f"❌ Failed: {item['name']}")
                print(f"Error: {result.stderr}")
                results.append({
                    'name': item['name'],
                    'status': 'failed',
                    'error': result.stderr
                })
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout: {item['name']}")
            results.append({
                'name': item['name'],
                'status': 'timeout',
                'error': 'Processing timeout after 5 minutes'
            })
    
    return results

def create_sample_config():
    """Create a sample batch configuration file"""
    
    sample_config = {
        "inputs": [
            {
                "name": "Biology Chapter 1",
                "content": "biology_ch1.pdf",
                "standard": "Class 10",
                "subject": "Biology",
                "chapter": "Life Processes",
                "type": "pdf"
            },
            {
                "name": "Physics Diagrams Set 1",
                "content": "light_diagram1.jpg,light_diagram2.png,prism_diagram.jpg",
                "standard": "Class 10",
                "subject": "Physics", 
                "chapter": "Light - Reflection and Refraction",
                "type": "images"
            },
            {
                "name": "Math Chapter 2",
                "content": "algebra_textbook_ch2.pdf",
                "standard": "Class 9",
                "subject": "Mathematics",
                "chapter": "Polynomials",
                "type": "pdf"
            }
        ]
    }
    
    with open('batch_config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("📄 Created sample configuration: batch_config.json")
    print("Edit this file with your actual content paths and details.")

def process_directory_images(directory, standard, subject, chapter):
    """Process all images in a directory as one batch"""
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
    
    image_files = []
    for file_path in Path(directory).iterdir():
        if file_path.suffix.lower() in image_extensions:
            image_files.append(str(file_path))
    
    if not image_files:
        print(f"❌ No image files found in directory: {directory}")
        return
    
    # Join all image paths with commas
    content = ','.join(image_files)
    
    print(f"🖼️ Processing {len(image_files)} images from {directory}")
    
    cmd = [
        'python', 'main_docling.py',
        '--content', content,
        '--standard', standard,
        '--subject', subject,
        '--chapter', chapter,
        '--type', 'images'
    ]
    
    try:
        result = subprocess.run(cmd, timeout=300)
        if result.returncode == 0:
            print(f"✅ Successfully processed directory: {directory}")
        else:
            print(f"❌ Failed to process directory: {directory}")
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout processing directory: {directory}")

def main():
    if len(sys.argv) < 2:
        print("""
🎓 Batch Processing for Textbook AI Agent

Usage:
  python batch_process.py config batch_config.json     # Process from config file
  python batch_process.py create-config                # Create sample config
  python batch_process.py directory [DIR] [STANDARD] [SUBJECT] [CHAPTER]  # Process directory of images

Examples:
  python batch_process.py create-config
  python batch_process.py config my_textbooks.json
  python batch_process.py directory ./science_diagrams "Class 10" "Physics" "Optics"
        """)
        return
    
    command = sys.argv[1]
    
    if command == "create-config":
        create_sample_config()
        
    elif command == "config":
        if len(sys.argv) < 3:
            print("❌ Please provide config file path")
            return
        
        config_file = sys.argv[2]
        if not os.path.exists(config_file):
            print(f"❌ Config file not found: {config_file}")
            return
            
        results = process_batch_config(config_file)
        
        # Print summary
        print("\n" + "="*50)
        print("📊 BATCH PROCESSING SUMMARY")
        print("="*50)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_count = len(results)
        
        print(f"✅ Successful: {success_count}/{total_count}")
        print(f"❌ Failed: {total_count - success_count}/{total_count}")
        
        for result in results:
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_emoji} {result['name']}: {result['status']}")
    
    elif command == "directory":
        if len(sys.argv) < 6:
            print("❌ Usage: python batch_process.py directory [DIR] [STANDARD] [SUBJECT] [CHAPTER]")
            return
            
        directory = sys.argv[2]
        standard = sys.argv[3]
        subject = sys.argv[4]
        chapter = sys.argv[5]
        
        if not os.path.exists(directory):
            print(f"❌ Directory not found: {directory}")
            return
            
        process_directory_images(directory, standard, subject, chapter)
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main() 
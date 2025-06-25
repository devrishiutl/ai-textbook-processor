import os
import sys
import argparse
from tools import (
    process_educational_content_tool,
    format_educational_output_tool
)

def main():
    """Entry point - handles CLI arguments and orchestrates processing"""
    
    parser = argparse.ArgumentParser(
        description="🎓 Advanced Textbook AI Agent with Docling Document Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --content textbook.pdf --standard "Class 10" --subject "Biology" --chapter "Cell Structure"
  %(prog)s --content diagram.jpg --standard "Grade 8" --subject "Physics" --chapter "Light" --type images
  %(prog)s --content "img1.jpg,img2.png" --standard "Class 12" --subject "Chemistry" --chapter "Organic" --type images
        """
    )
    
    parser.add_argument("--content", required=True, 
                       help="Path to PDF file, image file, or comma-separated image paths")
    parser.add_argument("--standard", required=True,
                       help="Student standard/grade (e.g., 'Class 10', '5th Grade')")
    parser.add_argument("--subject", required=True,
                       help="Subject name (e.g., 'Science', 'Mathematics', 'Biology')")
    parser.add_argument("--chapter", required=True,
                       help="Chapter/topic name (e.g., 'Plant Kingdom', 'Algebra')")
    parser.add_argument("--type", choices=["pdf", "images", "text"], default="pdf",
                       help="Type of content input (default: pdf)")
    
    args = parser.parse_args()
    
    print("🚀 Starting Advanced Educational Content Processing...")
    print(f"📚 Subject: {args.subject} | Standard: {args.standard} | Chapter: {args.chapter}")
    
    # Validate inputs
    if args.type == "pdf":
        if not os.path.exists(args.content):
            print(f"❌ PDF file not found: {args.content}")
            sys.exit(1)
        if not args.content.lower().endswith('.pdf'):
            print(f"❌ Please provide a PDF file (got: {args.content})")
            sys.exit(1)
            
    elif args.type == "images":
        if "," in args.content:
            image_paths = [path.strip() for path in args.content.split(",")]
        else:
            image_paths = [args.content]
        
        for img_path in image_paths:
            if not os.path.exists(img_path):
                print(f"❌ Image file not found: {img_path}")
                sys.exit(1)
        
        args.content = image_paths
    
    # Process educational content using tools
    try:
        result = process_educational_content_tool(
            content_source=args.content,
            standard=args.standard,
            subject=args.subject,
            chapter=args.chapter,
            content_type=args.type
        )
        
        if result and not result.get('error'):
            print("\n" + "="*70)
            print("🎉 ADVANCED EDUCATIONAL CONTENT GENERATION COMPLETE")
            print("="*70)
            
            # Format and display the output using tool
            formatted_output = format_educational_output_tool(result)
            print(formatted_output)
            
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'Failed to generate content'
            print(f"❌ {error_msg}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error during content processing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
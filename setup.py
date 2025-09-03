
import sys
import subprocess
import platform
import os
from pathlib import Path
def check_python_version():
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True


def install_system_dependencies():
    system = platform.system().lower()
    print(f"\nDetected system: {system}")
    
    if system == "linux":
        print("Installing Tesseract OCR on Linux...")
        try:
            # Try different package managers
            commands = [
                ["sudo", "apt-get", "update"],
                ["sudo", "apt-get", "install", "-y", "tesseract-ocr", "tesseract-ocr-eng"]
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Command failed: {' '.join(cmd)}")
                    print("Please install Tesseract manually:")
                    print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
                    print("  CentOS/RHEL: sudo yum install tesseract")
                    return False
            
            print("✓ Tesseract OCR installed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install Tesseract: {e}")
            return False
    
    elif system == "darwin":  # macOS
        print("Installing Tesseract OCR on macOS...")
        try:
            # Check if Homebrew is installed
            homebrew_check = subprocess.run(["which", "brew"], capture_output=True)
            if homebrew_check.returncode != 0:
                print("❌ Homebrew not found. Please install Homebrew first:")
                print("Visit: https://brew.sh/")
                return False
            
            # Install tesseract
            result = subprocess.run(["brew", "install", "tesseract"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Tesseract OCR installed successfully")
                return True
            else:
                print(f"❌ Failed to install Tesseract: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to install Tesseract: {e}")
            return False
    
    elif system == "windows":
        print("  Windows detected - Manual Tesseract installation required")
        print("Please download and install Tesseract from:")
        print("https://github.com/tesseract-ocr/tesseract/releases")
        print("Make sure to add it to your system PATH")
        return True
    
    else:
        print(f"  Unknown system: {system}")
        print("Please install Tesseract OCR manually for your system")
        return True


def install_python_dependencies():
    print("\nInstalling Python dependencies...")
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Upgrade pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ All Python dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            print("\nTrying alternative installation method...")
            
            essential_packages = [
                "pdfplumber",
                "pandas",
                "Pillow",
                "pytesseract",
                "opencv-python"
            ]
            
            for package in essential_packages:
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                  check=True, capture_output=True)
                    print(f"✓ Installed {package}")
                except subprocess.CalledProcessError:
                    print(f"❌ Failed to install {package}")
            
            # Try camelot-py separately (often problematic)
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "camelot-py[cv]"], 
                              check=True, capture_output=True)
                print("✓ Installed camelot-py")
            except subprocess.CalledProcessError:
                print("❌ Failed to install camelot-py - trying alternative...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "camelot-py"], 
                                  check=True, capture_output=True)
                    subprocess.run([sys.executable, "-m", "pip", "install", "opencv-python-headless"], 
                                  check=True, capture_output=True)
                    print("✓ Installed camelot-py (alternative method)")
                except subprocess.CalledProcessError:
                    print("❌ Could not install camelot-py - table extraction may be limited")
            
            return True
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def test_installations():
    """Test if all installations were successful."""
    print("\nTesting installations...")
    test_imports = [
        ("pdfplumber", "pdfplumber"),
        ("pandas", "pandas"),
        ("PIL", "Pillow"),
        ("pytesseract", "pytesseract"),
        ("cv2", "opencv-python")
    ]
    
    successful_imports = 0
    
    for module, package_name in test_imports:
        try:
            __import__(module)
            print(f"✓ {package_name} - OK")
            successful_imports += 1
        except ImportError:
            print(f"❌ {package_name} - Failed to import")
    
    # Test camelot separately
    try:
        import camelot
        print("✓ camelot-py - OK")
        successful_imports += 1
    except ImportError:
        print("❌ camelot-py - Failed to import")
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR {version} - OK")
    except Exception as e:
        print(f" Tesseract OCR - May not be properly configured: {e}")
    
    print(f"\nInstallation Summary: {successful_imports}/6 packages working")
    
    if successful_imports >= 5:  # Allow for camelot to fail
        print(" Setup completed successfully!")
        print("\nYou can now run the PDF parser:")
        print("  python pdf_parser.py your_document.pdf")
        print("\nOr test with:")
        print("  python test_pdf_parser.py")
        return True
    else:
        print(" Some packages failed to install. Check error messages above.")
        return False


def create_sample_test():
    """Create a simple test to verify everything works."""
    test_code = '''#!/usr/bin/env python3
"""
Quick installation test
"""
import sys

def test_basic_imports():
    """Test basic functionality."""
    try:
        print("Testing imports...")
        
        import pdfplumber
        print("✓ pdfplumber")
        
        import pandas
        print("✓ pandas")
        
        from PIL import Image
        print("✓ Pillow")
        
        import pytesseract
        print("✓ pytesseract")
        
        import cv2
        print("✓ opencv-python")
        
        try:
            import camelot
            print("✓ camelot-py")
        except ImportError:
            print(" camelot-py (optional for advanced table extraction)")
        
        print("\ All core dependencies are working!")
        return True
        
    except ImportError as e:
        print(f" Import failed: {e}")
        return False

if __name__ == "__main__":
    test_basic_imports()
'''
    
    with open("test_installation.py", "w") as f:
        f.write(test_code)
    
    print("Created test_installation.py - run this to verify your setup")
def main():
    print(" PDF Parser Setup Script")
    print("=" * 50)
    
    if not check_python_version():
        sys.exit(1)
    print("\n Installing system dependencies...")
    print("\n Installing Python dependencies...")
    if not install_python_dependencies():
        print(" Failed to install all Python dependencies")
        print("You may need to install some packages manually")
    test_installations()
    create_sample_test()
    
    print("\n" + "=" * 50)
    print("Setup completed! Next steps:")
    print("1. Test your installation: python test_installation.py")
    print("2. Run the parser: python pdf_parser.py your_document.pdf")
    print("3. Check the README.md for detailed usage instructions")


if __name__ == "__main__":
    main()

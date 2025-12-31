#!/usr/bin/env python3
"""
Simple Argos Translate REST API Server
This server provides a local translation API using Argos Translate.
"""

import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import argostranslate.package
import argostranslate.translate

# Server configuration (can be overridden by environment variables)
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5100))

# Track installed languages
installed_languages = set()


def ensure_language_package(from_code: str, to_code: str) -> bool:
    """Download and install language package if not already installed."""
    pair_key = f"{from_code}->{to_code}"
    
    if pair_key in installed_languages:
        return True
    
    try:
        # Update package index
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        # Find the package for this language pair
        package_to_install = next(
            (pkg for pkg in available_packages 
             if pkg.from_code == from_code and pkg.to_code == to_code),
            None
        )
        
        if package_to_install is None:
            print(f"No package found for {from_code} -> {to_code}")
            return False
        
        # Check if already installed
        installed_packages = argostranslate.package.get_installed_packages()
        is_installed = any(
            pkg.from_code == from_code and pkg.to_code == to_code
            for pkg in installed_packages
        )
        
        if not is_installed:
            print(f"Installing language package: {from_code} -> {to_code}")
            download_path = package_to_install.download()
            argostranslate.package.install_from_path(download_path)
            print(f"Installed: {from_code} -> {to_code}")
        
        installed_languages.add(pair_key)
        return True
        
    except Exception as e:
        print(f"Error installing package: {e}")
        return False


def check_package_available(from_code: str, to_code: str) -> bool:
    """Check if a language package is available (installed or can be installed)."""
    pair_key = f"{from_code}->{to_code}"
    
    if pair_key in installed_languages:
        return True
    
    try:
        # Check installed packages first
        installed_packages = argostranslate.package.get_installed_packages()
        is_installed = any(
            pkg.from_code == from_code and pkg.to_code == to_code
            for pkg in installed_packages
        )
        
        if is_installed:
            installed_languages.add(pair_key)
            return True
        
        # Check available packages
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        package_exists = any(
            pkg.from_code == from_code and pkg.to_code == to_code
            for pkg in available_packages
        )
        
        return package_exists
        
    except Exception as e:
        print(f"Error checking package: {e}")
        return False


def translate_direct(text: str, from_code: str, to_code: str) -> str:
    """Translate text directly using Argos Translate (single hop)."""
    # Ensure language package is installed
    if not ensure_language_package(from_code, to_code):
        raise Exception(f"Language pair not available: {from_code} -> {to_code}")
    
    # Get installed languages
    installed_languages_list = argostranslate.translate.get_installed_languages()
    
    from_lang = next(
        (lang for lang in installed_languages_list if lang.code == from_code), 
        None
    )
    to_lang = next(
        (lang for lang in installed_languages_list if lang.code == to_code), 
        None
    )
    
    if from_lang is None or to_lang is None:
        raise Exception(f"Language not found: {from_code} or {to_code}")
    
    translation = from_lang.get_translation(to_lang)
    if translation is None:
        raise Exception(f"No translation available: {from_code} -> {to_code}")
    
    return translation.translate(text)


def translate_text(text: str, from_code: str, to_code: str) -> str:
    """
    Translate text using Argos Translate.
    If direct translation is not available, use English as pivot language.
    For example: vi -> zh becomes vi -> en -> zh
    """
    # If source and target are the same, return original text
    if from_code == to_code:
        return text
    
    # Check if direct translation is available
    if check_package_available(from_code, to_code):
        print(f"Direct translation: {from_code} -> {to_code}")
        return translate_direct(text, from_code, to_code)
    
    # If not available, try pivot through English
    pivot_lang = "en"
    
    # If either source or target is English, we can't pivot
    if from_code == pivot_lang or to_code == pivot_lang:
        raise Exception(f"No translation available: {from_code} -> {to_code}")
    
    # Check if pivot translation is possible
    can_pivot_from = check_package_available(from_code, pivot_lang)
    can_pivot_to = check_package_available(pivot_lang, to_code)
    
    if not can_pivot_from:
        raise Exception(f"Cannot translate {from_code} -> {pivot_lang} (needed for pivot)")
    
    if not can_pivot_to:
        raise Exception(f"Cannot translate {pivot_lang} -> {to_code} (needed for pivot)")
    
    # Perform pivot translation
    print(f"Pivot translation: {from_code} -> {pivot_lang} -> {to_code}")
    
    # Step 1: Translate source -> English
    intermediate_text = translate_direct(text, from_code, pivot_lang)
    
    # Step 2: Translate English -> target
    final_text = translate_direct(intermediate_text, pivot_lang, to_code)
    
    return final_text


def get_available_languages():
    """Get list of available language pairs."""
    try:
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        return [
            {"from": pkg.from_code, "to": pkg.to_code, "name": pkg.from_name + " -> " + pkg.to_name}
            for pkg in available_packages
        ]
    except Exception as e:
        print(f"Error getting languages: {e}")
        return []


class TranslateHandler(BaseHTTPRequestHandler):
    """HTTP request handler for translation API."""
    
    def send_json_response(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self.send_json_response({"status": "ok", "engine": "argos-translate"})
        elif self.path == "/languages":
            languages = get_available_languages()
            self.send_json_response({"languages": languages})
        else:
            self.send_json_response({"error": "Not found"}, 404)
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/translate":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                
                text = data.get("q", "")
                source = data.get("source", "en")
                target = data.get("target", "vi")
                
                if not text:
                    self.send_json_response({"error": "No text provided"}, 400)
                    return
                
                # Translate
                result = translate_text(text, source, target)
                self.send_json_response({"translatedText": result})
                
            except json.JSONDecodeError:
                self.send_json_response({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
        else:
            self.send_json_response({"error": "Not found"}, 404)
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[Argos Server] {args[0]}")


def main():
    """Start the server."""
    print(f"🌐 Argos Translate Server starting on http://{HOST}:{PORT}")
    print("📦 Language packages will be downloaded on first use")
    print("━" * 50)
    
    server = HTTPServer((HOST, PORT), TranslateHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        server.shutdown()


if __name__ == "__main__":
    main()

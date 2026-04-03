"""
ThreatGPT – Desktop launcher
Starts Flask in a background thread, then opens a native pywebview window.

Requirements:
    pip install flask pywebview
"""

import threading
import time
import sys
import os

# ── Add project root to path ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app  # Flask app


def run_flask():
    """Run Flask server (suppressing reloader in thread)."""
    app.run(port=8501, debug=False, use_reloader=False, threaded=True)


def main():
    try:
        import webview
    except ImportError:
        print("=" * 50)
        print("pywebview not found. Install it with:")
        print("  pip install pywebview")
        print()
        print("Then re-run this script.")
        print()
        print("Alternatively, run Flask directly:")
        print("  python app.py")
        print("And open http://localhost:8501 in your browser.")
        print("=" * 50)
        # Fallback: just run Flask and open browser
        import webbrowser
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        time.sleep(1.2)
        webbrowser.open("http://localhost:8501")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Give Flask time to start
    time.sleep(1.0)

    # Open native desktop window
    window = webview.create_window(
        title="ThreatGPT — Advanced Threat Intelligence Engine",
        url="http://localhost:8501",
        width=1200,
        height=760,
        min_size=(900, 600),
        resizable=True
    )
    webview.start()

if __name__ == "__main__":
    main()
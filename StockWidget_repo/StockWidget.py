# filename: StockWidget.py
# python3 -m PyInstaller -F -w .\StockWidget.py --name StockWidget --icon .\StockWidget.ico --add-data ".\StockWidget.ico;."
import sys, ctypes
from App import App, APP_NAME

if __name__ == "__main__":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"{APP_NAME}.1")
    except Exception:
        pass

    app = App(sys.argv)
    sys.exit(app.exec())

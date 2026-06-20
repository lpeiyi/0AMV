import sys, os, json, ctypes
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
import keyboard as kb

from band_panel import BandPanel
from band_engine import BandEngine
from band_settings import SettingsDialog

APP_NAME = "BandMonitor"
CONFIG_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), APP_NAME)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_config(cfg):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_FILE)

class BandApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)

        cfg = load_config()

        # Init engine (fetch data + compute bands)
        self.engine = BandEngine()
        try:
            self.engine.fetch_all()
            engine_cfg = cfg.get("strategy", {})
            if engine_cfg:
                self.engine.strategy.update(engine_cfg)
            self.engine.refresh()
        except Exception as e:
            print(f"Engine init error: {e}")

        self.win = BandPanel(cfg, self.engine)
        self.win.set_on_change(self.save_now)
        self.win.set_open_settings_callback(self.open_settings)

        icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip(APP_NAME)
        menu = QMenu()
        menu.addAction(QAction("显示/隐藏", self, triggered=self.toggle_win))
        menu.addAction(QAction("设置…", self, triggered=self.open_settings))
        menu.addSeparator()
        menu.addAction(QAction("退出", self, triggered=self.quit_app))
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray)
        self.tray.show()

        self.settings_dlg = None
        self.win.show()
        self.win.raise_()
        self.win.activateWindow()
        self.win.setFocus(Qt.ActiveWindowFocusReason)
        self.save_now()

        # Hotkey
        self._hotkey_registered = []
        try:
            kb.add_hotkey("ctrl+alt+f", self.toggle_win)
            self._hotkey_registered.append("ctrl+alt+f")
        except:
            pass

    def _on_tray(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_win()

    def toggle_win(self):
        if self.win.isVisible():
            self.win.hide()
        else:
            self.win.show()
            self.win.raise_()
            self.win.activateWindow()
            self.win.setFocus(Qt.ActiveWindowFocusReason)

    def open_settings(self):
        if self.settings_dlg and self.settings_dlg.isVisible():
            self.settings_dlg.raise_()
            self.settings_dlg.activateWindow()
            return
        self.settings_dlg = SettingsDialog(self.win, self.win, app=self)
        screen = QApplication.primaryScreen().availableGeometry()
        self.settings_dlg.adjustSize()
        cx = screen.left() + (screen.width() - self.settings_dlg.width()) // 2
        cy = screen.top() + (screen.height() - self.settings_dlg.height()) // 2
        self.settings_dlg.move(QPoint(cx, cy))
        self.settings_dlg.show()
        self.settings_dlg.raise_()
        self.settings_dlg.activateWindow()

    def quit_app(self):
        for hk in getattr(self, "_hotkey_registered", []):
            try:
                kb.remove_hotkey(hk)
            except:
                pass
        self.tray.hide()
        self.save_now()
        sys.exit(0)

    def set_hotkey(self, seq):
        for hk in getattr(self, "_hotkey_registered", []):
            try:
                kb.remove_hotkey(hk)
            except:
                pass
        self._hotkey_registered = []
        hk_lower = seq.lower().replace(" ", "")
        try:
            kb.add_hotkey(hk_lower, self.toggle_win)
            self._hotkey_registered.append(hk_lower)
        except:
            pass

    def save_now(self):
        cfg = self.win.current_config()
        cfg["strategy"] = dict(self.engine.strategy)
        hotkey_raw = getattr(self, "_hotkey_registered", ["Ctrl+Alt+F"])
        cfg["hotkey"] = hotkey_raw[0] if hotkey_raw else "Ctrl+Alt+F"
        save_config(cfg)

if __name__ == "__main__":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"{APP_NAME}.1")
    except:
        pass
    app = BandApp(sys.argv)
    sys.exit(app.exec())

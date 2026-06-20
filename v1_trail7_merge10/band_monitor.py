import sys, os, json, ctypes
from PySide6.QtCore import Qt, QPoint, QTimer, QThread, QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
import keyboard as kb

from band_panel import BandPanel
from band_engine import BandEngine
from band_settings import SettingsDialog

APP_NAME = "0AMVMonitor"
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

class EngineWorker(QObject):
    finished = Signal()
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
    def run(self):
        self.engine.fetch_all()
        self.finished.emit()

class BandApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)

        cfg = load_config()

        self.engine = None

        self.win = BandPanel(cfg, None)
        self.win.set_on_change(self.save_now)
        self.win.set_open_settings_callback(self.open_settings)

        ico_path = os.path.join(sys._MEIPASS, '0AMV.ico') if getattr(sys, 'frozen', False) else os.path.join(os.path.dirname(__file__), '0AMV.ico')
        app_icon = QIcon(ico_path) if os.path.isfile(ico_path) else self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.setWindowIcon(app_icon)
        self.tray = QSystemTrayIcon(app_icon, self)
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
        QApplication.processEvents()

        # Hotkey (独立于 engine，立即注册)
        self._hotkey_registered = []
        try:
            kb.add_hotkey("ctrl+alt+f", self.toggle_win)
            self._hotkey_registered.append("ctrl+alt+f")
        except:
            pass

        # 异步启动 engine 获取数据（不阻塞 UI）
        QTimer.singleShot(0, self._start_engine)

    def _start_engine(self):
        cfg = load_config()
        cache_path = cfg.get("cache_path")
        engine = BandEngine(cache_path=cache_path)
        engine_cfg = cfg.get("strategy", {})
        if engine_cfg:
            engine.strategy.update(engine_cfg)

        # 尝试加载缓存——命中则秒出真实数据
        cache_ok = engine.load_cache()
        # 配置的路径无效时，回退到默认路径
        if not cache_ok and cache_path:
            default_path = os.path.join(CONFIG_DIR, "cache.pkl")
            if default_path != engine.cache_path:
                engine.cache_path = default_path
                cache_ok = engine.load_cache()

        if cache_ok:
            import pandas as pd
            today = pd.Timestamp.now().normalize()
            stale_days = (today - engine.last_fetch_date).days if engine.last_fetch_date is not None else 999
            if stale_days <= 7:
                self.engine = engine
                self.win.engine = engine
                self.win.on_engine_ready()
                self.save_now()

        # 后台线程始终刷新
        self._engine_worker = EngineWorker(engine)
        self._engine_thread = QThread(self)
        self._engine_worker.moveToThread(self._engine_thread)
        self._engine_thread.started.connect(self._engine_worker.run)
        self._engine_worker.finished.connect(self._on_engine_ready)
        self._engine_worker.finished.connect(self._engine_thread.quit)
        self._engine_thread.start()

    def _on_engine_ready(self):
        self.engine = self._engine_worker.engine
        self.win.engine = self.engine
        self.win.on_engine_ready()
        self.save_now()

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
        if hasattr(self, "_engine_thread") and self._engine_thread.isRunning():
            self._engine_thread.quit()
            self._engine_thread.wait(2000)
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
        if self.engine is not None:
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

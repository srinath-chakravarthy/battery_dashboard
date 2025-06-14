import panel as pn
from battery_dashboard.main import create_app
from battery_dashboard.config import PANEL_PORT, PANEL_ALLOW_WEBSOCKET_ORIGIN
if __name__ == "__main__":
    pn.config.autoreload = True
    app = create_app()
    app.show(port=PANEL_PORT,
             threaded=True,
             allow_websocket_origin=[PANEL_ALLOW_WEBSOCKET_ORIGIN])
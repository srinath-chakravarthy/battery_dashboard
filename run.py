import panel as pn
from battery_dashboard.main import create_app
from battery_dashboard.config import PANEL_PORT, PANEL_ALLOW_WEBSOCKET_ORIGIN, PANEL_HOST
if __name__ == "__main__":
    pn.config.autoreload = True
    app = create_app()
    app.show(port=8561,
             address='192.168.80.30',
             threaded=True,
             allow_websocket_origin=['*'])
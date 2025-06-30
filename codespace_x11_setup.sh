#!/bin/bash
# codespace_x11_setup.sh
# Sets up Xvfb, x11vnc, and noVNC for GUI forwarding in GitHub Codespaces
# to launch gui.py, run 'export DISPLAY=:1'
# cd /workspaces/checkmate && export DISPLAY=:1 && python3 gui.py
# https://fuzzy-engine-x9769w75xrx3vjxw-6080.app.github.dev/vnc.html

set -e

# Install Xvfb, x11-apps, x11vnc, noVNC, and dependencies
sudo apt-get update && sudo apt-get install -y xvfb x11-apps x11vnc novnc
pip install websockify numpy

# Kill any previous Xvfb, x11vnc, or websockify processes
pkill Xvfb || true
pkill x11vnc || true
pkill websockify || true

# Start Xvfb on display :1 with access control disabled
nohup Xvfb :1 -screen 0 1920x1080x24 -ac > /tmp/xvfb.log 2>&1 &
sleep 3

# Export display for this session
export DISPLAY=:1

# Start x11vnc on display :1 with explicit port
touch /tmp/x11vnc.log
nohup x11vnc -display :1 -nopw -forever -shared -rfbport 5900 > /tmp/x11vnc.log 2>&1 &
sleep 3

# Start websockify/noVNC
touch /tmp/websockify.log
nohup websockify --web=/usr/share/novnc/ 6080 localhost:5900 > /tmp/websockify.log 2>&1 &

# Get Codespace URL
CODESPACE_URL="https://$(hostname)-6080.app.github.dev"

cat <<EOF

X11 and VNC services are now running successfully!

To run your Tkinter GUI application:
  cd /workspaces/checkmate
  export DISPLAY=:1
  python3 gui.py

To access the GUI in your browser:
  $CODESPACE_URL/vnc.html

If you see a black screen in VNC, make sure your GUI application is running.
You can check running GUI applications with:
  export DISPLAY=:1 && xwininfo -tree -root

Log files: /tmp/xvfb.log /tmp/x11vnc.log /tmp/websockify.log

Troubleshooting:
- If VNC shows a black screen, restart your GUI application
- If connection fails, try rerunning this setup script
- Check log files for detailed error information

EOF
exit 0
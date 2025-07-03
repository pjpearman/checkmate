#!/bin/bash
# codespace_x11_setup.sh
# Sets up Xvfb, x11vnc, and noVNC for GUI forwarding in GitHub Codespaces
# to launch gui.py, run 'export DISPLAY=:1'
# cd /workspaces/checkmate && export DISPLAY=:1 && python3 gui.py

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

# Start x11vnc on display :1 with explicit port and better WebSocket support
touch /tmp/x11vnc.log
nohup x11vnc -display :1 -nopw -forever -shared -rfbport 5900 -noxdamage -noscr -nowf > /tmp/x11vnc.log 2>&1 &
sleep 3

# Start websockify/noVNC with better compatibility
touch /tmp/websockify.log
nohup websockify --web=/usr/share/novnc/ --wrap-mode=ignore 6080 localhost:5900 > /tmp/websockify.log 2>&1 &
sleep 3

# Make port 6080 public for external access (GitHub Codespaces)
if command -v gh >/dev/null 2>&1; then
    echo "Making port 6080 public for external access..."
    gh codespace ports visibility 6080:public --codespace "$CODESPACE_NAME" >/dev/null 2>&1 || echo "Note: Could not set port visibility automatically"
fi

# Get Codespace URL - GitHub Codespaces format
if [ -n "$CODESPACE_NAME" ]; then
    CODESPACE_URL="https://$CODESPACE_NAME-6080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
else
    # Fallback to hostname-based URL
    CODESPACE_URL="https://$(hostname)-6080.app.github.dev"
fi

# Ensure DISPLAY is set for the current session
echo "export DISPLAY=:1" >> ~/.bashrc

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
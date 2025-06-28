#!/bin/bash
# codespace_x11_setup.sh
# Sets up Xvfb, x11vnc, and noVNC for GUI forwarding in GitHub Codespaces
# to launch gui.py, run 'export DISPLAY=:1'
# cd /workspaces/checkmate && export DISPLAY=:1 && python3 gui.py
# https://humble-yodel-vg94gv96wwrcpx4w-6080.app.github.dev/vnc.html

set -e

# Install Xvfb, x11-apps, x11vnc, noVNC, and dependencies
sudo apt-get update && sudo apt-get install -y xvfb x11-apps x11vnc novnc
pip install websockify numpy

# Kill any previous Xvfb, x11vnc, or websockify processes
pkill Xvfb || true
pkill x11vnc || true
pkill websockify || true

# Start Xvfb on display :1
nohup Xvfb :1 -screen 0 1920x1080x24 > /tmp/xvfb.log 2>&1 &
sleep 2

# Export display for this session
export DISPLAY=:1

# Start x11vnc on display :1
touch /tmp/x11vnc.log
nohup x11vnc -display :1 -nopw -forever -shared > /tmp/x11vnc.log 2>&1 &
sleep 2

# Start websockify/noVNC
touch /tmp/websockify.log
nohup websockify --web=/usr/share/novnc/ 6080 localhost:5900 > /tmp/websockify.log 2>&1 &

# Get Codespace URL
CODESPACE_URL="https://$(hostname)-6080.app.github.dev"

cat <<EOF

Xvfb, x11vnc, and noVNC are now running.
To run your Tkinter app:
  export DISPLAY=:1
  python your_tkinter_script.py

To access the GUI, open in your browser:
  $CODESPACE_URL

Log files: /tmp/xvfb.log /tmp/x11vnc.log /tmp/websockify.log

EOF
exit 0
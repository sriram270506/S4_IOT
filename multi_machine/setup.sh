#!/bin/bash
# Setup script for multi-machine SDN testbed
# Run on each laptop separately

set -e

echo "========================================================================"
echo "  SDN Multi-Machine Testbed - Setup Script"
echo "========================================================================"

# Detect which machine we're on
read -p "Which machine are you setting up? [controller/ap/monitor]: " MACHINE

case $MACHINE in
    controller)
        echo ""
        echo "Setting up CONTROLLER LAPTOP (192.168.1.100)"
        echo ""
        
        # Check Python
        if ! command -v python3 &> /dev/null; then
            echo "❌ Python3 not installed"
            exit 1
        fi
        
        echo "✓ Python3 found: $(python3 --version)"
        
        # Install Python dependencies
        echo ""
        echo "Installing Python dependencies..."
        pip3 install -q flask numpy matplotlib
        
        echo ""
        echo "✓ Controller setup complete!"
        echo ""
        echo "To start the controller:"
        echo "  cd multi_machine"
        echo "  python3 controller_server.py config.json"
        echo ""
        echo "Dashboard will be available at: http://127.0.0.1:8080"
        ;;
    
    ap)
        echo ""
        echo "Setting up AP LAPTOP (192.168.1.101)"
        echo ""
        
        # Check Python
        if ! command -v python3 &> /dev/null; then
            echo "❌ Python3 not installed"
            exit 1
        fi
        
        echo "✓ Python3 found: $(python3 --version)"
        
        # Check hostapd
        if ! command -v hostapd &> /dev/null; then
            echo "⚠️  hostapd not found. Installing..."
            sudo apt-get update
            sudo apt-get install -y hostapd dnsmasq wireless-tools
        else
            echo "✓ hostapd found"
        fi
        
        # Check iw
        if ! command -v iw &> /dev/null; then
            echo "⚠️  iw not found. Installing..."
            sudo apt-get install -y wireless-tools
        else
            echo "✓ iw found"
        fi
        
        echo ""
        echo "✓ AP setup complete!"
        echo ""
        echo "To start the AP agent:"
        echo "  cd multi_machine"
        echo "  python3 ap_agent.py config.json"
        echo ""
        echo "Note: Make sure hostapd is configured with:"
        echo "  • Interface: wlan0"
        echo "  • SSID: SDN-TestNet"
        echo "  • Channel: 6"
        ;;
    
    monitor)
        echo ""
        echo "Setting up MONITOR/JAMMER LAPTOP (192.168.1.102)"
        echo ""
        
        # Check Python
        if ! command -v python3 &> /dev/null; then
            echo "❌ Python3 not installed"
            exit 1
        fi
        
        echo "✓ Python3 found: $(python3 --version)"
        
        # Check iperf3
        if ! command -v iperf3 &> /dev/null; then
            echo "⚠️  iperf3 not found. Installing..."
            sudo apt-get update
            sudo apt-get install -y iperf3
        else
            echo "✓ iperf3 found: $(iperf3 --version)"
        fi
        
        echo ""
        echo "✓ Monitor setup complete!"
        echo ""
        echo "To start the monitor agent:"
        echo "  cd multi_machine"
        echo "  python3 monitor_agent.py config.json"
        echo ""
        echo "For phones:"
        echo "  • Install iperf3 app from Google Play Store"
        echo "  • Connect to WiFi network: SDN-TestNet"
        echo "  • Start iperf3 server on phones"
        ;;
    
    *)
        echo "❌ Unknown machine type: $MACHINE"
        echo "Please use: controller, ap, or monitor"
        exit 1
        ;;
esac

echo ""
echo "========================================================================"

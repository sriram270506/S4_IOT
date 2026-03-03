# PRE-DEPLOYMENT CHECKLIST

## Hardware Verification

### Controller Laptop
- [ ] Connected to home WiFi (5 GHz band preferred)
- [ ] IP address noted: `___.___.___.___`
- [ ] Python 3.7+ installed: `python3 --version`
- [ ] Can reach AP laptop: `ping 192.168.1.101`
- [ ] Can reach Monitor laptop: `ping 192.168.1.102`

### AP Laptop
- [ ] Connected to home WiFi
- [ ] IP address noted: `___.___.___.___`
- [ ] Linux OS confirmed (Ubuntu/Debian preferred)
- [ ] Python 3.7+ installed: `python3 --version`
- [ ] hostapd installed: `hostapd -v`
- [ ] WiFi AP mode supported: `iw list | grep "AP mode"`
- [ ] Can reach Controller laptop: `ping 192.168.1.100`
- [ ] Can reach Monitor laptop: `ping 192.168.1.102`

### Monitor Laptop
- [ ] Connected to home WiFi
- [ ] IP address noted: `___.___.___.___`
- [ ] Python 3.7+ installed: `python3 --version`
- [ ] iperf3 installed: `iperf3 --version`
- [ ] ping works: `ping 8.8.8.8`
- [ ] Can reach Controller laptop: `ping 192.168.1.100`
- [ ] Can reach AP laptop: `ping 192.168.1.101`

### Phone 1
- [ ] iperf3 app installed (from Play Store)
- [ ] Phone can see "SDN-TestNet" WiFi network
- [ ] Phone connected to "SDN-TestNet"
- [ ] IP address noted (Settings → About): `192.168.88.___`
- [ ] iperf3 app opens without errors
- [ ] Battery > 50% (for stable connection)

### Phone 2
- [ ] iperf3 app installed (from Play Store)
- [ ] Phone can see "SDN-TestNet" WiFi network
- [ ] Phone connected to "SDN-TestNet"
- [ ] IP address noted (Settings → About): `192.168.88.___`
- [ ] iperf3 app opens without errors
- [ ] Battery > 50% (for stable connection)

---

## Software Installation

### Controller Laptop
```bash
cd /path/to/multi_machine
bash setup.sh
# Select: controller
```
- [ ] Flask installed: `pip3 show flask`
- [ ] NumPy installed: `pip3 show numpy`
- [ ] Matplotlib installed: `pip3 show matplotlib`

### AP Laptop
```bash
cd /path/to/multi_machine
bash setup.sh
# Select: ap
```
- [ ] hostapd installed: `hostapd -v`
- [ ] iw installed: `which iw`
- [ ] iwconfig installed: `which iwconfig`

### Monitor Laptop
```bash
cd /path/to/multi_machine
bash setup.sh
# Select: monitor
```
- [ ] iperf3 installed: `iperf3 --version`
- [ ] ping available: `which ping`

---

## Configuration File Setup

Edit `multi_machine/config.json`:

```json
{
  "network": {
    "controller_ip": "FILL_THIS_IN",
    "ap_ip": "FILL_THIS_IN",
    "monitor_ip": "FILL_THIS_IN"
  }
}
```

- [ ] Controller IP updated
- [ ] AP IP updated
- [ ] Monitor IP updated
- [ ] All IPs verified to be reachable
- [ ] No typos in IP addresses
- [ ] JSON is valid: `python3 -m json.tool config.json`

---

## Connectivity Test

### Test 1: Ping Between Laptops

From Controller laptop:
```bash
ping -c 3 192.168.1.101  # AP
ping -c 3 192.168.1.102  # Monitor
```
- [ ] Both pings successful (no packet loss)

From AP laptop:
```bash
ping -c 3 192.168.1.100  # Controller
ping -c 3 192.168.1.102  # Monitor
```
- [ ] Both pings successful (no packet loss)

From Monitor laptop:
```bash
ping -c 3 192.168.1.100  # Controller
ping -c 3 192.168.1.101  # AP
```
- [ ] Both pings successful (no packet loss)

### Test 2: WiFi Network

From Controller laptop:
```bash
iwconfig  # or: nmtui
```
- [ ] Home WiFi network visible
- [ ] Connected to home WiFi (5 GHz preferred)
- [ ] Signal strength good (> -70 dBm)

### Test 3: Phone Connectivity

On Phone 1:
```
WiFi Settings → SDN-TestNet → Info
```
- [ ] SSID: SDN-TestNet visible
- [ ] Signal strength good
- [ ] IP address: 192.168.88.x
- [ ] Gateway: 192.168.88.1

On Phone 2:
```
WiFi Settings → SDN-TestNet → Info
```
- [ ] SSID: SDN-TestNet visible
- [ ] Signal strength good
- [ ] IP address: 192.168.88.x
- [ ] Gateway: 192.168.88.1

---

## Pre-Experiment Tests

### Test 1: Controller Server Startup

On Controller laptop:
```bash
cd /path/to/multi_machine
python3 controller_server.py config.json
```

Expected output:
```
[xx:xx:xx] [CONTROLLER] Controller initialized
[xx:xx:xx] [CONTROLLER] Controller listening on 192.168.1.100:9000
[xx:xx:xx] [CONTROLLER] Controller threads started
```

- [ ] Server starts without errors
- [ ] Listening on correct port
- [ ] No module import errors
- [ ] Can be stopped with Ctrl+C

### Test 2: AP Agent Startup

On AP laptop:
```bash
cd /path/to/multi_machine
python3 ap_agent.py config.json
```

Expected output:
```
[xx:xx:xx] [AP_AGENT] AP Agent initialized on 192.168.1.101:9001
[xx:xx:xx] [AP_AGENT] AP Agent threads started
```

- [ ] Agent starts without errors
- [ ] Can reach controller (logs should show contact)
- [ ] Can be stopped with Ctrl+C

### Test 3: Monitor Agent Startup

On Monitor laptop:
```bash
cd /path/to/multi_machine
python3 monitor_agent.py config.json
```

Expected output:
```
[xx:xx:xx] [MONITOR] Monitor Agent initialized (MAC: aa:bb:cc:dd:ee:ff)
[xx:xx:xx] [MONITOR] Monitor Agent started
```

- [ ] Agent starts without errors
- [ ] Can reach controller (logs should show contact)
- [ ] Can be stopped with Ctrl+C

### Test 4: Integration Test

Start all three in different terminals (from Test 1, 2, 3 above):

Terminal 1 (Controller):
```bash
python3 controller_server.py config.json
```

Terminal 2 (AP):
```bash
python3 ap_agent.py config.json
```

Terminal 3 (Monitor):
```bash
python3 monitor_agent.py config.json
```

Wait 5 seconds, then check Controller logs:
- [ ] Controller receives metrics from AP agent
- [ ] Controller receives metrics from Monitor agent
- [ ] No error messages

---

## Phone Setup Verification

### Phone 1 - iperf3 Server

1. [ ] iperf3 app installed on phone
2. [ ] Open iperf3 app
3. [ ] Tap "Server" button
4. [ ] Wait for "Server started on port 5201"
5. [ ] Leave running for full experiment duration
6. [ ] Leave WiFi enabled

### Phone 2 - iperf3 Server

1. [ ] iperf3 app installed on phone
2. [ ] Open iperf3 app
3. [ ] Tap "Server" button
4. [ ] Wait for "Server started on port 5201"
5. [ ] Leave running for full experiment duration
6. [ ] Leave WiFi enabled

---

## Final Readiness Check

### Code Files Verified
- [ ] `config.json` present and updated
- [ ] `controller_server.py` present
- [ ] `ap_agent.py` present
- [ ] `monitor_agent.py` present
- [ ] `orchestrator.py` present
- [ ] `dashboard.py` present
- [ ] `setup.sh` present
- [ ] `README.md` present
- [ ] All files have correct permissions

### Documentation Ready
- [ ] README.md reviewed
- [ ] COMPLETE_GUIDE.md available
- [ ] PHONE_SETUP.md reviewed
- [ ] ARCHITECTURE_REFINED.md reviewed
- [ ] Printed or accessible on laptop

### Synchronization
- [ ] All 3 laptops have synchronized time
  ```bash
  sudo ntpdate -s time.nist.gov
  # or: sudo timedatectl set-ntp true
  ```
- [ ] Time difference < 1 second between machines

### Backup
- [ ] Original code backed up
- [ ] config.json backed up
- [ ] Test run results backed up
- [ ] Screenshots captured (if needed)

---

## Experiment Day Checklist

### 1 Hour Before
- [ ] Charge all devices to 100%
- [ ] Close unnecessary applications
- [ ] Disable auto-sleep on all laptops
- [ ] Disable screen lock on phones
- [ ] Review presentation script

### 30 Minutes Before
- [ ] All 3 laptops powered on
- [ ] All 3 laptops connected to home WiFi
- [ ] Both phones charged and connected to WiFi
- [ ] Terminal windows open and ready
- [ ] Browser window ready for dashboard

### 10 Minutes Before
- [ ] Run connectivity test (ping all machines)
- [ ] Verify controller server can start
- [ ] Verify AP agent can start
- [ ] Verify Monitor agent can start
- [ ] Take screenshot of setup (for documentation)

### During Experiment
- [ ] Follow orchestrator output
- [ ] Watch for expected log messages
- [ ] Monitor dashboard in browser
- [ ] Note any errors or unexpected behavior
- [ ] Keep phones stable and within AP range

### After Experiment
- [ ] Save all output logs
- [ ] Verify `sdn_testbed_metrics.json` created
- [ ] Take screenshots of results
- [ ] Export dashboard data (if applicable)
- [ ] Backup all results

---

## Troubleshooting Reference

See `COMPLETE_GUIDE.md` under "Troubleshooting" for:
- Cannot reach controller from AP/Monitor
- Phones don't see SDN-TestNet
- Jammer not detected
- Channel switch fails
- Apps crash on startup

Quick commands:
```bash
# Test connectivity
ping 192.168.1.100
ping 8.8.8.8

# Check Python
python3 --version

# Check installed packages
pip3 list | grep -E "flask|numpy|matplotlib"

# Check WiFi on AP
hostapd -v
iw phy phy0 channels

# Check iperf3
iperf3 --version

# View controller logs
tail -f controller.log

# Validate JSON
python3 -m json.tool config.json
```

---

## Sign-Off

- [ ] All hardware verified
- [ ] All software installed
- [ ] All configuration correct
- [ ] All connectivity tests passed
- [ ] All pre-experiment tests passed
- [ ] Ready for deployment

**Date Checked:** _______________
**Checked By:** _______________
**Any Issues:** _______________

---

**STATUS: READY TO RUN** ✅

Next: Execute `python3 orchestrator.py config.json`

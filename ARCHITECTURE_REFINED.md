# REFINED ARCHITECTURE: WiFi-Connected Distributed SDN Testbed

## FINAL SYSTEM DESIGN

### Network Topology
```
                    ┌─────────────────┐
                    │  Home WiFi      │
                    │  (Internet)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌──────▼──────┐      ┌──────▼──────┐
   │Controller│         │   AP        │      │  Monitor/   │
   │ Laptop   │         │  Laptop     │      │  Jammer LP  │
   │          │         │             │      │             │
   │Ryu SDN   │◄────┐   │ hostapd     │      │ UDP Jammer  │
   │ Port 6633│     │   │ Channel 6   │      │ Packet Gen  │
   │          │     │   │             │      │             │
   │ Flask    │     │   │ hostapd_cli │      │ Metrics     │
   │ Port 8080│     │   │ (control)   │      │ Reporter    │
   │          │     │   │             │      │             │
   └──────────┘     │   └──────┬──────┘      └─────────────┘
                    │          │
              [WiFi] Comms     [WiFi] AP Signal
              via UDP msgs      (SDN-TestNet)
                    │          │
        ┌───────────┘          │
        │                      │
   ┌────▼────┐         ┌──────▼──────┐
   │  Phone1  │         │   Phone2    │
   │ iperf3   │         │  iperf3     │
   │ server   │         │  server     │
   └──────────┘         └─────────────┘

=== Key Points ===
• Controller, AP, Monitor are on HOME WiFi (non-interfering band, e.g., 5GHz)
• AP laptop ALSO broadcasts SDN-TestNet on 2.4 GHz Channel 6 for phones
• Phones connect to AP's SDN-TestNet (not home WiFi)
• All inter-laptop communication via home WiFi using UDP sockets
• Phones only need to connect to AP's WiFi signal for measurements
```

---

## COMMUNICATION PROTOCOL (WiFi-based)

### Between Laptops (via Home WiFi, UDP)

#### 1. AP → Controller (Every 2 seconds)
```json
{
  "source": "ap_agent",
  "timestamp": 1234567890.123,
  "ap_metrics": {
    "channel": 6,
    "connected_clients": ["00:11:22:33:44:55", "00:11:22:33:44:66"],
    "channel_utilization_percent": 45.2,
    "rssi_per_client": {
      "00:11:22:33:44:55": -55,
      "00:11:22:33:44:66": -58
    },
    "tx_power": 20,
    "bandwidth": "20MHz"
  }
}
```

#### 2. Monitor → Controller (Every 1 second during baseline, every 0.5s during attack)
```json
{
  "source": "monitor_agent",
  "timestamp": 1234567890.123,
  "monitor_metrics": {
    "my_mac": "aa:bb:cc:dd:ee:ff",
    "ping_latency_ms": 15.2,
    "ping_target": "8.8.8.8",
    "local_throughput_mbps": 0.0,
    "jammer_active": true,
    "jammer_packet_rate_pps": 8500,
    "channel_scans": {
      "channel_6": {"noise": -90, "interference": 20},
      "channel_11": {"noise": -92, "interference": 5}
    }
  }
}
```

#### 3. Controller → AP (Commands via UDP)
```json
{
  "command": "switch_channel",
  "target_channel": 11,
  "reason": "jammer_detected_on_channel_6"
}
```
OR
```json
{
  "command": "blacklist_mac",
  "target_mac": "aa:bb:cc:dd:ee:ff",
  "reason": "jammer_flooding"
}
```

### Between Phones & AP (WiFi, standard)
- Phones connect to AP's WiFi SSID: "SDN-TestNet"
- Phones get IP via DHCP: 192.168.88.x range
- iperf3 runs on each phone on port 5201

---

## EXPERIMENT PHASES (30-40 seconds total)

### PHASE 1: SETUP (0-2 seconds)
```
✓ Controller: Start Ryu + Flask dashboard
✓ AP: Start hostapd on Channel 6 (SSID: SDN-TestNet)
✓ Phones: Connect to SDN-TestNet, start iperf3 servers
✓ Monitor: Start agent, register with controller
✓ Verify: All components communicate
```

### PHASE 2: BASELINE (2-12 seconds)
```
Metrics collected:
  • Throughput: iperf3 from controller to Phone1 & Phone2
  • Latency: ping from Monitor to 8.8.8.8
  • RSSI: Reported by AP per connected client
  • Channel: 6 (default)
  • Jammer: OFF

Expected results:
  ✓ Phone1: ~4.5 Mbps
  ✓ Phone2: ~4.5 Mbps
  ✓ Total: ~9 Mbps
  ✓ Latency: <50ms
  ✓ RSSI: -50 to -60 dBm
```

### PHASE 3: JAMMER ACTIVE (12-22 seconds)
```
Monitor/Jammer laptop:
  • Joins SDN-TestNet WiFi as a client (gets 192.168.88.100)
  • Starts UDP packet flood: ~8000 packets/second of 1500-byte packets
  • Target: broadcast address (causes channel congestion)
  • Duration: 10 seconds

Effects:
  ✓ Throughput drops: ~0.5-1 Mbps per phone
  ✓ Latency increases: >200ms
  ✓ RSSI degrades: -70 to -80 dBm
  ✓ Channel utilization: >95%

Controller detects:
  • High packet rate from jammer MAC (8000 pkt/s > threshold 5000 pkt/s)
  • RSSI degradation on both phones
  • Throughput drop >50%
  ✓ Decision at t=20s: "JAMMER DETECTED"
```

### PHASE 4: CONTROLLER RESPONSE (22-30 seconds)
```
Controller chooses BOTH strategies:

Strategy 1: MAC ISOLATION (immediate)
  • Command to AP: blacklist_mac(aa:bb:cc:dd:ee:ff)
  • AP executes: hostapd_cli deny_acl add aa:bb:cc:dd:ee:ff
  • Result: Jammer cannot transmit
  • Effect: Throughput recovers to ~4 Mbps per phone

Strategy 2: CHANNEL SWITCH (after 2 seconds)
  • Command to AP: switch_channel(11)
  • AP executes: hostapd_cli set_channel 11
  • Phones auto-reconnect (if WiFi driver supports it)
  • Jammer still on Channel 6 (physically separated)
  • Result: Even cleaner throughput ~4.8 Mbps per phone

Timeline:
  t=20s: Jammer detected, isolation starts
  t=20.5s: MAC blacklisted, throughput partially recovers
  t=22s: Channel switch initiated
  t=23s: Phones reconnected to Channel 11
  t=24-30s: Stable high throughput on Channel 11
```

### PHASE 5: RECOVERY + PROOF (30-40 seconds)
```
Final metrics:
  ✓ Throughput: ~4.8-5 Mbps per phone (similar to baseline)
  ✓ Latency: <50ms
  ✓ RSSI: -50 to -55 dBm (better than attack phase)
  ✓ Channel: 11 (switched from 6)
  ✓ Jammer: Isolated (cannot transmit)

Proof visualization (Flask dashboard):
  • Real-time throughput graph: [9Mbps → 1Mbps → 9Mbps]
  • RSSI trend: [Good → Degraded → Good]
  • Channel history: [6 → 6 → 11]
  • Events log: "Jammer detected → MAC blacklisted → Channel switched"
```

---

## FILE STRUCTURE (New)

```
S4_IOT_MULTI_MACHINE/
│
├── config.json                          # Shared config (IPs, channels, thresholds)
│
├── controller_laptop/
│   ├── ryu_sdn_controller.py           # Ryu OpenFlow controller logic
│   ├── controller_server.py            # Main controller with socket server
│   ├── dashboard.py                    # Flask web dashboard
│   ├── jammer_detection_engine.py      # Detection algorithm
│   ├── templates/
│   │   └── dashboard.html              # Web UI (charts, real-time data)
│   └── static/
│       └── chart.js                    # Real-time graph rendering
│
├── ap_laptop/
│   ├── hostapd.conf                    # WiFi AP configuration (Channel 6)
│   ├── ap_agent.py                     # Reports AP metrics to controller
│   ├── channel_switch.py               # Execute channel switching commands
│   └── ap_setup.sh                     # Bootstrap script (install hostapd)
│
├── monitor_jammer_laptop/
│   ├── monitor_agent.py                # Sends metrics to controller
│   ├── jammer.py                       # UDP packet flood generator
│   ├── network_stats.py                # Collect local ping/throughput
│   └── monitor_setup.sh                # Bootstrap script
│
├── orchestrator.py                     # Master orchestrator (runs experiment phases)
├── client_control.py                   # Send iperf3 commands to phones (via adb)
│
├── results/
│   ├── sdn_testbed_metrics.json        # Final experiment metrics
│   ├── jammer_detection_log.json       # Controller decisions timeline
│   └── channel_history.log             # Channel switching timeline
│
└── ARCHITECTURE_DESIGN.md              # This document
```

---

## IMPLEMENTATION CHECKLIST

### PHASE 1: Core Communication (WiFi UDP messaging)
```
[ ] Create config.json with IPs/ports/thresholds
[ ] Implement UDP server on controller (listen for AP & Monitor metrics)
[ ] Implement UDP client on AP agent (send metrics every 2s)
[ ] Implement UDP client on Monitor agent (send metrics every 1s)
[ ] Test messaging between laptops
```

### PHASE 2: AP Control & Monitoring
```
[ ] Write AP agent to query hostapd for client list & RSSI
[ ] Implement channel switching command (hostapd_cli)
[ ] Implement MAC blacklisting command (hostapd_cli deny_acl)
[ ] Test both commands manually
```

### PHASE 3: Detection Algorithm
```
[ ] Implement packet rate detection (threshold: 5000 pkt/s)
[ ] Implement RSSI degradation detection (threshold: >15 dBm drop)
[ ] Implement throughput drop detection (threshold: >50% loss)
[ ] Combine into single jammer detection logic
[ ] Return confidence score + recommended action
```

### PHASE 4: Controller Decision Logic
```
[ ] When jammer detected: Execute MAC blacklist
[ ] Monitor recovery for 2 seconds
[ ] If still degraded: Execute channel switch
[ ] If recovered: Log success and continue monitoring
[ ] If failed: Attempt alternative channel
```

### PHASE 5: Dashboard (Flask)
```
[ ] Create real-time throughput graph (WebSocket updates)
[ ] Create RSSI trend display
[ ] Create channel history visualization
[ ] Create event log (detection, isolation, switch)
[ ] Create control panel (manual override buttons)
```

### PHASE 6: Orchestrator
```
[ ] Script Phase 1: Setup & startup
[ ] Script Phase 2: Baseline (10s measurement)
[ ] Script Phase 3: Jammer activation (10s)
[ ] Script Phase 4: Controller response (8s)
[ ] Script Phase 5: Recovery documentation (2-10s)
[ ] Export JSON results + screenshots
```

### PHASE 7: Testing & Validation
```
[ ] Run on all three laptops simultaneously
[ ] Verify metrics arrive at controller correctly
[ ] Verify jammer detection triggers
[ ] Verify MAC blacklist works
[ ] Verify channel switch works
[ ] Verify phones reconnect smoothly
[ ] Verify throughput recovery is measurable
[ ] Capture wireshark on AP during attack
[ ] Generate final report
```

---

## TECHNICAL DETAILS

### 1. AP Configuration (hostapd.conf)
```
# SDN-TestNet on 2.4 GHz Channel 6
interface=wlan0
driver=nl80211
ssid=SDN-TestNet
hw_mode=g
channel=6
wmm_enabled=1
auth_algs=1
wpa=0
```

### 2. Jammer Implementation
```python
# Pseudo-jammer: UDP flood
while jammer_active:
    packet = create_udp_packet(
        src_ip=my_ip,
        dst_ip="255.255.255.255",  # Broadcast
        payload_size=1500,
        packet_rate=8000  # pps
    )
    send_packet(packet)
```

### 3. Detection Algorithm (Pseudocode)
```python
def detect_jammer(ap_metrics, monitor_metrics):
    jammer_score = 0
    
    # Check 1: High packet rate
    if monitor_metrics.pkt_rate > 5000:
        jammer_score += 40
    
    # Check 2: RSSI degradation
    rssi_drop = baseline_rssi - current_rssi
    if rssi_drop > 15:
        jammer_score += 30
    
    # Check 3: Throughput loss
    throughput_loss = (baseline_tput - current_tput) / baseline_tput
    if throughput_loss > 0.5:
        jammer_score += 30
    
    # Decision
    if jammer_score > 60:
        return {"detected": True, "confidence": jammer_score, 
                "suspect_mac": monitor_metrics.my_mac}
    else:
        return {"detected": False}
```

### 4. Channel Switching Command
```python
def switch_channel(target_channel):
    os.system(f"hostapd_cli set_channel {target_channel}")
    # Verify
    current = get_current_channel()
    assert current == target_channel, "Channel switch failed"
```

### 5. MAC Isolation
```python
def blacklist_mac(mac_address):
    os.system(f"hostapd_cli deny_acl add {mac_address}")
    os.system("hostapd_cli reload_acl")
    # Jammer cannot authenticate now
```

---

## EXPECTED RESULTS (JSON Output)

```json
{
  "experiment_id": "MULTI_MACHINE_SDN_001",
  "duration_seconds": 40,
  "phases": {
    "baseline": {
      "duration": 10,
      "phone1_throughput_mbps": 4.5,
      "phone2_throughput_mbps": 4.6,
      "total_throughput_mbps": 9.1,
      "avg_latency_ms": 12.3,
      "avg_rssi_dbm": -55,
      "channel": 6
    },
    "jammer_active": {
      "duration": 10,
      "phone1_throughput_mbps": 0.8,
      "phone2_throughput_mbps": 0.9,
      "total_throughput_mbps": 1.7,
      "avg_latency_ms": 245,
      "avg_rssi_dbm": -72,
      "jammer_packet_rate_pps": 8500,
      "channel": 6
    },
    "recovery": {
      "duration": 20,
      "phone1_throughput_mbps": 4.7,
      "phone2_throughput_mbps": 4.8,
      "total_throughput_mbps": 9.5,
      "avg_latency_ms": 18.5,
      "avg_rssi_dbm": -52,
      "channel_after_switch": 11,
      "jammer_status": "isolated"
    }
  },
  "controller_actions": [
    {
      "timestamp": 20.0,
      "action": "jammer_detected",
      "confidence": 85.5,
      "suspect_mac": "aa:bb:cc:dd:ee:ff"
    },
    {
      "timestamp": 20.2,
      "action": "mac_blacklisted",
      "target_mac": "aa:bb:cc:dd:ee:ff",
      "result": "success"
    },
    {
      "timestamp": 22.5,
      "action": "channel_switch",
      "from_channel": 6,
      "to_channel": 11,
      "phones_reconnected": 2,
      "result": "success"
    }
  ],
  "performance_improvement": {
    "throughput_recovery_percent": 95.6,
    "latency_improvement_percent": 92.4,
    "rssi_improvement_dbm": 20
  }
}
```

---

## CRITICAL ASSUMPTIONS & CONSTRAINTS

### ✅ What We Assume Works
- All 3 laptops on same home WiFi (5GHz for inter-laptop comms)
- AP laptop can run `hostapd` to broadcast on 2.4 GHz Channel 6
- `hostapd_cli` commands available on AP laptop
- Phones have iperf3 app installed
- UDP communication between laptops is stable (<10ms latency)

### ⚠️ What Could Break
- Phones not auto-reconnecting after channel switch → need manual script
- Other WiFi networks on Channel 6 causing baseline interference
- AP WiFi chipset doesn't support channel switching on-the-fly
- Monitor laptop can't join AP's WiFi (DHCP fails) → pre-assign static IP

### 🔧 Workarounds
1. If phones don't auto-reconnect: Add Python script to trigger reconnect via ADB
2. If interference on Ch6: Start experiment at off-peak time or switch to Ch11/13
3. If hostapd_cli unavailable: Use direct hostapd socket communication
4. If DHCP fails: Pre-configure static IPs on Monitor laptop

---

## READY TO IMPLEMENT?

Once you confirm this architecture, I'll build:
1. ✅ Controller server + UDP listeners
2. ✅ AP agent + channel/MAC control
3. ✅ Monitor agent + jammer
4. ✅ Detection algorithm
5. ✅ Flask dashboard
6. ✅ Orchestrator script
7. ✅ Test suite

**Estimated code: ~2000 lines of Python**
**Estimated time to implement: 2-3 hours**
**Reproducible: Yes (fully automated)**

Sound good? Any adjustments before we code? 🚀

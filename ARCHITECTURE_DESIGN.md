# REFINED PROJECT ARCHITECTURE - MULTI-MACHINE SDN TESTBED

## ANALYSIS OF YOUR REQUIREMENTS

### Hardware Setup (3 Physical Laptops):
1. **Controller Laptop** — Runs Ryu SDN controller + monitoring dashboard
2. **AP Laptop** — Runs hostapd (WiFi AP) on 2.4 GHz Channel 6
3. **Monitor/Jammer Laptop** — Runs monitoring agent + pseudo-jammer

### Wireless Clients:
- **2 Android/iOS Phones** — Connect to AP WiFi, generate traffic via iperf3

---

## CRITICAL QUESTIONS & DESIGN DECISIONS

### ❓ Question 1: What does "multi system testing" mean here?
**Our Understanding:**
- Each laptop is a separate physical machine on different networks
- Communication happens via Ethernet (not WiFi)
- Controller laptop connects to AP laptop via Ethernet to manage it
- Monitor/Jammer laptop is isolated from WiFi but communicates with controller via Ethernet
- **Is this correct?**

### ❓ Question 2: How should the three laptops communicate?
**Option A (Recommended):**
```
[Phone 1] ──WiFi──┐
                  ├──→ [AP Laptop (hostapd)] ──Ethernet─→ [Controller Laptop]
[Phone 2] ──WiFi──┘                                        (Ryu OpenFlow)
                                                           + Dashboard
                                                           
[Monitor/Jammer Laptop] ──────Ethernet─────────→ [Controller Laptop]
(Sends UDP packets via WiFi to jam AP)
```

**Option B (More Complex - using OpenFlow switch):**
- Add an actual OpenFlow-compatible switch (OVS) to control WiFi AP behavior

**Which do you prefer?**

### ❓ Question 3: How should the jammer work?
**Proposed Approach:**
- Monitor/Jammer laptop connects to WiFi network FIRST as a client
- Then runs a packet generator (large UDP packets) to simulate jamming
- This creates **realistic interference** on the channel
- Controller detects jammer's MAC address via RSSI degradation + high packet rate
- **Is this what you meant by "legally"?** (i.e., not creating actual RF interference, just UDP traffic?)

### ❓ Question 4: What "real-time networking tools" data do you want?
**Proposed Metrics Collection:**
- **iperf3**: Throughput (Mbps) from phones to AP
- **ping**: Latency to controller (ms)
- **RSSI**: WiFi signal strength from phones (dBm)
- **Wireshark**: Packet capture on AP laptop to show jammer traffic
- **Channel utilization**: % bandwidth used
- **Is this the right set?**

### ❓ Question 5: How should channel switching work?
**Proposed Mechanism:**
```
1. Baseline: AP broadcasts on Channel 6
2. Controller monitors RSSI + throughput
3. When jammer detected:
   - Controller sends command to AP: "Switch to Channel 11"
   - AP uses `hostapd_cli set_channel 11`
   - Phones auto-reconnect (if configured)
   - Performance improves (less interference)
4. Monitor dashboard shows: "Channel 6 → Channel 11" + throughput graph
```

**Is this the expected behavior?**

### ❓ Question 6: What about isolation?
**Proposed Isolation Mechanism:**
When controller detects jammer (by MAC address):
```
Option A: Blacklist MAC on AP (hostapd_cli deny_acl)
  → Jammer cannot connect/authenticate
  
Option B: Rate limit via iptables (if jammer is already connected)
  → Jammer's packets get dropped/queued
  
Option C: Both A + B for robustness
```

**Which isolation strategy do you want?**

---

## PROPOSED SYSTEM FLOW

### PHASE 1: SETUP (One-time)
```
1. Configure static IPs on all three laptops
   - Controller: 192.168.1.100
   - AP: 192.168.1.101
   - Monitor: 192.168.1.102

2. Start AP laptop with hostapd
   - Creates WiFi SSID: "SDN-TestNet" on Channel 6
   - IP: 192.168.1.101

3. Connect phones to WiFi
   - Phone 1: Assigned 192.168.1.11 (via DHCP or static)
   - Phone 2: Assigned 192.168.1.12

4. Start Ryu controller on Controller laptop
   - Listens on 192.168.1.100:6633 (OpenFlow port)
   - Dashboard on port 8080

5. Monitor/Jammer laptop
   - Joins WiFi first (gets 192.168.1.103)
   - Registers with controller as "monitor_agent"
```

### PHASE 2: BASELINE (10 seconds)
```
1. Both phones start iperf3 server
   $ iperf3 -s  (on each phone)

2. Controller laptop runs iperf3 client
   $ iperf3 -c 192.168.1.11  (measure throughput to phone1)
   $ iperf3 -c 192.168.1.12  (measure throughput to phone2)

3. Monitor collects metrics:
   - Throughput: iperf3 output
   - Latency: ping to 8.8.8.8 (or controller IP)
   - RSSI: via `iw dev wlan0 link` on phones (sent to controller)
   - Channel: 6

4. Dashboard shows:
   - Real-time throughput graph (Channel 6)
   - RSSI trend
   - Ping latency
   - Active connections
```

### PHASE 3: JAMMER ACTIVE (10 seconds)
```
1. Monitor/Jammer laptop activates pseudo-jammer:
   $ python3 jammer.py --target-channel 6 --packet-rate 10000pps

2. This sends large UDP packets (fake jamming traffic)
   - ARP to broadcast
   - Causes channel congestion
   - Phones can't send iperf3 traffic efficiently

3. Effects observed:
   - Throughput drops (iperf3 shows <0.5 Mbps)
   - RSSI degrades (jammer nearby)
   - Ping latency increases (>1000ms)
   - Wireshark shows jammer MAC flooding the channel

4. Controller detects jammer:
   - High packet rate from monitor MAC (>5000pps)
   - Degradation in phone throughput
   - RSSI from phones decreased
   - **Decision: "Jammer detected on Channel 6"**
```

### PHASE 4: ISOLATION (2 seconds)
```
1. Controller blacklists jammer MAC on AP:
   $ hostapd_cli deny_acl add <jammer-mac>
   $ hostapd_cli reload_acl

2. Result:
   - Jammer cannot transmit (MAC blocked at AP)
   - Phones' packets get through again
   - Dashboard shows: "Jammer isolated"
   
3. Alternatively: Controller switches channel to escape interference
```

### PHASE 5: RECOVERY + CHANNEL SWITCH (10 seconds)
```
1. Option A: Just isolate jammer
   - Jammer stays blacklisted
   - Throughput recovers on Channel 6
   - Performance: ~4.5-5 Mbps

2. Option B: Switch to different channel
   - Controller sends: "Switch to Channel 11"
   - AP changes: hostapd_cli set_channel 11
   - Phones reconnect automatically
   - Jammer still on Channel 6 (separated)
   - Throughput: ~4.8-5 Mbps (clean channel)

3. Dashboard animation:
   - Throughput graph: Shows dip, then recovery
   - Channel display: "6 → 11" (if switching)
   - Jammer status: "Isolated" or "Escaped"
```

---

## SOFTWARE ARCHITECTURE

### Directory Structure
```
S4_IOT_MULTI_MACHINE/
├── controller/
│   ├── ryu_sdn_controller.py      # OpenFlow controller (Ryu)
│   ├── dashboard.py               # Web dashboard (Flask)
│   ├── metrics_collector.py        # Listens for metrics from AP/Monitor
│   └── detection_engine.py         # Jammer detection logic
│
├── ap_laptop/
│   ├── ap_setup.sh                # Bash: Configure hostapd
│   ├── hostapd.conf               # WiFi AP config (Channel 6)
│   ├── ap_agent.py                # Reports RSSI/metrics to controller
│   └── channel_switch.py           # Commands to switch channels
│
├── monitor_jammer_laptop/
│   ├── monitor_agent.py            # Sends network metrics to controller
│   ├── jammer.py                   # Pseudo-jammer (UDP flood)
│   ├── network_metrics.py          # Collect ping/throughput locally
│   └── iperf3_client.py            # Send traffic for measurement
│
├── phones/
│   ├── iperf3_server.apk          # (Install via Play Store)
│   └── connectivity_test.apk       # (Custom app to report RSSI)
│
├── orchestrator.py                 # Master script: runs all phases
├── config.json                     # IP addresses, channels, timeouts
└── results/
    ├── sdn_testbed_results.json    # Final metrics
    └── wireshark_capture.pcap      # Traffic capture
```

---

## PROPOSED TECHNOLOGY STACK

### Controller Laptop (Linux):
- **Ryu** — OpenFlow controller
- **Flask** — Web dashboard for real-time visualization
- **iperf3** — Traffic generation/measurement
- **hostapd** — WiFi AP management (if controller also acts as AP)
- **iw** — WiFi commands (set_channel, etc.)

### AP Laptop (Linux):
- **hostapd** — WiFi Access Point software
- **Python agent** — Send metrics to controller
- **Wireshark** — Optional traffic capture

### Monitor/Jammer Laptop (Linux):
- **Python** — Jammer traffic generator
- **iperf3** — Traffic measurement
- **ping** — Latency monitoring
- **hostapd_cli** — If it controls AP remotely

### Phones (Android/iOS):
- **iperf3** app (from Play Store)
- **Ping app** (built-in or app)
- **Wireshark/tcpdump** (if available)

---

## QUESTIONS BEFORE IMPLEMENTATION

Please clarify:

1. **Hardware Networking:**
   - Will the 3 laptops be on the same Ethernet network?
   - Can the AP laptop broadcast WiFi independently (using hostapd)?
   - Or do you want to use an actual WiFi router + add OpenFlow switch?

2. **WiFi Phones:**
   - Will phones have iperf3 app installed?
   - Can phones report their own RSSI to controller (custom app or just ping)?
   - Do phones need to show metrics on screen or just send them to controller?

3. **Jammer Behavior:**
   - Should jammer be a connected WiFi client (more realistic)?
   - Or send packets from outside the network (less realistic but easier)?
   - What if jammer gets isolated — should it try to reconnect or stay blocked?

4. **Controller Intelligence:**
   - Should controller ALWAYS switch channels when jammer detected?
   - Or should it try isolation first, then switch if that fails?
   - How should it decide which channel is "safe" (measure interference first)?

5. **Real-time Display:**
   - Should dashboard be web-based (browser on controller laptop)?
   - Or command-line graphs (matplotlib)?
   - Do you want Wireshark packet capture running side-by-side?

6. **Performance Metrics:**
   - What throughput should we expect per phone? (depends on WiFi chipset)
   - What RSSI threshold indicates "jammer nearby"?
   - How many packets per second = "jammer behavior"?

---

## RECOMMENDED FLOW (Our Proposal)

**Start here, then refine:**

```
SETUP:
  1. Configure hostapd on AP laptop (Channel 6)
  2. Start Ryu controller on Controller laptop
  3. Phones join WiFi + start iperf3 server
  4. Monitor agent registers with controller

BASELINE (10s):
  - iperf3 measure: phones → controller
  - Throughput: ~4-5 Mbps per phone
  - RSSI: -50 to -60 dBm (good signal)
  - Latency: <50ms

JAMMER ACTIVE (10s):
  - Monitor sends UDP flood on Channel 6
  - Throughput drops to <0.5 Mbps
  - RSSI degrades to -75 dBm
  - Latency spikes to >500ms

CONTROLLER RESPONSE:
  Option A: Blacklist jammer MAC → throughput recovers to 4.5 Mbps
  Option B: Switch to Channel 11 → throughput recovers to 4.8 Mbps

PROOF:
  - JSON export: before/after metrics
  - Real-time dashboard: graph animation
  - Wireshark: visible MAC blocking or channel change
```

---

## WHAT WE NEED FROM YOU

1. **Hardware confirmation:**
   - Can AP laptop run `hostapd` to broadcast WiFi?
   - Are all 3 laptops on same Ethernet network?
   - Do phones have iperf3 app?

2. **Clarify jammer:**
   - Is "pseudo jammer" = UDP flood OR simulated RF interference?

3. **Priority features:**
   - Most important: Channel switching OR MAC isolation?
   - Real-time dashboard (web/CLI)?
   - Wireshark integration?

4. **Time constraints:**
   - How long should entire test run? (30s? 60s?)
   - How many phases? (we suggested 5, can be fewer)

---

## NEXT STEPS

Once you clarify above, we will:

1. ✅ Design exact message protocol (AP → Controller, Monitor → Controller)
2. ✅ Implement channel-switch command
3. ✅ Create jammer detection algorithm (packet rate + RSSI)
4. ✅ Build MAC isolation mechanism
5. ✅ Design real-time dashboard
6. ✅ Write orchestrator to run full experiment
7. ✅ Generate quantifiable results

**This will be REAL, REPRODUCIBLE, and IMPRESSIVE for faculty!**

---

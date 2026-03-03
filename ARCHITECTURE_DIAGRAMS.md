# SDN Single-Laptop Architecture - Visual Diagrams

## 1. Network Topology Diagram

```
╔════════════════════════════════════════════════════════════════════════════╗
║                         SRIRAM'S LAPTOP (THINKPAD)                        ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐ ║
║  │ Physical Layer                                                        │ ║
║  │                                                                        │ ║
║  │  [WiFi Card wlo1]                   [WiFi Card wlan0]               │ ║
║  │  (Home WiFi connected)              (AP mode, hostapd)              │ ║
║  │  Connected to: home router          Broadcasts: SDN-TestNet         │ ║
║  └──────────────────────────────────────────────────────────────────────┘ ║
║           ↓                                    ↓                          ║
║           │                                    │                          ║
║           ↓                                    ↓                          ║
║  ┌──────────────────────────────────────────────────────────────────────┐ ║
║  │ IP Layer                                                              │ ║
║  │                                                                        │ ║
║  │  Interface: wlo1                     Interface: ap0 (virtual)        │ ║
║  │  IP: 10.12.188.184                   IP: 192.168.88.1              │ ║
║  │  Netmask: 255.255.240.0              Netmask: 255.255.255.0        │ ║
║  │  Subnet: 10.12.176.0/20              Subnet: 192.168.88.0/24       │ ║
║  │  Gateway: home router                Gateway: self (192.168.88.1)   │ ║
║  │  Purpose: Home network               Purpose: AP network             │ ║
║  │                                                                        │ ║
║  │  ← UPLINK →                          ← ISOLATED AP →                │ ║
║  └──────────────────────────────────────────────────────────────────────┘ ║
║           ↓                                    ↓                          ║
║           │                                    │                          ║
║           │ (Optional NAT)                     │ (WiFi Broadcast)       ║
║           │                                    │                          ║
║           ↓                                    ↓                          ║
║  ┌──────────────────────────────────────────────────────────────────────┐ ║
║  │ Application Layer (Agents)                                            │ ║
║  │                                                                        │ ║
║  │ ┌──────────────────┬──────────────────┬──────────────────────────┐   │ ║
║  │ │ SDN Controller   │ hostapd + dnsmasq │ Monitor Agent         │   │ ║
║  │ │ Port 9000        │ Port 53 (DNS)    │ Port 9001             │   │ ║
║  │ │                  │ Port 67 (DHCP)   │                       │   │ ║
║  │ │ Listens on:      │ Listens on:      │ Listens on:           │   │ ║
║  │ │ 192.168.88.1     │ 192.168.88.1     │ 192.168.88.1          │   │ ║
║  │ │                  │                  │                       │   │ ║
║  │ │ Responsibilities:│ Responsibilities:│ Responsibilities:     │   │ ║
║  │ │ • Detect jammer │ • Manage AP      │ • Measure throughput │   │ ║
║  │ │ • Score metrics │ • Assign IPs     │ • Generate jammer    │   │ ║
║  │ │ • Send commands │ • Execute cmds   │ • Report metrics     │   │ ║
║  │ │                  │                  │                       │   │ ║
║  │ └──────────────────┴──────────────────┴──────────────────────────┘   │ ║
║  │                                                                        │ ║
║  └──────────────────────────────────────────────────────────────────────┘ ║
║           │                                    ↓                          ║
║           │                                    │                          ║
║           │                             WiFi Broadcast                  ║
║           │                           "SDN-TestNet" (Ch 6)              ║
║           │                                    │                          ║
║           └────────────────────────┬──────────┘                          ║
║                                    │                                      ║
║  ┌────────────────────────────────┴────────────────────────────────────┐ ║
║  │ Wireless Clients (Outside Laptop)                                   │ ║
║  │                                                                      │ ║
║  │  [Phone 1]                              [Phone 2]                   │ ║
║  │  IP: 192.168.88.10+                    IP: 192.168.88.11+         │ ║
║  │  (Auto-assigned by dnsmasq)            (Auto-assigned by dnsmasq) │ ║
║  │  Running: iperf3 server                Running: iperf3 server     │ ║
║  │  Port: 5201                             Port: 5201                 │ ║
║  │                                                                      │ ║
║  └────────────────────────────────────────────────────────────────────┘ ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

IP RANGES SUMMARY:
═══════════════════════════════════════════════════════════════════════════

Uplink (Home WiFi):
    Range: 10.12.176.0 - 10.12.191.255  (/20)
    Your IP: 10.12.188.184
    Gateway: Home router (auto-detected)
    DNS: Home router's DNS (auto-detected)

AP Network (Isolated):
    Range: 192.168.88.0 - 192.168.88.255  (/24)
    Gateway: 192.168.88.1 (your laptop)
    DHCP Pool: 192.168.88.10 - 192.168.88.200
    Broadcast: 192.168.88.255

Agent Binding:
    Controller: 192.168.88.1:9000
    Monitor: 192.168.88.1:9001
    DHCP: 192.168.88.1:67
    DNS: 192.168.88.1:53

Phone IPs (Examples):
    Phone 1: 192.168.88.10 (first device)
    Phone 2: 192.168.88.11 (second device)
```

---

## 2. Agent Communication Diagram

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    AGENT COMMUNICATION FLOW                               ║
╚════════════════════════════════════════════════════════════════════════════╝

Legend:
    → TCP/UDP communication
    ⇒ High-frequency (every 1-2s)
    ⤳ On-demand / Event-driven


1. METRICS REPORTING (Every 2 seconds)
═══════════════════════════════════════════════════════════════════════════

    Monitor Agent                  Controller
    (192.168.88.1:9001)            (192.168.88.1:9000)
           │                               ▲
           │                               │
           └──────────── UDP ────────────→ │
              (metrics)
              - throughput (Mbps)
              - latency (ms)
              - RSSI (dBm)
              - packet_rate (pps)
              - jammer_active (bool)

    Hostapd (daemon)               Controller
    (ap0 interface)                (192.168.88.1:9000)
           │                               ▲
           │                               │
           └─────── hostapd_cli ─────────→ │
              (poll for metrics)
              - connected clients
              - RSSI per client
              - channel utilization


2. COMMAND FLOW (On-demand, during response)
═══════════════════════════════════════════════════════════════════════════

    Controller                     Hostapd
    (192.168.88.1:9000)            (daemon)
           │                           ▲
           │                           │
           └────── hostapd_cli ──────→ │
              command: "deny_acl add [jammer_mac]"
              
    ~2 seconds delay...

    Controller                     Hostapd
    (192.168.88.1:9000)            (daemon)
           │                           ▲
           │                           │
           └────── hostapd_cli ──────→ │
              command: "set_channel 11"


3. JAMMER TRAFFIC FLOW (When jammer is active)
═══════════════════════════════════════════════════════════════════════════

    Monitor Agent                  WiFi Broadcast
    (192.168.88.1)                 (192.168.88.255:12345)
           │                                ▲
           │                                │
           └────── UDP Flood ──────────────→ │
              - 8000 pps
              - 1500 bytes each
              - Broadcast to all clients

    Phones connected to AP will experience:
    - Interference on Channel 6
    - Degraded throughput
    - Increased latency
    - Lower RSSI


4. ORCHESTRATOR FLOW (Master control, sequential)
═══════════════════════════════════════════════════════════════════════════

    Orchestrator                   All Agents
    (orchestrator.py)              (controller.py, monitor.py, etc)
           │
           ├─→ [Phase 1] Start agents ────────→ (startup)
           │                                    ▲
           │                                    │
           ├─→ [Phase 2] Baseline (10s) ───→ (collect metrics)
           │                                    │
           ├─→ [Phase 3] Jammer Active (10s) → (UDP flood)
           │                                    │
           ├─→ [Phase 4] Detection ────────→ (score metrics)
           │                                    │
           ├─→ [Phase 5] Response ────────→ (MAC blacklist + channel switch)
           │                                    │
           ├─→ [Phase 6] Recovery (14s) ──→ (measure recovery)
           │                                    │
           └─→ [Done] Export results ──────→ (sdn_testbed_metrics.json)
```

---

## 3. Data Flow During Jammer Attack

```
NORMAL OPERATION (Phase 2: Baseline)
═══════════════════════════════════════════════════════════════════════════

    Controller          Monitor         Phone1          Hostapd
       │                 │              │               │
       │                 │←─ iperf3 ──→ │ (9.0 Mbps)   │
       │                 │              │               │
       │← metrics ──────  │              │               │
       │  (clean)         │              │               │
       │                 │←─ ping ──────→ 8.8.8.8       │
       │                 │  (15 ms)      │               │
       │                 │              │               │
       │← RSSI metrics ──────────────────────────────→  │
       │  (-55 dBm)      │              │               │
       │                 │              │               │
       │← packet rate ──  │              │               │
       │  (1000 pps)      │              │               │
       │                 │              │               │


JAMMER ACTIVE (Phase 3: Jammer)
═══════════════════════════════════════════════════════════════════════════

    Controller          Monitor         Phone1          Hostapd
       │                 │              │               │
       │                 │              │               │
       │     [UDP Flood starts]         │               │
       │                 │→ broadcast ──→ (interference)│
       │                 │→ broadcast ──→ (interference)│
       │                 │→ broadcast ──→ (interference)│
       │                 │  ... 8000 pps total         │
       │                 │              │               │
       │                 │←─ iperf3 ──→ │ (1.5 Mbps)   │
       │                 │  (degraded)   │               │
       │← metrics ──────  │              │               │
       │  (poor)          │              │               │
       │                 │←─ ping ──────→ 8.8.8.8       │
       │                 │  (250 ms!)    │               │
       │                 │              │               │
       │← RSSI metrics ──────────────────────────────→  │
       │  (-72 dBm)       │              │               │ [DETECTION]
       │  [BAD!]          │              │               │ Confidence ≥ 60
       │                 │              │               │
       │← packet rate ──  │              │               │
       │  (8000 pps!)     │              │               │
       │  [ANOMALY!]      │              │               │


RESPONSE (Phase 5: MAC Blacklist + Channel Switch)
═══════════════════════════════════════════════════════════════════════════

    [t=20.0s] Detection triggered (confidence = 100)

    Controller                        Hostapd
       │                              │
       │─→ hostapd_cli deny_acl ─────→ │
       │   "add [jammer_mac]"          │ (immediate)
       │                              ↓
       │                    [MAC Blacklisted]
       │
       │ ... wait 2 seconds for TCP session cleanup ...
       │
    [t=22.0s] Channel switch triggered

       │─→ hostapd_cli set_channel ───→ │
       │   "11"                         │ (switched!)
       │                              ↓
       │                    [Channel 6 → 11]


RECOVERY (Phase 6: Measuring Recovery)
═══════════════════════════════════════════════════════════════════════════

    Controller          Monitor         Phone1          Hostapd
       │                 │              │               │
       │  [Jammer still sending, but blocked/no effect] │
       │                 │              │               │
       │                 │←─ iperf3 ──→ │ (recovering)  │
       │                 │  (getting better)             │
       │← metrics ──────  │              │               │
       │  (improving)     │              │               │
       │                 │←─ ping ──────→ 8.8.8.8       │
       │                 │  (faster)     │               │
       │                 │              │               │
       │← RSSI metrics ──────────────────────────────→  │
       │  (-52 dBm)       │              │               │
       │  [RECOVERED]     │              │               │
       │                 │              │               │
       │← packet rate ──  │              │               │
       │  (normal)        │              │               │
       │                 │              │               │

    [t=23-40s] Network fully recovered: 9.5 Mbps throughput
```

---

## 4. Configuration Structure Diagram

```
config.json (Hierarchical Structure)
═════════════════════════════════════════════════════════════════════════

{
  "system" ─┐
            ├─ deployment_mode: "single_laptop_multi_role"
            ├─ description: "..."
            ├─ demo_optimized: true
            └─ stability_focus: true

  "network" ─┐
             ├─ "uplink" ─┐
             │            ├─ interface: "wlo1"
             │            ├─ ip_address: "10.12.188.184"
             │            ├─ netmask: "255.255.240.0"
             │            ├─ subnet_cidr: "10.12.176.0/20"
             │            └─ gateway_auto: true
             │
             ├─ "ap" ────┐
             │           ├─ interface: "ap0"
             │           ├─ ssid: "SDN-TestNet"
             │           ├─ channel: 6
             │           ├─ ip_address: "192.168.88.1"
             │           └─ subnet_cidr: "192.168.88.0/24"
             │
             ├─ "dhcp" ──┐
             │           ├─ server_interface: "ap0"
             │           ├─ dhcp_range_start: "192.168.88.10"
             │           ├─ dhcp_range_end: "192.168.88.200"
             │           └─ tool: "dnsmasq"
             │
             ├─ "nat" ───┐
             │           ├─ enabled: true
             │           ├─ source_interface: "ap0"
             │           ├─ dest_interface: "wlo1"
             │           └─ masquerade_rule: "MASQUERADE"
             │
             ├─ "controller" ┐
             │               ├─ ip_address: "192.168.88.1"
             │               ├─ port: 9000
             │               └─ bind_interface: "ap0"
             │
             └─ "monitor" ──┐
                            ├─ ip_address: "192.168.88.1"
                            ├─ port: 9001
                            └─ bind_interface: "ap0"

  "phones" ──┐
             ├─ phone_count: 2
             ├─ ip_pool: "192.168.88.10-200"
             ├─ "phone_1" ┐
             │            └─ role: "iperf3_server"
             └─ "phone_2" ┐
                          └─ role: "optional_secondary"

  "experiment" ─┐
                ├─ duration_sec: 40
                └─ "phases" ┐
                             ├─ phase_1_setup
                             ├─ phase_2_baseline
                             ├─ phase_3_jammer_active
                             ├─ phase_4_detection
                             ├─ phase_5_response
                             └─ phase_6_recovery

  "jammer" ──┐
             ├─ mode: "pseudo_jammer_udp"
             ├─ enabled: true
             ├─ target_broadcast: "192.168.88.255"
             ├─ packet_rate_pps: 8000
             └─ packet_size_bytes: 1500

  "detection" ┐
              ├─ algorithm: "multi_factor_confidence_scoring"
              ├─ "factors" ┐
              │            ├─ packet_rate (>5000 pps)
              │            ├─ rssi_degradation (>15 dBm)
              │            └─ throughput_loss (>50%)
              └─ confidence_threshold: 60

  "response" ┐
             └─ "actions" ┐
                          ├─ [0] MAC_BLACKLIST (t+0s)
                          └─ [1] CHANNEL_SWITCH (t+2s)

  "metrics_collection" ┐
                      └─ "sources" ┐
                                   ├─ ap_metrics (iw)
                                   ├─ throughput (iperf3)
                                   ├─ latency (ping)
                                   └─ packet_rate (netstat)

  "deprecated_fields_removed" ─→ [documentation]

  "architecture_notes" ────────→ [5 logical roles]
}
```

---

## 5. Experiment Timeline Diagram

```
EXPERIMENT TIMELINE (40 SECONDS TOTAL)
═══════════════════════════════════════════════════════════════════════════

Time     Phase                Metrics                    Actions
─────────────────────────────────────────────────────────────────────────

0s       ┌─────────────────┐
         │ Phase 1: Setup  │
         │ (2 seconds)     │
         │ Start agents    │  Controller: starting
2s       │ Establish AP    │  AP: online
         │ DHCP active     │  Monitor: ready
         └─────────────────┘  Phones: connected
         
         ┌─────────────────────────────────────────┐
         │ Phase 2: Baseline Measurement           │
2s       │ (10 seconds - Clean Network)            │
         │                                         │
12s      │ Throughput: 9.0 Mbps ──────────────┐  │
         │ Latency: 15 ms ─────────────────┐  │  │
         │ RSSI: -55 dBm ──────────────┐  │  │  │
         │ Packet Rate: ~1000 pps      │  │  │  │
         │                              │  │  │  │
         └──────────────────────────────┼──┼──┼──┘
                                        │  │  │
                                        ▼  ▼  ▼
         ┌─────────────────────────────────────────┐
         │ Phase 3: Jammer Active                  │
12s      │ (10 seconds - UDP Flood)                │
         │ [Monitor generates packet flood]        │
         │                                         │
         │ Throughput: 1.5 Mbps (83% loss!) ──┐  │
22s      │ Latency: 250 ms (16x worse!) ────┐ │  │
         │ RSSI: -72 dBm (17 dBm drop) ──┐  │ │  │
         │ Packet Rate: 8000 pps (HIGH!) │  │ │  │
         │                                │  │ │  │
         │                            [POOR METRICS!]
         └────────────────────────────────────────┘
                                        
20s      ┌─────────────────────────────────────────┐
         │ [DETECTION TRIGGERED]                   │
         │ Confidence Score = 100 points (>60!)    │
         │ Jammer Status: DETECTED ✓               │
         └─────────────────────────────────────────┘

         ┌─────────────────────────────────────────┐
20s      │ Phase 5: Response                       │
         │ [t=20.0s] MAC Blacklist (immediate)     │
         │ [t=22.0s] Channel Switch (2s delay)     │
23s      │                                         │
         │ hostapd_cli deny_acl add [jammer_mac]  │
         │ hostapd_cli set_channel 11              │
         └─────────────────────────────────────────┘

         ┌─────────────────────────────────────────┐
23s      │ Phase 6: Recovery Measurement           │
         │ (17 seconds - Network Recovering)       │
         │                                         │
         │ Throughput: 9.5 Mbps ──────────────┐   │
40s      │ Latency: 18 ms ───────────────┐  │   │
         │ RSSI: -52 dBm ─────────────┐  │  │   │
         │ Packet Rate: ~1000 pps      │  │  │   │
         │                              │  │  │   │
         │ [NETWORK FULLY RECOVERED!]  │  │  │   │
         └──────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════

PERFORMANCE COMPARISON:
═══════════════════════════════════════════════════════════════════════════

Throughput:
  9.0 Mbps ─────────────┐
           │             │ Baseline
  8.0 ────┤             │
  7.0 ────┤             │
  6.0 ────┤             │
  5.0 ────┤             │
  4.0 ────┤    ┌────────┼───────┐
  3.0 ────┤    │        │       │ Recovery
  2.0 ────┤    │ Attack │   ┌───┘
  1.5 Mbps┼────┘        │   │
  0.5 ────┤             └───┘
          └─────────────────────────
          0s    12s    22s    40s
          
Recovery Gain: 1.5 → 9.5 Mbps = 533% improvement ✓

Latency:
  250 ms ──────────────┐
        │             │ Attack
  200 ──┤             │
  150 ──┤    ┌────────┤
  100 ──┤    │        │ Recovery
   50 ──┤    │   ┌────┴──┐
   15 ms┼─┐  │   │       │
        └─┘──┘   └───────┘
        0s 12s  22s    40s
        
Recovery: 250 ms → 18 ms = 92% faster ✓

RSSI Signal Strength:
 -50 dBm ────────────┐
        │           │ Baseline (good)
 -55 ───┤─┐          │
 -60 ───┤ │   ┌─────┐
 -65 ───┤ │   │     │ Attack (poor)
 -70 ───┤ │   │  ┌──┘ Recovery
 -72 dBm┤ └───┘  │
        └─────────┘
        0s  12s 22s 40s
        
Recovery: -72 → -52 dBm = +20 dBm improvement ✓
```

---

## 6. Detection Algorithm Diagram

```
MULTI-FACTOR JAMMER DETECTION
═══════════════════════════════════════════════════════════════════════════

Input: Real-time network metrics

┌─────────────────┐
│ Monitor Agent   │ (reports every 2 seconds)
│                 │
│ • Packet Rate   │
│ • RSSI          │
│ • Throughput    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ CONFIDENCE SCORING ALGORITHM                                │
│                                                             │
│ Factor 1: Packet Rate Anomaly                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ IF packet_rate > 5000 pps:  +40 confidence points   │   │
│ │ ELSE:                       0 points                 │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ Factor 2: RSSI Degradation                                │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ IF RSSI_drop > 15 dBm:      +30 confidence points   │   │
│ │ ELSE:                       0 points                 │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ Factor 3: Throughput Loss                                 │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ IF throughput_loss > 50%:   +30 confidence points   │   │
│ │ ELSE:                       0 points                 │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ Total Confidence Score = Factor1 + Factor2 + Factor3      │
│ (Maximum: 100 points)                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ DECISION LOGIC                                              │
│                                                             │
│ IF confidence_score >= 60:                                  │
│     JAMMER DETECTED ✓                                       │
│     Trigger Response Actions                               │
│ ELSE:                                                       │
│     No jammer, continue monitoring                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ RESPONSE ACTIONS                                            │
│                                                             │
│ Action 1 (Immediate):                                       │
│  • MAC Blacklist: hostapd_cli deny_acl add [jammer_mac]    │
│  • Effect: Blocks jammer traffic                           │
│                                                             │
│ Action 2 (Delayed 2 seconds):                              │
│  • Channel Switch: hostapd_cli set_channel 11              │
│  • Effect: Escapes interference                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
   [NETWORK RECOVERED]


EXAMPLE CONFIDENCE CALCULATION:
═══════════════════════════════════════════════════════════════════════════

During Attack (Phase 3):
    Packet Rate: 8000 pps        → Factor 1: +40 (> 5000)
    RSSI Drop: 17 dBm            → Factor 2: +30 (> 15)
    Throughput Loss: 83%         → Factor 3: +30 (> 50%)
    ─────────────────────────────────────────────────
    TOTAL: 40 + 30 + 30 = 100 confidence points

Result: 100 >= 60 ✓
Status: JAMMER DETECTED with 100% confidence
Action: Trigger response (MAC blacklist + channel switch)


BEFORE & AFTER ATTACK:
═══════════════════════════════════════════════════════════════════════════

BASELINE (Clean Network):
    Packet Rate: 1000 pps        → Factor 1: 0 (< 5000)
    RSSI: -55 dBm                → Factor 2: 0 (< 15 dBm drop)
    Throughput: 9.0 Mbps         → Factor 3: 0 (no loss)
    ─────────────────────────────────────────────────────
    TOTAL: 0 + 0 + 0 = 0 confidence points
    
Result: 0 < 60
Status: No jammer detected (correct)


AFTER RECOVERY (Channel Switched):
    Packet Rate: 1000 pps        → Factor 1: 0 (< 5000)
    RSSI: -52 dBm                → Factor 2: 0 (recovered)
    Throughput: 9.5 Mbps         → Factor 3: 0 (recovered)
    ─────────────────────────────────────────────────────
    TOTAL: 0 + 0 + 0 = 0 confidence points
    
Result: 0 < 60
Status: No jammer detected (correct, jammer now ineffective)
```

---

## 7. Code Structure Diagram

```
PROJECT FILE ORGANIZATION
═══════════════════════════════════════════════════════════════════════════

/home/sriram/Desktop/S4_IOT/
│
├── multi_machine/                           ← MAIN PROJECT DIR
│   │
│   ├── config.json                          ← ✅ REFACTORED
│   │   └─ Single-laptop config, 10.12.x.x validation
│   │
│   ├── controller_server.py                 ← ⏳ NEEDS UPDATE
│   │   ├─ Class: ControllerServer
│   │   ├─ Class: JammerDetectionEngine
│   │   └─ Function: config['network']['controller']['ip_address']
│   │
│   ├── ap_agent.py                          ← ⏳ NEEDS UPDATE
│   │   ├─ Class: APAgent
│   │   └─ Function: config['network']['ap']['interface']
│   │
│   ├── monitor_agent.py                     ← ⏳ NEEDS UPDATE
│   │   ├─ Class: MonitorAgent
│   │   ├─ Function: activate_jammer()
│   │   └─ Function: config['network']['ap']['ip_address']
│   │
│   ├── orchestrator.py                      ← ⏳ NEEDS UPDATE
│   │   ├─ Class: Orchestrator
│   │   ├─ Function: phase_1_setup()
│   │   ├─ Function: phase_2_baseline()
│   │   ├─ Function: phase_3_jammer()
│   │   └─ Function: config['network']['dhcp']['dhcp_range_start']
│   │
│   ├── dashboard.py                         ← ⏳ NEEDS UPDATE
│   │   ├─ Class: DashboardServer
│   │   └─ Function: config['network']['controller']['port']
│   │
│   └── [Original docs: README.md, etc.]    ← Reference only
│
├── REFACTOR_SINGLE_LAPTOP.md                ← ✅ NEW (detailed guide)
├── SINGLE_LAPTOP_QUICK_REF.md               ← ✅ NEW (cheat sheet)
├── REFACTOR_SUMMARY.md                      ← ✅ NEW (this summary)
├── ARCHITECTURE_DIAGRAMS.md                 ← ✅ NEW (visuals)
│
└── [Original files: controller.py, etc.]    ← Legacy code

REFACTORING CHECKLIST:
═══════════════════════════════════════════════════════════════════════════

Agent Code Updates (5 files):
  ☐ controller_server.py
    - OLD: config['network']['controller_ip_home']
    - NEW: config['network']['controller']['ip_address']
  
  ☐ ap_agent.py
    - OLD: config['network']['ap_ip_home']
    - NEW: config['network']['ap']['ip_address']
  
  ☐ monitor_agent.py
    - OLD: config['network']['monitor_ip_home']
    - NEW: config['network']['monitor']['ip_address']
  
  ☐ orchestrator.py
    - OLD: config['deployment']['multi_machine']
    - NEW: config['system']['deployment_mode']
  
  ☐ dashboard.py
    - OLD: config['network']['controller_ip_home']
    - NEW: config['network']['controller']['ip_address']
```

---

## Summary

This complete visual documentation provides:

1. **Network Topology** - Physical and logical layout of all components
2. **Agent Communication** - How agents talk to each other
3. **Data Flow During Attack** - Step-by-step what happens during jammer
4. **Configuration Structure** - Hierarchical organization of config.json
5. **Experiment Timeline** - 40-second experiment breakdown with metrics
6. **Detection Algorithm** - Multi-factor confidence scoring explained
7. **Code Structure** - Files that need updating and how

All diagrams use ASCII art for compatibility and clarity.

**Next Step:** Use these diagrams when explaining the system to faculty!

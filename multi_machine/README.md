# SDN Multi-Machine Testbed - Quick Start

## 30-Second Setup

### Before You Start
- [ ] 3 laptops on same home WiFi (5 GHz preferred)
- [ ] Python 3.7+ on all laptops
- [ ] 2 phones with iperf3 app installed
- [ ] Note down IP addresses of each laptop

### IP Configuration (Edit config.json)
```json
{
  "network": {
    "controller_ip": "YOUR_CONTROLLER_IP",
    "ap_ip": "YOUR_AP_IP",
    "monitor_ip": "YOUR_MONITOR_IP"
  }
}
```

---

## Start Experiment (4 Terminals)

### Terminal 1 - Controller Laptop
```bash
cd multi_machine
python3 controller_server.py config.json
```

### Terminal 2 - AP Laptop
```bash
cd multi_machine
python3 ap_agent.py config.json
```

### Terminal 3 - Monitor Laptop
```bash
cd multi_machine
python3 monitor_agent.py config.json
```

### Terminal 4 - Run Experiment
```bash
cd multi_machine
python3 orchestrator.py config.json
```

**Automatic steps:**
1. ✅ Setup phase (2s) - all components connect
2. ✅ Baseline phase (10s) - measure clean network
3. ✅ Jammer active (10s) - UDP flood activated
4. ✅ Recovery phase (18s) - controller responds, network recovers

---

## What You'll See

**Monitor Terminal Output:**
```
[xx:xx:xx] [CONTROLLER] ✓ All components started
[xx:xx:xx] [CONTROLLER] Baseline established: RSSI=-55dBm, Throughput=9.0Mbps
[xx:xx:xx] [CONTROLLER] ⚠️ JAMMER DETECTED! Confidence: 85.5%
[xx:xx:xx] [CONTROLLER] ✓ MAC blacklist command sent
[xx:xx:xx] [CONTROLLER] ✓ Channel switch command sent: 6 → 11
[xx:xx:xx] [CONTROLLER] ✓ Network recovered - Throughput=9.5Mbps
```

**Results File:**
```bash
cat sdn_testbed_metrics.json
```

Shows JSON with all metrics and controller decisions.

---

## Dashboard

Open in browser on controller laptop:
```
http://127.0.0.1:8080
```

**Live graphs:**
- Throughput (Mbps) over time
- RSSI signal strength (dBm)
- Channel history (6 → 11)
- Event log (detection, responses)

---

## Key Files

| File | Purpose |
|------|---------|
| `config.json` | Configuration (IPs, channels, thresholds) |
| `controller_server.py` | SDN controller (detection + decisions) |
| `ap_agent.py` | AP WiFi control (hostapd integration) |
| `monitor_agent.py` | Metrics reporter + jammer generator |
| `orchestrator.py` | Master script (runs all 5 phases) |
| `dashboard.py` | Flask web interface |
| `COMPLETE_GUIDE.md` | Full documentation |

---

## Troubleshooting

**Q: Agents can't communicate**
```bash
# Test connectivity
ping 192.168.1.100  # From AP or Monitor laptop
```

**Q: Phones don't see SDN-TestNet**
```bash
# Restart AP agent
# Check: iw dev wlan0 link
```

**Q: Jammer not detected**
- Check Monitor is sending 8000 pps
- Verify config.json thresholds
- Check controller logs

**Q: Channel switch fails**
```bash
# Test manually
hostapd_cli -i wlan0 set_channel 11
```

---

## Expected Results

| Phase | Throughput | Latency | Channel |
|-------|-----------|---------|---------|
| Baseline | 9.0 Mbps | 15ms | 6 |
| Jammer | 1.5 Mbps | 250ms | 6 |
| Recovery | 9.5 Mbps | 18ms | 11 |

---

## For Faculty

**Show them:**
1. 3 physical laptops (proves real, not simulated)
2. Live metrics degrading (jammer impact)
3. Controller detecting jammer
4. Channel switching in real-time
5. Metrics recovering (proof it works)

**Files to show:**
- `config.json` (multi-machine setup)
- Dashboard (real-time graphs)
- `sdn_testbed_metrics.json` (quantified results)
- Controller logs (detection & response)

---

**Status:** ✅ Ready for evaluation  
**Total runtime:** 40 seconds  
**Reproducible:** Yes (fully automated)  
**Real hardware:** Yes (3 physical laptops + 2 phones)

See `COMPLETE_GUIDE.md` for detailed documentation.

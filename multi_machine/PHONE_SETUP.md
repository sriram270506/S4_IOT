# Phone Setup Guide for SDN Testbed

## Step-by-Step Instructions

### For Both Phone 1 and Phone 2

#### Step 1: Install iperf3 App

1. Open **Google Play Store**
2. Search for **"iperf3"**
3. Look for app by **xnetcat** (it's free, no ads)
4. Tap **Install**
5. Wait for installation to complete
6. Open the app

#### Step 2: Connect to WiFi

1. Go to **Settings** → **WiFi**
2. Look for network named **"SDN-TestNet"** (broadcasted by AP laptop)
3. Tap on it
4. No password required (it's an open AP)
5. Wait for connection (icon shows WiFi symbol)

#### Step 3: Find Your IP Address

1. Go to **Settings** → **About Phone** (or **Device Information**)
2. Scroll down to find **IP Address**
3. Should be something like **192.168.88.11** or **192.168.88.12**
4. Note this IP down

#### Step 4: Start iperf3 Server

1. Open **iperf3** app
2. Tap the **Server** button (bottom of screen)
3. You should see **"Server started on port 5201"**
4. Leave this running

#### Step 5: Verify Connection

1. On controller laptop, run:
   ```bash
   python3 ap_agent.py config.json
   ```

2. Check controller log - should show:
   ```
   Connected clients: 2
   ```

---

## What Happens During Experiment

### Phase 1: Baseline (10 seconds)
- Phone is idle (app running as server)
- Controller measures throughput to your phone
- You might notice some network activity

### Phase 2: Jammer Active (10 seconds)
- Network becomes congested
- App may show connection lag
- WiFi signal might appear weaker
- **This is normal - jammer is attacking**

### Phase 3: Recovery (18 seconds)
- Channel switches from 6 to 11
- **Important:** Phone auto-reconnects to new channel
  - You may see WiFi disconnect/reconnect animation
  - This is normal and expected
- Network becomes fast again
- Controller shows metrics recovering

---

## Troubleshooting

### Problem: Can't Find "SDN-TestNet"

**Solution:**
1. Make sure AP laptop is running `ap_agent.py`
2. Check that hostapd is running
3. Try WiFi "Scan" to refresh network list
4. Restart phone WiFi (toggle OFF/ON)

---

### Problem: App Says "Server Failed to Start"

**Solution:**
1. Restart the iperf3 app
2. Make sure no other app is using port 5201
3. Try again

---

### Problem: Can't Get IP Address

**Solution:**
1. Check WiFi is connected (WiFi icon shows)
2. Go to **Settings** → **WiFi** → Tap "SDN-TestNet" → **Edit**
3. Look for **DHCP** IP address
4. If still not showing, restart phone WiFi

---

### Problem: Phone Doesn't Auto-Reconnect After Channel Switch

**Solution:**
1. This is normal on some phones (5-10 second delay)
2. If it takes longer than 15 seconds:
   - Manually reconnect: Settings → WiFi → SDN-TestNet
   - Or restart iperf3 app

---

## Technical Details (Optional)

### What iperf3 Does

- Listens on port 5201 for connections
- Measures throughput when controller sends data
- Logs successful transfers

### Why Two Phones?

- Simulates real wireless network with multiple clients
- Controller measures both: `~4.5 Mbps × 2 = ~9 Mbps total`
- Demonstrates load balancing across clients

### What Happens at Jammer Activation

- Monitor laptop sends 8000 packets/second
- Creates interference on WiFi Channel 6
- Your phone's packets get dropped/delayed
- Throughput drops dramatically

### What Happens at Channel Switch

- AP broadcasts on Channel 11 instead of 6
- Phone's WiFi driver auto-reconnects
- Jammer still on Channel 6 (physically separated)
- Your network becomes clean again

---

## Success Criteria

Your phone is set up correctly if:
- ✅ WiFi shows "SDN-TestNet" as connected
- ✅ IP address appears in Settings (192.168.88.x)
- ✅ iperf3 app shows "Server started"
- ✅ App stays running (doesn't crash)
- ✅ WiFi auto-reconnects after 10-15 seconds during experiment

---

## During Experiment

### Do's
- ✅ Leave iperf3 app running
- ✅ Keep phone on and nearby AP
- ✅ Keep screen on (or prevent sleep)
- ✅ Expect WiFi to disconnect/reconnect briefly (~10s into experiment)
- ✅ Note the IP address for controller

### Don'ts
- ❌ Don't close iperf3 app
- ❌ Don't disconnect from WiFi manually
- ❌ Don't move phone far from AP
- ❌ Don't launch other bandwidth-hungry apps
- ❌ Don't turn off WiFi

---

## After Experiment

You can:
- Close iperf3 app
- Disconnect from "SDN-TestNet"
- Reconnect to normal home WiFi
- All data is local to controller (no privacy concerns)

---

## Questions?

See `COMPLETE_GUIDE.md` for more details about:
- How jammer detection works
- What metrics are measured
- How channel switching works
- Expected performance numbers

---

**Status:** ✅ Ready to use  
**Difficulty:** Easy (just install app + connect WiFi)  
**Time to setup:** 5 minutes per phone

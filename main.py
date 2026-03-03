"""main.py

Entrypoint for SDN wireless reconfiguration + jammer isolation simulation.
"""
import random
import time
from access_point import AccessPoint
from client import Client
from jammer import Jammer
from monitor import Monitor
from controller import Controller
from visualizer import Visualizer


def setup_simulation(seed: int = 42):
    random.seed(seed)

    # Create APs: start both on same channel to induce interference
    ap1 = AccessPoint('AP1', channel=6, bandwidth_mbps=100.0)
    ap2 = AccessPoint('AP2', channel=6, bandwidth_mbps=100.0)

    # Create 6 clients, 3 per AP
    clients = []
    for i in range(1, 7):
        # vary demand so we can see effects
        mean = 5.0 + (i % 3) * 2.0
        c = Client(f'Client{i}', mean_demand_mbps=mean, variance=1.5)
        clients.append(c)

    # connect first 3 to AP1, next 3 to AP2
    for c in clients[:3]:
        ap1.connect(c)
    for c in clients[3:]:
        ap2.connect(c)

    # monitor
    monitor = Monitor()

    # controller
    controller = Controller([ap1, ap2], monitor)

    # jammer initially inactive
    jammer = Jammer(target_channel=6, active=False)

    return {
        'aps': [ap1, ap2],
        'clients': clients,
        'monitor': monitor,
        'controller': controller,
        'jammer': jammer,
    }


def run(sim, duration_s: int = 60, step_sec: int = 1, jammer_start: int = 10):
    aps = sim['aps']
    clients = sim['clients']
    monitor = sim['monitor']
    controller = sim['controller']
    jammer = sim['jammer']

    viz = Visualizer(monitor, controller, aps, clients, jammer)

    total_steps = int(duration_s / step_sec)

    # We'll drive the simulation within the animation by updating state each second.
    # To do that, we start a background simulation loop that updates state each step and
    # the visualizer will read the monitor's time series.

    # However, to keep things simple and single-threaded (matplotlib main loop), we'll
    # pre-schedule simulation steps by using a generator inside FuncAnimation. Instead,
    # here we implement a simple blocking loop that advances simulation and yields control
    # to the visualizer by letting it plot from the monitor. The visualizer's animation will
    # still poll the monitor periodically.

    # Activate jammer after jammer_start seconds
    print("Starting simulation. Both APs on Channel 6 initially to create interference.")

    for step in range(total_steps + 1):
        # Step timestamp
        t = step

        # Activate jammer at configured time
        if step == jammer_start:
            jammer.activate(channel=6)
            print(f"[Jammer] Activated on channel {jammer.target_channel} (effectiveness {jammer.effectiveness:.2f})")
            monitor.log_event(t, f"Jammer activated on {jammer.target_channel}")

        # Clients generate traffic
        for c in clients:
            c.step()

        # Determine AP conflict counts
        channel_counts = {}
        for ap in aps:
            channel_counts.setdefault(ap.channel, 0)
            channel_counts[ap.channel] += 1

        # APs perform step using interference and jammer
        for ap in aps:
            other = max(0, channel_counts.get(ap.channel, 1) - 1)
            jammer_factor = 0.0
            if jammer.active and ap.channel == jammer.target_channel:
                jammer_factor = jammer.effectiveness
            ap.step(other_aps_on_same_channel=other, jammer_factor=jammer_factor)

        # update jammer internal state
        jinfo = jammer.step()

        # Controller polls telemetry and may reassign channels
        controller.poll(t, jammer_info=jinfo)

        # Print structured logs for important events (monitor already logs events)
        # Sleep to simulate real time for demonstration, but keep responsive to user
        time.sleep(step_sec)

    # After simulation loop, launch visualizer (it will show the collected history). For
    # a streaming effect that shows improvements during the recorded run, we still use
    # the matplotlib animation but it will only visualize the already recorded monitor data.
    print('Simulation complete. Launching visualizer (use window to inspect timelines).')
    viz.run(interval_ms=500)


if __name__ == '__main__':
    sim = setup_simulation(seed=1234)
    # demo: 60s with jammer starting at 10s
    run(sim, duration_s=60, step_sec=1, jammer_start=10)

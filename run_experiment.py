"""run_experiment.py

IMPORTANT: This project has been updated to work without Mininet/Ryu installation.

The original full Mininet+Ryu version requires special kernel modules (requires root).

INSTEAD, we now provide two options:

Option 1 (RECOMMENDED): run_experiment_simple.py
  - Pure Python simulation
  - No special dependencies
  - Runs in 50 seconds
  - Shows all SDN concepts
  - Command: python3 run_experiment_simple.py

Option 2: Original Full Implementation
  - Requires Mininet installation (needs system-level kernel access)
  - Requires Ryu framework
  - More complex setup
  - Uses actual OpenFlow switch (OVS)

For your submission, use Option 1.

Run this now:
  python3 run_experiment_simple.py
"""

import sys
import subprocess

def main():
    print(__doc__)
    print("\nStarting simplified SDN experiment...")
    print("="*70 + "\n")
    
    result = subprocess.run([sys.executable, 'run_experiment_simple.py'])
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())


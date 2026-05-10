# Story 1.1: Hardware & Port Validation Spikes

**Epic:** 1 — Foundation & CI/CD Pipeline
**Story:** 1.1
**Status:** done
**Type:** Spike (investigation/validation — no production code committed)

---

## User Story

As a developer,
I want to validate that the printer connects via USB to the Pi and that port 9000 is available,
So that all architecture decisions are confirmed before any code is written.

---

## Context & Purpose

This is the **first story in the project** and a mandatory prerequisite for all other development. Nothing else can proceed until:

1. The printer's USB vendor ID and product ID are known (needed in `.env` and `printer.py`)
2. `python-escpos Usb()` connection is confirmed working on Pi
3. The udev persistent symlink `/dev/receipt-printer` is created and survives reboot
4. Port 9000 is confirmed free on the Pi (no conflict with PiHole or Octoprint)

**This is a spike — the output is documented findings and configuration, not committed application code.**

The outcomes directly unblock:
- Story 1.2 (scaffolding needs confirmed port and `.env.example` values)
- Story 2.1 (`EscposPrinter` needs vendor/product ID to connect)
- Story 1.3 (docker-compose needs confirmed device path and port)

---

## Acceptance Criteria

**AC1 — lsusb printer identification:**
**Given** the printer is connected to the Pi via USB
**When** `lsusb` is run on the Pi
**Then** the printer vendor ID and product ID are identified and documented in `.env.example`

**AC2 — python-escpos Usb() connection:**
**Given** the vendor ID and product ID from lsusb
**When** `python -c "from escpos.printer import Usb; p = Usb(0xVENDOR, 0xPRODUCT); print('connected')"` is run
**Then** the printer connects without error

**AC3 — udev symlink survives reboot:**
**Given** a udev rule created at `/etc/udev/rules.d/99-receipt-printer.rules` using the printer's vendor/product IDs
**When** the Pi is rebooted with the printer connected
**Then** `/dev/receipt-printer` symlink exists and points to the correct device

**AC4 — port 9000 confirmed free:**
**Given** the Pi is running PiHole and Octoprint
**When** `docker ps` and `netstat -tlnp` are run
**Then** port 9000 is confirmed free and `.env.example` `PORT=9000` is verified correct

---

## Implementation Guide

### Prerequisites

- SSH access to the Pi: `ssh pi@<pi-ip>`
- The thermal receipt printer available (currently connected via Bluetooth to Windows PC — needs USB cable for this test)
- USB cable connecting printer to Pi

### Spike 1: USB Printer Identification

**Step 1 — Connect printer to Pi via USB cable**

**Step 2 — Run lsusb and find the printer:**
```bash
lsusb
```
Look for an entry that is your thermal printer. Example output:
```
Bus 001 Device 005: ID 0483:5740 STMicroelectronics Virtual COM Port
```
The `0483:5740` format is `VENDOR_ID:PRODUCT_ID`.

**Step 3 — Confirm it's the printer by checking device details:**
```bash
lsusb -v -d VENDOR:PRODUCT 2>/dev/null | grep -E "idVendor|idProduct|iProduct|iManufacturer"
```

**Step 4 — Test python-escpos connection:**
```bash
# On the Pi, install python-escpos if not present
pip3 install python-escpos

# Test connection (replace 0xVENDOR and 0xPRODUCT with hex values from lsusb)
python3 -c "
from escpos.printer import Usb
p = Usb(0xVENDOR, 0xPRODUCT)
print('Connected successfully')
p.text('Test\n\n\n')
p.cut()
"
```

**If connection fails with permission error:**
```bash
# Add pi user to lp group (printer group)
sudo usermod -a -G lp pi
# Also try plugdev group
sudo usermod -a -G plugdev pi
# Logout and back in, then retry
```

**If connection fails with "Device not found":**
```bash
# Check if printer appears as different device type
ls -la /dev/usb/
ls -la /dev/ttyUSB*
# Some printers enumerate as /dev/ttyUSB0 (serial-over-USB) rather than /dev/usb/lp0
# If serial: use Serial() backend instead of Usb()
```

**Step 5 — Test get_status() for paper sensor capability:**
```bash
python3 -c "
from escpos.printer import Usb
p = Usb(0xVENDOR, 0xPRODUCT)
try:
    status = p.get_status()
    print('Status result:', status)
    print('Paper sensor available:', True)
except Exception as e:
    print('get_status() not supported:', e)
    print('Paper sensor available: False - will use byte-count estimation only')
"
```
**Document the result** — this determines whether `hardware_paper_sensor_available` in `roll_state.json` is set to `true` or `false`.

---

### Spike 2: udev Persistent Symlink

**Step 1 — Create the udev rule:**
```bash
sudo nano /etc/udev/rules.d/99-receipt-printer.rules
```

Add this content (replace `VENDOR` and `PRODUCT` with the actual 4-character hex values from lsusb, lowercase, no `0x` prefix):
```
SUBSYSTEM=="usb", ATTRS{idVendor}=="VENDOR", ATTRS{idProduct}=="PRODUCT", SYMLINK+="receipt-printer", MODE="0666"
```

Example (if vendor=0483, product=5740):
```
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", SYMLINK+="receipt-printer", MODE="0666"
```

**Step 2 — Reload udev rules:**
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Step 3 — Verify symlink exists before reboot:**
```bash
ls -la /dev/receipt-printer
```

**Step 4 — Reboot and verify:**
```bash
sudo reboot
# After reboot:
ssh pi@<pi-ip>
ls -la /dev/receipt-printer
```
The symlink must exist after reboot for AC3 to pass.

**If printer enumerates as serial (ttyUSB):**
```
SUBSYSTEM=="tty", ATTRS{idVendor}=="VENDOR", ATTRS{idProduct}=="PRODUCT", SYMLINK+="receipt-printer", MODE="0666"
```

---

### Spike 3: Port Availability Check

**Step 1 — Check what ports are in use:**
```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
netstat -tlnp 2>/dev/null | grep LISTEN
# Alternative if netstat not available:
ss -tlnp
```

**Step 2 — Check PiHole specifically:**
```bash
docker inspect pihole 2>/dev/null | grep -A5 '"Ports"'
```

**Step 3 — Check Octoprint specifically:**
```bash
docker inspect octoprint 2>/dev/null | grep -A5 '"Ports"'
# Octoprint default is 5000, but verify
```

**Step 4 — Confirm port 9000 is free:**
```bash
netstat -tlnp 2>/dev/null | grep :9000
# Should return nothing if port is free
```

If port 9000 is in use, choose an alternative (e.g., 8888, 3001, 9001) and document it.

---

## Outputs to Document

After completing all spikes, document these values. These will be committed to `.env.example` in Story 1.2:

```
# Printer Hardware
PRINTER_VENDOR_ID=0x????    # from lsusb (e.g., 0x0483)
PRINTER_PRODUCT_ID=0x????   # from lsusb (e.g., 0x5740)
PRINTER_BACKEND=usb         # or 'serial' if printer uses ttyUSB
PRINTER_DEVICE=/dev/receipt-printer

# Service Configuration
PORT=9000                    # or alternative if 9000 in use

# Paths (used in Docker)
DATA_DIR=/app/data

# Hardware Capabilities (discovered during spike)
HARDWARE_PAPER_SENSOR=true  # or false based on get_status() test
```

Also document:
- Whether `get_status()` is supported (for `roll_tracker.py` sensor logic in Story 2.6)
- Actual PiHole port(s) in use (for future reference)
- Any groups the `pi` user needed to join for USB access

---

## Architecture Compliance Notes

From `architecture.md`:

- **Device path:** The udev symlink MUST be `/dev/receipt-printer` — this is hardcoded in `docker-compose.yml` as `devices: ["/dev/receipt-printer:/dev/receipt-printer"]`
- **USB vs Serial:** The architecture assumes `python-escpos Usb()` backend. If the printer only works via `Serial()` backend (`/dev/ttyUSB0`), this must be flagged as it changes `printer.py` implementation in Story 2.1
- **Port 9000:** The architecture assumes port 9000. If this changes, update the architecture document and note in story dev notes
- **`MODE="0666"` in udev rule:** Required so the Docker container can access the device without `--privileged` mode

---

## Failure Scenarios & Fallbacks

| Scenario | Action |
|---|---|
| Printer not detected by `lsusb` | Try different USB cable; check printer is powered on; try `lsusb -t` for tree view |
| `Usb()` permission denied | Add `pi` to `lp` and `plugdev` groups; reboot |
| `Usb()` raises "Device not found" | Printer may use serial-over-USB; test with `Serial(devfile='/dev/ttyUSB0', ...)`; update architecture if needed |
| `get_status()` raises exception | Document as `hardware_paper_sensor_available: false`; byte-count estimation will be the only method |
| udev symlink not created | Check rule syntax; try `udevadm test $(udevadm info -q path -n /dev/usb/lp0)` for debug info |
| Port 9000 in use | Choose next available port (try 8888, 9001); update `PORT` in `.env.example` |
| PiHole owns port 9000 | Very unlikely (PiHole uses 80/443/53); but if so, use 8888 |

---

## Definition of Done

- [ ] `lsusb` output captured, vendor/product IDs documented
- [ ] `python-escpos Usb(vendor, product)` connects successfully on the Pi
- [ ] `get_status()` tested — result documented (supported: true/false)
- [ ] udev rule at `/etc/udev/rules.d/99-receipt-printer.rules` created
- [ ] `/dev/receipt-printer` symlink confirmed present after Pi reboot
- [ ] Port 9000 confirmed free (or alternative chosen and documented)
- [ ] All discovered values noted for inclusion in `.env.example` in Story 1.2
- [ ] Any deviations from the planned architecture (e.g., serial backend needed) flagged in dev notes below

---

## Dev Notes

```
PRINTER_VENDOR_ID: 0x1ba0
PRINTER_PRODUCT_ID: 0x220a
PRINTER_BRAND: Jolimark
PRINTER_BACKEND: usb (Usb() class)
HARDWARE_PAPER_SENSOR: true (method is paper_status(), NOT get_status())
PAPER_STATUS_VALUES: 2 = paper OK
PORT: 9000 (confirmed free)
PIHOLE_PORTS: 53 (TCP+UDP), 80, 67
OCTOPRINT_PORT: 5000
USB_GROUPS_ADDED: udev rule MODE="0666" handles access (no group changes needed)
UDEV_RULE: /etc/udev/rules.d/99-receipt-printer.rules
SYMLINK: /dev/receipt-printer (confirmed survives reboot)
DEVIATIONS: paper_status() not get_status() — update printer.py interface in Story 2.1
```

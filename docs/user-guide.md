# PrintServer — User Guide

PrintServer lets you print to a thermal receipt printer from your phone browser or via Telegram.

**App:** `http://192.168.0.25:9000` (on the home network)
**Telegram bot:** `@CobaPrinty_bot`

---

## The app

Open the URL in your phone browser. You can install it to your home screen like an app:
- **Android (Chrome):** tap the menu → *Add to Home Screen*
- **iPhone (Safari):** tap the Share button → *Add to Home Screen*

Once installed it opens full-screen, no browser chrome.

### Status bar

At the top of every screen:

- **Dot** — printer status. Green (pulsing) = online and ready. Grey = offline. Amber = paper running low.
- **Gauge** — estimated paper remaining on the current roll.

### Print types

**Free Text** — type anything and choose a font size (Small / Medium / Large). Prints immediately.

**QR Code** — enter a URL. A preview QR code appears as you type. Tap Print to print it on paper.

**Todo List** — give your list a title, add items one by one (tap Add or press Enter), then Print. Each item gets a checkbox on the receipt.

**Receipt** — enter a store name, optional address and phone, add line items with prices, set a tax percentage. The subtotal, tax, and total update live as you add items.

**Goatse** — you know what this is.

**Admin** — manage the paper roll and see Telegram bot activity. See [Admin](#admin) below.

### After printing

A toast notification confirms success (green) or reports an error (red). If the printer is offline, you'll see "Printer offline" — go to Admin and tap **Restart Service** if the printer was recently power-cycled.

---

## Telegram bot

Message `@CobaPrinty_bot` on Telegram to print without opening the app.

### Commands

```
print: Hello world
```
Prints "Hello world" in medium font.

```
print todo: Shopping | Milk | Bread | Eggs
```
Prints a todo list titled "Shopping" with three items. Separate the title and each item with `|`.

The bot replies **Printing ✓** when it works, or **Printer error: ...** if something goes wrong.

Anything else you send the bot will get a help message back.

---

## Admin

Open the app and tap **Admin** from the home screen.

### Current Roll

Shows estimated paper remaining, how much has been printed since the last roll change, and when the roll was last reset.

The gauge self-calibrates: the first time the printer's hardware sensor detects paper running low, it back-calculates the real usage rate for your roll and updates its model. Estimates improve over time.

### Log New Roll

When you put in a fresh roll of paper:

1. Measure or note the roll's width and diameter (typical: 57mm × 40mm)
2. Enter the dimensions in the form
3. Tap **Save New Roll** — this resets the usage counter and clears the old calibration

### Service

Tap **Restart Service** after powering the printer off and on again. The app needs to reconnect to the printer whenever it loses USB — this button does that without needing SSH access.

### Printy — Bot Messages

Shows the last 20 messages received by the Telegram bot:

| Status | Meaning |
|---|---|
| ✓ printed | Message was received and printed successfully |
| ✗ error | Printer returned an error |
| ? help | Sender sent an unrecognised command |
| ⊘ blocked | Sender is not on the allowed list (if allowlist is enabled) |

---

## Troubleshooting

**Printer offline (grey dot)**
The printer is turned off, or just needs the USB connection re-established. Check the printer is on, then go to Admin → Restart Service.

**Print button does nothing / spinner doesn't stop**
The request is timing out (8 second limit). The printer may be in a bad state. Go to Admin → Restart Service.

**QR code print crashes the printer**
Power cycle the printer (turn off and on), then go to Admin → Restart Service.

**Telegram bot not responding**
The printer may have been unavailable when the container started, so the bot didn't start. Go to Admin → Restart Service. If it still doesn't respond after ~15 seconds, the bot token may need checking.

**Roll gauge seems wrong**
The gauge starts with a rough estimate and self-calibrates once the printer reports "near end". If you've just loaded a new roll, tap **Log New Roll** on the Admin page to reset the counter.

from escpos.printer import Serial
import argparse
from datetime import datetime
import random

LINE_WIDTH = 32

def connect():
    return Serial(devfile='COM9', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1.00, dsrdtr=True)


# ── Goatse ────────────────────────────────────────────────────────────────────

GOATSE = """\
* g o a t s e x * g o a t s e x * g o a t s e x *
g                                               g
o /     \\             \\            /    \\       o
a|       |             \\          |      |      a
t|       `.             |         |       :     t
s`        |             |        \\|       |     s
e \\       | /       /  \\\\\\   --__ \\\\       :    e
x  \\      \\/   _--~~          ~--__| \\     |    x
*   \\      \\_-~                    ~-_\\    |    *
g    \\_     \\        _.--------.______\\|   |    g
o      \\     \\______// _ ___ _ (_(__>  \\   |    o
a       \\   .  C ___)  ______ (_(____>  |  /    a
t       /\\ |   C ____)/      \\ (_____>  |_/     t
s      / /\\|   C_____)       |  (___>   /  \\    s
e     |   (   _C_____}\\______/  // _/ /     \\   e
x     |    \\  |__   \\\\_________// (__/       |  x
*    | \\    \\____)   `----   --'             |  *
g    |  \\_          ___\\       /_          _/ | g
o   |              /    |     |  \\            | o
a   |             |    /       \\  \\           | a
t   |          / /    |         |  \\           |t
s   |         / /      \\__/\\___/    |          |s
e  |           /        |    |       |         |e
x  |          |         |    |       |         |x
* g o a t s e x * g o a t s e x * g o a t s e x *"""

def _compress_line(line, target):
    if len(line) <= target:
        return line
    chars = list(line)
    while len(chars) > target:
        best_start, best_len = -1, 1
        i = 1
        while i < len(chars) - 1:
            if chars[i] == ' ':
                j = i
                while j < len(chars) - 1 and chars[j] == ' ':
                    j += 1
                if j - i > best_len:
                    best_len = j - i
                    best_start = i
                i = j
            else:
                i += 1
        if best_start == -1:
            chars = chars[:target - 1] + [chars[-1]]
            break
        del chars[best_start + best_len - 1]
    return ''.join(chars)

def print_goatse(printer, width=42):
    printer.set(align='left', bold=False, height=1, width=1, font='b')
    for line in GOATSE.split('\n'):
        printer.text(_compress_line(line, width) + '\n')
    printer.text('\n\n\n')
    printer.cut()


# ── To-do list ────────────────────────────────────────────────────────────────

def print_todo(printer, items, title='TO DO'):
    # Title — use double size if it fits, else bold normal
    printer.set(align='center', bold=True, height=1, width=1, font='a')
    if len(title) <= LINE_WIDTH // 2:
        printer.set(align='center', bold=True, height=2, width=2, font='a')
    printer.text(title + '\n')

    printer.set(align='left', bold=False, height=1, width=1)
    printer.text('\n')
    printer.text('-' * LINE_WIDTH + '\n')

    for item in items:
        prefix = '[ ] '
        max_text = LINE_WIDTH - len(prefix)
        # First line
        printer.text(f'{prefix}{item[:max_text]}\n')
        # Continuation lines if item overflows
        remainder = item[max_text:]
        indent = ' ' * len(prefix)
        while remainder:
            printer.text(f'{indent}{remainder[:max_text]}\n')
            remainder = remainder[max_text:]
        printer.text('\n')

    printer.text('-' * LINE_WIDTH + '\n')
    printer.text('\n\n\n')
    printer.cut()


# ── Fake receipt ──────────────────────────────────────────────────────────────

def _row(left, right, width=LINE_WIDTH):
    gap = width - len(left) - len(right)
    if gap < 1:
        left = left[:width - len(right) - 1]
        gap = 1
    return f'{left}{" " * gap}{right}'

def print_receipt(printer, store, items, address=None, phone=None, tax_pct=0):
    now = datetime.now()
    receipt_num = random.randint(10000, 99999)

    # Store name
    printer.set(align='center', bold=True, height=1, width=1, font='a')
    if len(store) <= LINE_WIDTH // 2:
        printer.set(align='center', bold=True, height=2, width=2, font='a')
    printer.text(store + '\n')

    printer.set(align='center', bold=False, height=1, width=1)
    if address:
        for part in address.split(','):
            printer.text(part.strip() + '\n')
    if phone:
        printer.text(phone + '\n')
    printer.text('\n')

    # Meta
    printer.set(align='left')
    printer.text(f'Date:    {now.strftime("%d/%m/%Y %H:%M")}\n')
    printer.text(f'Receipt: #{receipt_num}\n')
    printer.text('-' * LINE_WIDTH + '\n')

    # Items
    subtotal = 0.0
    for name, price in items:
        printer.text(_row(name, f'£{price:.2f}') + '\n')
        subtotal += price

    printer.text('-' * LINE_WIDTH + '\n')

    # Totals
    if tax_pct > 0:
        tax = subtotal * tax_pct / 100
        total = subtotal + tax
        printer.text(_row('Subtotal', f'£{subtotal:.2f}') + '\n')
        printer.text(_row(f'Tax ({tax_pct}%)', f'£{tax:.2f}') + '\n')
        printer.text('-' * LINE_WIDTH + '\n')
    else:
        total = subtotal

    printer.set(bold=True)
    printer.text(_row('TOTAL', f'£{total:.2f}') + '\n')

    printer.set(bold=False, align='center')
    printer.text('\n')
    printer.text('Thank you for your visit!\n')
    printer.text(now.strftime('%d/%m/%Y') + '\n')
    printer.text('\n\n\n')
    printer.cut()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Receipt printer CLI')
    sub = parser.add_subparsers(dest='command', required=True)

    # todo
    p_todo = sub.add_parser('todo', help='Print a to-do list')
    p_todo.add_argument('items', nargs='+', help='Items to include')
    p_todo.add_argument('--title', default='TO DO', help='List title (default: TO DO)')

    # receipt
    p_rec = sub.add_parser('receipt', help='Print a fake receipt')
    p_rec.add_argument('--store', required=True, help='Store name')
    p_rec.add_argument('--address', help='Address (use commas for line breaks)')
    p_rec.add_argument('--phone', help='Phone number')
    p_rec.add_argument('--item', action='append', dest='items',
                       metavar='NAME:PRICE', help='e.g. "Coffee:2.50" (repeatable)')
    p_rec.add_argument('--tax', type=float, default=0, metavar='PCT',
                       help='Tax percentage e.g. 20')

    # goatse
    sub.add_parser('goatse', help='Print goatse ASCII art')

    args = parser.parse_args()
    p = connect()

    if args.command == 'todo':
        print_todo(p, args.items, title=args.title)

    elif args.command == 'receipt':
        if not args.items:
            p_rec.error('Provide at least one --item NAME:PRICE')
        parsed = []
        for raw in args.items:
            try:
                name, price = raw.rsplit(':', 1)
                parsed.append((name.strip(), float(price.strip())))
            except ValueError:
                p_rec.error(f'Bad item format (expected Name:Price): {raw}')
        print_receipt(p, args.store, parsed,
                      address=args.address, phone=args.phone, tax_pct=args.tax)

    elif args.command == 'goatse':
        print_goatse(p)


if __name__ == '__main__':
    main()

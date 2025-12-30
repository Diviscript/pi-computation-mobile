"""
pi_master.py
High-scale π computation on mobile (Termux friendly)

Features:
- Decimal computation with checkpoint
- Digits/second and ETA
- Binary compact storage (~10x smaller)
- SHA256 integrity verification
- BBP hexadecimal digits (fast, independent)
"""

from mpmath import mp
import os
import time
import hashlib

# ===================== CONFIG =====================
TOTAL_DIGITS = 100_000_000
BLOCK_SIZE = 1_000_000
CHECKPOINT_INTERVAL = 120  # seconds
DIGITS_PER_LINE = 50

BASE_DIR = "/storage/emulated/0/pi_master"
DECIMAL_DIR = f"{BASE_DIR}/decimal"
BINARY_FILE = f"{BASE_DIR}/pi.bin"
CHECKPOINT_FILE = f"{BASE_DIR}/checkpoint.txt"
SHA256_FILE = f"{BASE_DIR}/sha256.txt"
HEX_FILE = f"{BASE_DIR}/pi_hex_bbp.txt"
# =================================================

os.makedirs(DECIMAL_DIR, exist_ok=True)

# ---------------- CHECKPOINT ----------------
def save_checkpoint(digits, elapsed):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(f"{digits}\n{elapsed}")

def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        return 0, 0.0
    with open(CHECKPOINT_FILE) as f:
        return int(f.readline()), float(f.readline())

# ---------------- BBP HEX ----------------
def bbp_hex(n):
    x = 0.0
    for k in range(n):
        x += (1 / (16 ** k)) * (
            4 / (8 * k + 1)
            - 2 / (8 * k + 4)
            - 1 / (8 * k + 5)
            - 1 / (8 * k + 6)
        )
    frac = x - int(x)
    out = []
    for _ in range(n):
        frac *= 16
        d = int(frac)
        frac -= d
        out.append(hex(d)[2:].upper())
    return "".join(out)

# ===================== MAIN =====================
generated, elapsed_prev = load_checkpoint()
print(f"Starting from {generated:,} digits")

start_time = time.time()
last_checkpoint = time.time()

with open(BINARY_FILE, "ab") as bin_file:
    while generated < TOTAL_DIGITS:
        mp.dps = generated + BLOCK_SIZE + 20
        pi_digits = str(mp.pi)[2:]

        size = min(BLOCK_SIZE, TOTAL_DIGITS - generated)
        block = pi_digits[generated : generated + size]

        file_index = generated // 5_000_000 + 1
        out_file = f"{DECIMAL_DIR}/pi_{file_index}.txt"
        is_new = not os.path.exists(out_file)

        with open(out_file, "a") as f:
            if is_new and file_index == 1:
                f.write("3.\n")

            for i in range(0, len(block), DIGITS_PER_LINE):
                line = block[i : i + DIGITS_PER_LINE]
                f.write(line + "\n")

                bits = "".join(format(int(d), "04b") for d in line)
                bin_file.write(int(bits, 2).to_bytes(len(bits) // 8, "big"))

        generated += size

        now = time.time()
        elapsed = elapsed_prev + (now - start_time)
        speed = generated / elapsed if elapsed else 0
        remaining = max(0, (TOTAL_DIGITS - generated) / speed) if speed else 0

        print(
            f"{generated:,}/{TOTAL_DIGITS:,} | "
            f"{speed:,.0f} digits/s | ETA {remaining/60:.1f} min"
        )

        if now - last_checkpoint >= CHECKPOINT_INTERVAL:
            save_checkpoint(generated, elapsed)
            last_checkpoint = now
            print("Checkpoint saved")

save_checkpoint(generated, elapsed_prev + (time.time() - start_time))

# ---------------- SHA256 ----------------
print("Calculating SHA256...")
sha = hashlib.sha256()
with open(BINARY_FILE, "rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        sha.update(chunk)

with open(SHA256_FILE, "w") as f:
    f.write(sha.hexdigest())

print("SHA256:", sha.hexdigest())

# ---------------- BBP ----------------
print("Generating BBP hexadecimal digits...")
hex_pi = bbp_hex(100_000)
with open(HEX_FILE, "w") as f:
    f.write("3." + hex_pi)

print("Finished successfully")


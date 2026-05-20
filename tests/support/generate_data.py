"""
Generate random test credentials and write them to tests/support/data.json.

TypeScript equivalent: tests/support/generateDataJson.mjs
Run with: python tests/support/generate_data.py
         or via taskipy: task generate-data

KEY DIFFERENCES from the TypeScript version:
  1. Module system: Python uses standard library (json, pathlib) instead of Node's 'fs' module.
     TS: import { writeFileSync } from 'fs'
     PY: from pathlib import Path  →  Path(...).write_text(...)

  2. Faker API: Python Faker uses snake_case methods.
     TS: faker.internet.userName()     →  PY: fake.user_name()
     TS: faker.internet.password(...)  →  PY: no direct equivalent — explicit construction required.
     The Python Faker library does not support the 'prefix' parameter that the TS version uses
     to guarantee character class requirements, so we build the password manually.

  3. Path resolution: Python uses pathlib.Path(__file__) to locate the script's own directory.
     TS: writeFileSync('tests/support/data.json', ...)  — relative to cwd (works if run from root)
     PY: Path(__file__).parent / 'data.json'            — always relative to this file, cwd-independent

  4. Password requirements for demoqa.com:
     Must contain: uppercase, lowercase, digit, special char (!@#$%^&*), minimum 8 chars.
     TS original relied on the 'prefix' trick: faker.internet.password(10, true, /[A-Za-z0-9]/, 'a1!A')
     PY equivalent: build from guaranteed character pools then shuffle.
"""

import json
import random
import re
import string
import time
from pathlib import Path

from faker import Faker

fake = Faker()

# Output path is always relative to this file — works regardless of cwd.
# TS equivalent: path.join(__dirname, 'data.json')  (if using CJS)
DATA_PATH = Path(__file__).parent / "data.json"


def generate_valid_password(length: int = 12) -> str:
    """
    Build a password that satisfies demoqa.com validation rules.

    Rules: >= 8 chars, >= 1 uppercase, >= 1 lowercase, >= 1 digit, >= 1 special char.

    TS: faker.internet.password(10, true, /[A-Za-z0-9]/, 'a1!A')
    PY: explicit pool construction + Fisher-Yates shuffle via random.shuffle()

    KEY DIFFERENCE: random.shuffle() mutates the list in place (no return value).
    TypeScript's Array.prototype.sort(() => Math.random() - 0.5) returns a new array.
    Python's random.shuffle(lst) returns None — the variable is modified directly.
    """
    guaranteed = [
        random.choice("!@#$%^&*"),  # at least 1 special char
        random.choice(string.ascii_uppercase),  # at least 1 uppercase
        random.choice(string.ascii_lowercase),  # at least 1 lowercase
        random.choice(string.digits),  # at least 1 digit
    ]
    filler_pool = string.ascii_letters + string.digits
    filler = [random.choice(filler_pool) for _ in range(length - len(guaranteed))]

    chars = guaranteed + filler
    random.shuffle(chars)  # in-place — TS equivalent: chars.sort(() => Math.random() - 0.5)
    return "".join(chars)


def generate_username() -> str:
    """
    Generate a URL-safe username with a timestamp suffix for uniqueness.

    TS: faker.internet.userName()  — may contain dots/hyphens that some forms reject
    PY: fake.user_name() + strip non-alphanumeric + timestamp suffix

    KEY DIFFERENCE: re.sub() replaces TypeScript's String.replace() with regex.
    TS: faker.internet.userName().replace(/[^a-zA-Z0-9]/g, '') + Date.now()
    PY: re.sub(r'[^a-zA-Z0-9]', '', fake.user_name()) + str(int(time.time()))

    The /g flag in TS regex is the default in Python's re.sub() — all occurrences replaced.
    """
    base = re.sub(r"[^a-zA-Z0-9]", "", fake.user_name())
    return f"{base}{int(time.time())}"


def main() -> None:
    username = generate_username()
    password = generate_valid_password()

    data = {"userName": username, "password": password}

    # KEY DIFFERENCE: pathlib Path.write_text() replaces Node's fs.writeFileSync()
    # TS: writeFileSync('tests/support/data.json', JSON.stringify(data, null, 2))
    # PY: Path(...).write_text(json.dumps(data, indent=2))
    # json.dumps(indent=2) is the direct equivalent of JSON.stringify(data, null, 2)
    DATA_PATH.write_text(json.dumps(data, indent=2))

    print(f"Generated {DATA_PATH}")
    print(f"  userName: {username}")
    print("  password: [hidden]")


if __name__ == "__main__":
    main()

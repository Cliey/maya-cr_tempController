---
topics:
  - Programming
  - Maya
---

# License and Protection Guide

This document covers protection techniques for distributing cr_tempController commercially.

---

## Table of Contents

1. [String Obfuscation](#1-string-obfuscation)
2. [Anti-Debugging](#2-anti-debugging)
3. [License Checking](#3-license-checking)
   - [Option A: Online Validation](#option-a-online-validation)
   - [Option B: Offline with Hardware Lock](#option-b-offline-with-hardware-lock-recommended)
   - [Option C: Simple Offline Key](#option-c-simple-offline-key)
4. [Integration Example](#4-integration-example)
5. [Recommendations](#5-recommendations)

---

## 1. String Obfuscation

### The Problem

Even in compiled `.pyd` files, string literals are stored as plain text. Anyone can extract them:

```bash
# On Windows (with strings utility or hex editor)
strings controller_mode.cp310-win_amd64.pyd
```

Output reveals:
```
cr_TempControls
_TempControl_Data
sourceNode
Invalid license key
License expired
```

This exposes your internal naming, error messages, and license-related strings.

### Solution 1: Base64 Encoding (Simple)

Encode strings at rest, decode at runtime.

```python
# utils/obfuscation.py
import base64

def _d(encoded: str) -> str:
    """Decode a base64 obfuscated string."""
    return base64.b64decode(encoded).decode('utf-8')

def _e(plain: str) -> str:
    """Encode a string to base64. Use this once to generate encoded values."""
    return base64.b64encode(plain.encode()).decode()
```

**Encoding your strings (run once):**
```python
>>> _e("cr_TempControls")
'Y3JfVGVtcENvbnRyb2xz'
>>> _e("Invalid license")
'SW52YWxpZCBsaWNlbnNl'
```

**Using in code:**
```python
# Before (visible in binary):
TEMP_PIVOT_GROUP = "cr_TempControls"
ERROR_MSG = "Invalid license"

# After (hidden):
from utils.obfuscation import _d
TEMP_PIVOT_GROUP = _d("Y3JfVGVtcENvbnRyb2xz")
ERROR_MSG = _d("SW52YWxpZCBsaWNlbnNl")
```

**Protection level**: Low - base64 is easily recognized and decoded. Stops casual viewers only.

### Solution 2: XOR Encoding (Better)

XOR each character with a key byte.

```python
# utils/obfuscation.py

# Key should be compiled into .pyd, not stored as plain string
_KEY = 0x5A  # Single byte key

def _encode_xor(plain: str) -> bytes:
    """Encode string with XOR. Run once to get encoded bytes."""
    return bytes([ord(c) ^ _KEY for c in plain])

def _decode_xor(encoded: bytes) -> str:
    """Decode XOR-encoded bytes at runtime."""
    return ''.join(chr(b ^ _KEY) for b in encoded)

# Shorter aliases for use in code
def _x(encoded: bytes) -> str:
    return _decode_xor(encoded)
```

**Encoding your strings (run once):**
```python
>>> _encode_xor("cr_TempControls")
b'9x5\x1e7\x0f6\x1b9\x0b$<x0&y'
>>> _encode_xor("Invalid license")
b'\x13$<\x0f&\x12;\x1e&\x12;7$y7'
```

**Using in code:**
```python
from utils.obfuscation import _x

TEMP_PIVOT_GROUP = _x(b'9x5\x1e7\x0f6\x1b9\x0b$<x0&y')
ERROR_MSG = _x(b'\x13$<\x0f&\x12;\x1e&\x12;7$y7')
```

**Protection level**: Medium - requires more effort to decode, not immediately recognizable.

### Solution 3: Multi-byte XOR with Rotating Key (Stronger)

```python
# utils/obfuscation.py

# Multi-byte key (compile this into .pyd)
_MKEY = b'\x5A\x3F\x7C\x2B\x91'

def _encode_multi(plain: str) -> bytes:
    """Encode with rotating multi-byte XOR key."""
    key_len = len(_MKEY)
    return bytes([ord(c) ^ _MKEY[i % key_len] for i, c in enumerate(plain)])

def _decode_multi(encoded: bytes) -> str:
    """Decode multi-byte XOR at runtime."""
    key_len = len(_MKEY)
    return ''.join(chr(b ^ _MKEY[i % key_len]) for i, b in enumerate(encoded))

def _m(encoded: bytes) -> str:
    return _decode_multi(encoded)
```

**Protection level**: Medium-High - pattern analysis required to break.

### What to Obfuscate

| Priority | What | Why |
|----------|------|-----|
| High | License error messages | Reveals protection logic |
| High | License validation strings | Key format hints |
| Medium | Internal node names | Your naming conventions |
| Medium | Attribute names | Internal structure |
| Low | UI labels | Not sensitive |

### Helper Script for Bulk Encoding

```python
# tools/encode_strings.py (development tool, don't distribute)

from utils.obfuscation import _encode_xor

strings_to_encode = [
    "cr_TempControls",
    "sourceNode",
    "Invalid license",
    "License expired",
    "_TempControl_Data",
]

print("# Encoded strings for copy-paste:\n")
for s in strings_to_encode:
    encoded = _encode_xor(s)
    print(f'# "{s}"')
    print(f"_x({encoded})\n")
```

---

## 2. Anti-Debugging

### The Problem

Reverse engineers attach debuggers (PyCharm, VS Code, pdb) to step through your code and understand the logic.

### Solution 1: Detect Python Debugger (sys.gettrace)

```python
# utils/protection.py
import sys

def is_debugger_attached() -> bool:
    """Check if a Python debugger is attached."""
    return sys.gettrace() is not None
```

### Solution 2: Detect Known Debugger Modules

```python
# utils/protection.py
import sys

DEBUGGER_MODULES = [
    'pydevd',           # PyCharm debugger
    'pydevd_frame',     # PyCharm internals
    '_pydevd',          # PyCharm native
    'debugpy',          # VS Code debugger
    'pdb',              # Standard library debugger
    'ipdb',             # IPython debugger
    'pudb',             # Console debugger
    'bdb',              # Base debugger class
    'rpdb',             # Remote debugger
]

def has_debugger_modules() -> bool:
    """Check if known debugger modules are loaded."""
    for mod in DEBUGGER_MODULES:
        if mod in sys.modules:
            return True
    return False
```

### Solution 3: Timing Check

Debuggers slow down execution. Measure critical operations.

```python
# utils/protection.py
import time

def timing_check() -> bool:
    """
    Detect debugger by measuring execution time.
    Simple operations should be fast; debuggers add overhead.
    """
    start = time.perf_counter()

    # Simple operation that should be instant
    result = 0
    for i in range(1000):
        result += i

    elapsed = time.perf_counter() - start

    # Should complete in < 1ms normally, debugger makes it slower
    return elapsed > 0.1  # 100ms threshold

def is_being_debugged() -> bool:
    return timing_check()
```

### Solution 4: Environment Checks

```python
# utils/protection.py
import os
import sys

def suspicious_environment() -> bool:
    """Check for suspicious environment variables and conditions."""

    # Common debugger environment variables
    debug_vars = [
        'PYDEVD_USE_FRAME_EVAL',
        'PYTHONBREAKPOINT',
        'PYCHARM_DEBUG',
        'VSCODE_PID',
        'DEBUGPY_LAUNCHER_PORT',
    ]

    for var in debug_vars:
        if os.environ.get(var):
            return True

    # Check if running in interactive mode (could be debugging)
    if hasattr(sys, 'ps1'):
        return True

    return False
```

### Combined Protection Check

```python
# utils/protection.py
import sys
import os
import time
import logging

LOGGER = logging.getLogger(__name__)

class EnvironmentValidator:
    """Validates the runtime environment for protection."""

    DEBUGGER_MODULES = [
        'pydevd', 'pydevd_frame', '_pydevd', 'debugpy',
        'pdb', 'ipdb', 'pudb', 'bdb', 'rpdb'
    ]

    DEBUG_ENV_VARS = [
        'PYDEVD_USE_FRAME_EVAL', 'PYTHONBREAKPOINT',
        'PYCHARM_DEBUG', 'VSCODE_PID', 'DEBUGPY_LAUNCHER_PORT'
    ]

    @classmethod
    def validate(cls) -> tuple[bool, str]:
        """
        Run all environment checks.
        Returns (is_valid, reason) tuple.
        """
        # Check 1: sys.gettrace
        if sys.gettrace() is not None:
            return False, "trace_detected"

        # Check 2: Debugger modules
        for mod in cls.DEBUGGER_MODULES:
            if mod in sys.modules:
                return False, f"module_{mod}"

        # Check 3: Environment variables
        for var in cls.DEBUG_ENV_VARS:
            if os.environ.get(var):
                return False, f"env_{var}"

        # Check 4: Timing (optional, can have false positives)
        # Uncomment if you want aggressive protection
        # if cls._timing_check():
        #     return False, "timing_anomaly"

        return True, "ok"

    @classmethod
    def _timing_check(cls) -> bool:
        start = time.perf_counter()
        result = sum(range(1000))
        elapsed = time.perf_counter() - start
        return elapsed > 0.05  # 50ms threshold

    @classmethod
    def enforce(cls, silent: bool = False) -> None:
        """
        Enforce environment validation.
        Raises RuntimeError if checks fail.
        """
        is_valid, reason = cls.validate()

        if not is_valid:
            if not silent:
                LOGGER.warning(f"Environment check failed: {reason}")
            raise RuntimeError("This application cannot run in the current environment")
```

### Usage in Your Plugin

```python
# cr_tempController.py (entry point)
from utils.protection import EnvironmentValidator

def run():
    # Validate environment before doing anything
    EnvironmentValidator.enforce()

    # ... rest of your code
```

### Important Notes

| Note | Details |
|------|---------|
| **False positives** | Maya itself might trigger some checks in certain modes |
| **Not foolproof** | Determined attackers can patch these checks out |
| **User experience** | Don't be too aggressive; legitimate users might have dev tools installed |
| **Silent mode** | Consider logging but not blocking in some cases |

### Recommended Approach

```python
def run():
    is_valid, reason = EnvironmentValidator.validate()

    if not is_valid:
        # Log for your analytics (if you have any)
        LOGGER.info(f"Environment flag: {reason}")

        # Option 1: Hard block
        # raise RuntimeError("Environment not supported")

        # Option 2: Soft block (degrade functionality)
        # DEMO_MODE = True

        # Option 3: Just log and continue (least intrusive)
        pass

    # Continue with normal execution
```

---

## 3. License Checking

### Overview of Options

| Option | Security | Ease of Use | Requires Server | Prevents Sharing |
|--------|----------|-------------|-----------------|------------------|
| A: Online | High | Medium | Yes | Yes |
| B: Hardware Lock | Medium-High | Medium | No | Yes |
| C: Simple Key | Low-Medium | High | No | No |

---

### Option A: Online Validation

User's key is validated against your server on each launch.

#### Server Side (Example with Flask)

```python
# server/license_server.py (runs on your server)
from flask import Flask, request, jsonify
import hashlib
import sqlite3
from datetime import datetime

app = Flask(__name__)
SECRET = "your-server-secret-key"

def get_db():
    conn = sqlite3.connect('licenses.db')
    return conn

@app.route('/validate', methods=['POST'])
def validate_license():
    data = request.json
    license_key = data.get('key', '')
    machine_id = data.get('machine_id', '')

    conn = get_db()
    cursor = conn.cursor()

    # Check if license exists and is valid
    cursor.execute('''
        SELECT email, expiry_date, max_machines, active
        FROM licenses
        WHERE license_key = ?
    ''', (license_key,))

    row = cursor.fetchone()

    if not row:
        return jsonify({'valid': False, 'reason': 'invalid_key'})

    email, expiry_date, max_machines, active = row

    if not active:
        return jsonify({'valid': False, 'reason': 'deactivated'})

    if datetime.now() > datetime.strptime(expiry_date, '%Y-%m-%d'):
        return jsonify({'valid': False, 'reason': 'expired'})

    # Check machine count
    cursor.execute('''
        SELECT COUNT(DISTINCT machine_id)
        FROM activations
        WHERE license_key = ?
    ''', (license_key,))

    machine_count = cursor.fetchone()[0]

    # Check if this machine is already registered
    cursor.execute('''
        SELECT 1 FROM activations
        WHERE license_key = ? AND machine_id = ?
    ''', (license_key, machine_id))

    is_registered = cursor.fetchone() is not None

    if not is_registered and machine_count >= max_machines:
        return jsonify({'valid': False, 'reason': 'max_machines_reached'})

    # Register this machine
    if not is_registered:
        cursor.execute('''
            INSERT INTO activations (license_key, machine_id, activated_at)
            VALUES (?, ?, ?)
        ''', (license_key, machine_id, datetime.now().isoformat()))
        conn.commit()

    conn.close()

    return jsonify({
        'valid': True,
        'expiry': expiry_date,
        'email': email
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
```

#### Client Side (In Your Plugin)

```python
# utils/license_online.py
import urllib.request
import urllib.error
import json
import hashlib
import uuid
import ssl

class OnlineLicenseManager:
    SERVER_URL = "https://your-domain.com/validate"

    @classmethod
    def get_machine_id(cls) -> str:
        """Get unique machine identifier."""
        mac = uuid.getnode()
        return hashlib.sha256(str(mac).encode()).hexdigest()[:32]

    @classmethod
    def validate(cls, license_key: str) -> tuple[bool, str]:
        """
        Validate license against server.
        Returns (is_valid, message).
        """
        machine_id = cls.get_machine_id()

        payload = json.dumps({
            'key': license_key,
            'machine_id': machine_id
        }).encode('utf-8')

        try:
            req = urllib.request.Request(
                cls.SERVER_URL,
                data=payload,
                headers={'Content-Type': 'application/json'}
            )

            # Create SSL context (for self-signed certs in dev, remove in production)
            context = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                result = json.loads(response.read().decode('utf-8'))

                if result.get('valid'):
                    return True, f"Licensed to {result.get('email', 'user')}"
                else:
                    reason = result.get('reason', 'unknown')
                    messages = {
                        'invalid_key': 'Invalid license key',
                        'expired': 'License has expired',
                        'deactivated': 'License has been deactivated',
                        'max_machines_reached': 'Maximum activations reached',
                    }
                    return False, messages.get(reason, 'Validation failed')

        except urllib.error.URLError as e:
            return False, f"Could not connect to license server: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"
```

**Pros**: Full control, can revoke keys, track usage
**Cons**: Requires server, users need internet, more complex

---

### Option B: Offline with Hardware Lock (Recommended)

License key is tied to user's machine. No server needed after purchase.

```python
# utils/license_hardware.py
import hashlib
import uuid
import datetime
import os
import json
from pathlib import Path

class HardwareLicenseManager:
    """
    Offline license manager with hardware locking.

    Workflow:
    1. Customer runs get_machine_id() and sends you the ID
    2. You run generate_license() with their machine ID and expiry date
    3. Customer enters the license key in your plugin
    4. Plugin validates offline using validate_license()
    """

    # IMPORTANT: Change this secret and compile into .pyd
    # Do NOT leave as-is or store in plain .py file
    _SECRET = "change-this-to-your-unique-secret-key-abc123"

    # License file location (in Maya prefs)
    _LICENSE_FILE = Path(os.environ.get('MAYA_APP_DIR', '~')) / 'cr_tempController_license.json'

    @classmethod
    def get_machine_id(cls) -> str:
        """
        Get unique machine identifier.
        Customer sends this to you when purchasing.
        """
        # Combine multiple identifiers for more uniqueness
        mac = uuid.getnode()

        # On Windows, could also use:
        # - os.environ.get('COMPUTERNAME', '')
        # - WMI queries for motherboard serial

        raw_id = f"{mac}"
        return hashlib.sha256(raw_id.encode()).hexdigest()[:16].upper()

    @classmethod
    def generate_license(cls, machine_id: str, expiry_date: str, customer_email: str = "") -> str:
        """
        Generate a license key for a customer.
        YOU run this (not the customer).

        Args:
            machine_id: Customer's machine ID from get_machine_id()
            expiry_date: Expiry date in YYYY-MM-DD format
            customer_email: Optional customer identifier

        Returns:
            License key string like: ABCD1234-20261231-X7F9A2B3
        """
        # Normalize inputs
        machine_id = machine_id.upper()[:16]
        expiry_compact = expiry_date.replace('-', '')  # 20261231

        # Create signature
        sign_data = f"{machine_id}:{expiry_compact}:{customer_email}:{cls._SECRET}"
        signature = hashlib.sha256(sign_data.encode()).hexdigest()[:8].upper()

        # Format: MACHINE-EXPIRY-SIGNATURE
        return f"{machine_id[:8]}-{expiry_compact}-{signature}"

    @classmethod
    def validate_license(cls, license_key: str) -> tuple[bool, str, dict]:
        """
        Validate a license key offline.

        Returns:
            (is_valid, message, details_dict)
        """
        try:
            # Parse the key
            parts = license_key.strip().upper().split('-')
            if len(parts) != 3:
                return False, "Invalid key format", {}

            key_machine, key_expiry, key_signature = parts

            # Validate format
            if len(key_machine) != 8 or len(key_expiry) != 8 or len(key_signature) != 8:
                return False, "Invalid key format", {}

            # Check machine ID
            current_machine = cls.get_machine_id()[:8]
            if key_machine != current_machine:
                return False, "License not valid for this machine", {
                    'expected_machine': current_machine,
                    'key_machine': key_machine
                }

            # Check expiry date
            try:
                expiry_date = datetime.datetime.strptime(key_expiry, "%Y%m%d")
                if datetime.datetime.now() > expiry_date:
                    return False, "License has expired", {
                        'expiry': expiry_date.strftime("%Y-%m-%d")
                    }
            except ValueError:
                return False, "Invalid expiry date in key", {}

            # Verify signature (try with and without email since we don't store it)
            expected_sig = hashlib.sha256(
                f"{current_machine}:{key_expiry}::{cls._SECRET}".encode()
            ).hexdigest()[:8].upper()

            if key_signature != expected_sig:
                return False, "Invalid license signature", {}

            return True, "License valid", {
                'expiry': expiry_date.strftime("%Y-%m-%d"),
                'days_remaining': (expiry_date - datetime.datetime.now()).days
            }

        except Exception as e:
            return False, f"Validation error: {e}", {}

    @classmethod
    def save_license(cls, license_key: str) -> bool:
        """Save license key to disk."""
        try:
            cls._LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls._LICENSE_FILE, 'w') as f:
                json.dump({'license_key': license_key.strip().upper()}, f)
            return True
        except Exception:
            return False

    @classmethod
    def load_license(cls) -> str | None:
        """Load saved license key from disk."""
        try:
            if cls._LICENSE_FILE.exists():
                with open(cls._LICENSE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('license_key')
        except Exception:
            pass
        return None

    @classmethod
    def check_or_prompt(cls) -> tuple[bool, str]:
        """
        Check saved license or prompt user for one.
        Call this at plugin startup.
        """
        # Try loading saved license
        saved_key = cls.load_license()
        if saved_key:
            is_valid, message, details = cls.validate_license(saved_key)
            if is_valid:
                days = details.get('days_remaining', 0)
                return True, f"Licensed ({days} days remaining)"

        # No valid saved license, need to prompt
        return False, "No valid license found"
```

#### Your License Generation Script (Keep Private)

```python
# tools/generate_license.py (YOU keep this, don't distribute)

from utils.license_hardware import HardwareLicenseManager

def generate_for_customer():
    print("=== License Generator ===\n")

    machine_id = input("Customer's Machine ID: ").strip()
    expiry_date = input("Expiry date (YYYY-MM-DD): ").strip()
    email = input("Customer email (optional): ").strip()

    license_key = HardwareLicenseManager.generate_license(
        machine_id=machine_id,
        expiry_date=expiry_date,
        customer_email=email
    )

    print(f"\n✓ Generated License Key:\n{license_key}\n")
    print(f"Send this to: {email or 'customer'}")

if __name__ == "__main__":
    generate_for_customer()
```

---

### Option C: Simple Offline Key

No hardware lock. Key works on any machine but has expiry.

```python
# utils/license_simple.py
import hashlib
import datetime
import os
import json
from pathlib import Path

class SimpleLicenseManager:
    """
    Simple offline license without hardware locking.
    Keys can be shared between machines.
    """

    # IMPORTANT: Change this and compile into .pyd
    _SECRET = "your-simple-license-secret-xyz789"
    _LICENSE_FILE = Path(os.environ.get('MAYA_APP_DIR', '~')) / 'cr_tempController_license.json'

    @classmethod
    def generate_license(cls, customer_email: str, expiry_date: str) -> str:
        """
        Generate a license key.
        YOU run this (not the customer).

        Args:
            customer_email: Customer's email (used in validation)
            expiry_date: Expiry date in YYYY-MM-DD format

        Returns:
            License key string
        """
        email_hash = hashlib.md5(customer_email.lower().encode()).hexdigest()[:8].upper()
        expiry_compact = expiry_date.replace('-', '')

        sign_data = f"{customer_email.lower()}:{expiry_compact}:{cls._SECRET}"
        signature = hashlib.sha256(sign_data.encode()).hexdigest()[:8].upper()

        return f"{email_hash}-{expiry_compact}-{signature}"

    @classmethod
    def validate_license(cls, customer_email: str, license_key: str) -> tuple[bool, str]:
        """
        Validate a license key.

        Args:
            customer_email: Email used when purchasing
            license_key: The license key

        Returns:
            (is_valid, message)
        """
        try:
            parts = license_key.strip().upper().split('-')
            if len(parts) != 3:
                return False, "Invalid key format"

            key_email_hash, key_expiry, key_signature = parts

            # Verify email hash matches
            expected_hash = hashlib.md5(customer_email.lower().encode()).hexdigest()[:8].upper()
            if key_email_hash != expected_hash:
                return False, "License key does not match this email"

            # Check expiry
            try:
                expiry_date = datetime.datetime.strptime(key_expiry, "%Y%m%d")
                if datetime.datetime.now() > expiry_date:
                    return False, "License has expired"
            except ValueError:
                return False, "Invalid expiry date"

            # Verify signature
            expected_sig = hashlib.sha256(
                f"{customer_email.lower()}:{key_expiry}:{cls._SECRET}".encode()
            ).hexdigest()[:8].upper()

            if key_signature != expected_sig:
                return False, "Invalid license key"

            days_left = (expiry_date - datetime.datetime.now()).days
            return True, f"Valid ({days_left} days remaining)"

        except Exception as e:
            return False, f"Error: {e}"

    @classmethod
    def save_license(cls, email: str, key: str) -> bool:
        try:
            cls._LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls._LICENSE_FILE, 'w') as f:
                json.dump({'email': email, 'key': key.upper()}, f)
            return True
        except:
            return False

    @classmethod
    def load_license(cls) -> tuple[str, str] | None:
        try:
            if cls._LICENSE_FILE.exists():
                with open(cls._LICENSE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('email'), data.get('key')
        except:
            pass
        return None, None
```

---

## 4. Integration Example

### Complete Startup Check

```python
# utils/startup_check.py
import maya.cmds as cmds
from utils.protection import EnvironmentValidator
from utils.license_hardware import HardwareLicenseManager
import logging

LOGGER = logging.getLogger(__name__)

def check_license_with_dialog() -> bool:
    """
    Check license at startup, prompt if needed.
    Returns True if licensed, False otherwise.
    """
    # First check saved license
    is_valid, message = HardwareLicenseManager.check_or_prompt()

    if is_valid:
        LOGGER.info(f"License validated: {message}")
        return True

    # Prompt user for license key
    result = cmds.promptDialog(
        title='License Required',
        message=f'Please enter your license key:\n\nYour Machine ID: {HardwareLicenseManager.get_machine_id()}',
        button=['Activate', 'Cancel'],
        defaultButton='Activate',
        cancelButton='Cancel',
        dismissString='Cancel'
    )

    if result != 'Activate':
        return False

    license_key = cmds.promptDialog(query=True, text=True)

    is_valid, message, details = HardwareLicenseManager.validate_license(license_key)

    if is_valid:
        HardwareLicenseManager.save_license(license_key)
        cmds.confirmDialog(
            title='Success',
            message=f'License activated!\n{message}',
            button=['OK']
        )
        return True
    else:
        cmds.confirmDialog(
            title='Invalid License',
            message=f'License validation failed:\n{message}',
            button=['OK'],
            icon='critical'
        )
        return False

def startup_checks() -> bool:
    """
    Run all startup checks.
    Returns True if all checks pass.
    """
    # Environment check (anti-debugging)
    is_valid, reason = EnvironmentValidator.validate()
    if not is_valid:
        LOGGER.warning(f"Environment check flagged: {reason}")
        # Decide: block, warn, or ignore
        # return False  # Uncomment to block

    # License check
    if not check_license_with_dialog():
        return False

    return True
```

### In Your Main Entry Point

```python
# cr_tempController.py
import cr_tempController.core.temp_controller as temp_controller
import maya.cmds as cmds
import cr_tempController.constants as constants

def run():
    # Import here to ensure compiled module is loaded
    from utils.startup_check import startup_checks

    if not startup_checks():
        cmds.warning("cr_tempController: License required")
        return

    if cmds.window(constants.TOOL_WINDOW_NAME, exists=True):
        cmds.deleteUI(constants.TOOL_WINDOW_NAME)
    temp_controller.TempController().show()
```

---

## 5. Recommendations

### For Most Maya Plugin Developers

| Recommendation | Reason |
|----------------|--------|
| **Use Option B (Hardware Lock)** | Good balance of security and usability |
| **Light obfuscation (XOR)** | Stops casual inspection without complexity |
| **Minimal anti-debugging** | Check `sys.gettrace()` only, don't be aggressive |
| **Compile core + utils** | Keep UI as Python for easier updates |

### Security vs User Experience

| More Secure | Better UX |
|-------------|-----------|
| Online validation | Offline validation |
| Strict anti-debugging | No environment checks |
| Hardware lock | Transferable keys |
| Short expiry | Perpetual licenses |

### Reality Check

- **Determined pirates will crack anything** - Your goal is to make it not worth the effort
- **Most users are honest** - Don't punish them with aggressive protection
- **Support matters more than protection** - Good support reduces piracy motivation
- **Cython + basic licensing is enough** - For a Maya plugin, this stops 95% of casual sharing

### Suggested Implementation Order

1. ✅ Cython compilation (already planned)
2. Add hardware-locked licensing (Option B)
3. Add basic string obfuscation for license messages
4. Add minimal `sys.gettrace()` check
5. Skip aggressive anti-debugging (causes support issues)

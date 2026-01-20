---
topics:
  - Programming
  - Maya
---
# 1. Obfuscate String Literals

**The problem**: Even in compiled .pyd files, strings are stored as plain text. Someone can run strings myfile.pyd and see:
  
```
cr_TempControls
_TempControl_Data
sourceNode
Invalid license key
```

**Solution**: Encode strings at rest, decode at runtime:
``` python
# utils/obfuscation.py
import base64

def _d(s: str) -> str:
	"""Decode an obfuscated string."""
	return base64.b64decode(s).decode('utf-8')
# Pre-encode your sensitive strings (do this once, store the result)
# base64.b64encode("cr_TempControls".encode()).decode() → "Y3JfVGVtcENvbnRyb2xz"

# In your code, instead of:
TEMP_PIVOT_GROUP = "cr_TempControls"

# Use:
TEMP_PIVOT_GROUP = _d("Y3JfVGVtcENvbnRyb2xz")

```

  This isn't unbreakable, but it stops casual snooping. For stronger protection, use XOR with a key:
```python
def _decode(encoded: bytes, key: int = 0x5A) -> str:
	return ''.join(chr(b ^ key) for b in encoded)

# Encode once: bytes([ord(c) ^ 0x5A for c in "cr_TempControls"])
TEMP_PIVOT_GROUP = _decode(b'9x5\x1e7\x0f6\x1b9\x0b$<x0&y')
```
  
# 2. Anti-Debugging

**The problem**: Reverse engineers attach debuggers to step through your code.

Basic detection (works in Maya's Python):
```python
import sys

def _check_environment():
	# Check for common debugger traces
	if sys.gettrace() is not None:
		return False  # Debugger attached

	# Check for suspicious modules
	suspicious = ['pydevd', 'debugpy', 'pdb', '_pydevd']
    for mod in suspicious:
	    if mod in sys.modules:
	        return False

	      return True

# Call at startup
if not _check_environment():
	raise RuntimeError("Environment not supported")
```

Note: This is easily bypassed by determined attackers. It mainly stops casual inspection.

# 3. License Checking Options
## Option A: Online Validation (Most Secure)

User enters key → Your server validates → Returns yes/no

**Pros**: Can revoke keys, track usage, prevent sharing
**Cons**: Requires internet, server maintenance, users dislike it

## Option B: Offline with Hardware Lock (Good Balance)

  Generate a key tied to user's machine. No server needed after purchase.
```python
# license_manager.py
import hashlib
import uuid
import datetime

def get_machine_id() -> str:
	"""Get unique machine identifier."""
	# Combine multiple hardware identifiers
	mac = uuid.getnode()  # MAC address
	return hashlib.sha256(str(mac).encode()).hexdigest()[:16]

def generate_license_key(machine_id: str, expiry_date: str, secret: str) -> str:
	"""YOU run this to generate keys for customers."""
	data = f"{machine_id}:{expiry_date}:{secret}"
	signature = hashlib.sha256(data.encode()).hexdigest()[:12]
	return f"{machine_id[:8]}-{expiry_date.replace('-', '')}-{signature}".upper()

def validate_license(license_key: str, secret: str) -> tuple[bool, str]:
	"""Runs in the plugin to check validity."""
	try:
		parts = license_key.replace('-', '')
		if len(parts) != 28:  # 8 + 8 + 12
			return False, "Invalid format"
		
		key_machine = parts[:8]
		key_date = parts[8:16]
		key_sig = parts[16:]
		
		# Check machine ID matches
		current_machine = get_machine_id()[:8].upper()
		if key_machine != current_machine:
			return False, "License not valid for this machine"
		
		# Check expiry
		expiry = datetime.datetime.strptime(key_date, "%Y%m%d")
		if datetime.datetime.now() > expiry:
			return False, "License expired"
		
		# Verify signature
		expiry_formatted = f"{key_date[:4]}-{key_date[4:6]}-{key_date[6:]}"
		expected_key = generate_license_key(current_machine, expiry_formatted, secret)
		if license_key.upper() != expected_key.upper():
			return False, "Invalid license"
		
		return True, "Valid"
	except Exception:
		return False, "Validation error"
```
  
### Workflow for Option B

- You (the seller):
	1. Customer purchases and sends you their Machine ID (they run get_machine_id())
	2. You generate a key: generate_license_key("abc123...", "2026-12-31", "YOUR_SECRET")
	3. Send them the key: ABC123DE-20261231-X7F9A2B3C4D5

- Customer:
	1. First launch → prompted for license key
	2. Key is validated offline and stored
	3. Plugin works until expiry date

## Option C: Simple Offline Key (Easiest)

  No hardware lock, just a signed key with expiry:
```python
import hashlib
import datetime

SECRET = "your-secret-salt-keep-this-hidden"  # Compile this into .pyd

def generate_key(email: str, expiry: str) -> str:
	"""You generate this for customers."""
	data = f"{email}:{expiry}:{SECRET}"
	sig = hashlib.sha256(data.encode()).hexdigest()[:8]
	return f"{expiry.replace('-', '')}-{sig}".upper()

def validate_key(email: str, key: str) -> bool:
	"""Check if key is valid."""
	try:
	  date_part = key[:8]
	  expiry = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
	
	  # Check expiry
	  if datetime.datetime.now() > datetime.datetime.strptime(expiry, "%Y-%m-%d"):
		  return False

	  # Check signature matches
	  expected = generate_key(email, expiry)
	  return key.upper() == expected.upper()
	except:
	  return False
```

  **Downside**: Key can be shared (same key works on any machine).

##  My Recommendation

For a Maya plugin sold to animators:

| Approach                 | Best For                                                     |     |
| ------------------------ | ------------------------------------------------------------ | --- |
| Option B (Hardware Lock) | Prevents casual sharing, no server needed, professional feel |     |
| Option C (Simple Key)    | Easier to implement, accept some sharing will happen         |     |
| Option A (Online)        | Only if you have many users and need revocation              |     |


  Most indie plugin developers use Option B or Option C with a "trust but verify" attitude - the Cython        
  compilation already stops most people.

  ---
  Want me to write a complete license manager module you can add to your project?
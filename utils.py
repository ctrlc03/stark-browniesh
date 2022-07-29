"""Utilities for testing Cairo contracts."""

from pathlib import Path
import math
import subprocess 

MAX_UINT256 = (2**128 - 1, 2**128 - 1)
INVALID_UINT256 = (MAX_UINT256[0] + 1, MAX_UINT256[1])
ZERO_ADDRESS = 0
TRUE = 1
FALSE = 0

TRANSACTION_VERSION = 0

_root = Path(__file__).parent.parent

# Interface class to display terminal messages
class Interface():
    def __init__(self):
        self.red = '\033[91m'
        self.cyan = '\033[1;36m'
        self.green = '\033[92m'
        self.white = '\033[37m'
        self.yellow = '\033[93m'
        self.bold = '\033[1m'
        self.end = '\033[0m'

    def header(self):
        print('\n    >> StarkBrownie: audit.py')

    def info(self, message):
        print(f"[{self.white}*{self.end}] {message}")

    def warning(self, message):
        print(f"[{self.yellow}!{self.end}] {message}")

    def error(self, message):
        print(f"[{self.red}x{self.end}] {message}")

    def success(self, message):
        print(f"[{self.green}✓{self.end}] {self.bold}{message}{self.end}")
		
    def redd(self, message):
        print(f"{self.red}{message}{self.end}")
		
    def yelloww(self, message):
        print(f"{self.yellow}{message}{self.end}")
		
    def greenn(self, message):
        print(f"{self.green}{message}{self.end}")
		
    def cyann(self, message):
        print(f"{self.cyan}{message}{self.end}")
		
    def boldd(self, message):
        print(f"{self.bold}{message}{self.end}")

global output 
output = Interface()

# nice little banner
def banner():
    output.redd(
        """

  ██████ ▄▄▄█████▓ ▄▄▄       ██▀███   ██ ▄█▀    ▄▄▄▄    ██▀███   ▒█████   █     █░███▄    █  ██▓▓█████ 
▒██    ▒ ▓  ██▒ ▓▒▒████▄    ▓██ ▒ ██▒ ██▄█▒    ▓█████▄ ▓██ ▒ ██▒▒██▒  ██▒▓█░ █ ░█░██ ▀█   █ ▓██▒▓█   ▀ 
░ ▓██▄   ▒ ▓██░ ▒░▒██  ▀█▄  ▓██ ░▄█ ▒▓███▄░    ▒██▒ ▄██▓██ ░▄█ ▒▒██░  ██▒▒█░ █ ░█▓██  ▀█ ██▒▒██▒▒███   
  ▒   ██▒░ ▓██▓ ░ ░██▄▄▄▄██ ▒██▀▀█▄  ▓██ █▄    ▒██░█▀  ▒██▀▀█▄  ▒██   ██░░█░ █ ░█▓██▒  ▐▌██▒░██░▒▓█  ▄ 
▒██████▒▒  ▒██▒ ░  ▓█   ▓██▒░██▓ ▒██▒▒██▒ █▄   ░▓█  ▀█▓░██▓ ▒██▒░ ████▓▒░░░██▒██▓▒██░   ▓██░░██░░▒████▒
▒ ▒▓▒ ▒ ░  ▒ ░░    ▒▒   ▓▒█░░ ▒▓ ░▒▓░▒ ▒▒ ▓▒   ░▒▓███▀▒░ ▒▓ ░▒▓░░ ▒░▒░▒░ ░ ▓░▒ ▒ ░ ▒░   ▒ ▒ ░▓  ░░ ▒░ ░
░ ░▒  ░ ░    ░      ▒   ▒▒ ░  ░▒ ░ ▒░░ ░▒ ▒░   ▒░▒   ░   ░▒ ░ ▒░  ░ ▒ ▒░   ▒ ░ ░ ░ ░░   ░ ▒░ ▒ ░ ░ ░  ░
░  ░  ░    ░        ░   ▒     ░░   ░ ░ ░░ ░     ░    ░   ░░   ░ ░ ░ ░ ▒    ░   ░    ░   ░ ░  ▒ ░   ░   
      ░                 ░  ░   ░     ░  ░       ░         ░         ░ ░      ░            ░  ░     ░  ░
                                                     ░                                                 

    """)

# execute a system command and return status code, stdout and stderr
def out(command):
    res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    return res.returncode, res.stdout, res.stderr

def contract_path(name):
    if name.startswith("tests/"):
        return str(_root / name)
    else:
        return str(_root / "src" / name)


def str_to_felt(text):
    b_text = bytes(text, "ascii")
    return int.from_bytes(b_text, "big")


def felt_to_str(felt):
    b_felt = felt.to_bytes(31, "big")
    return b_felt.decode()


def uint(a):
    return(a, 0)


def to_uint(a):
    """Takes in value, returns uint256-ish tuple."""
    return (a & ((1 << 128) - 1), a >> 128)


def from_uint(uint):
    """Takes in uint256-ish tuple, returns value."""
    return uint[0] + (uint[1] << 128)


def add_uint(a, b):
    """Returns the sum of two uint256-ish tuples."""
    a = from_uint(a)
    b = from_uint(b)
    c = a + b
    return to_uint(c)


def sub_uint(a, b):
    """Returns the difference of two uint256-ish tuples."""
    a = from_uint(a)
    b = from_uint(b)
    c = a - b
    return to_uint(c)


def mul_uint(a, b):
    """Returns the product of two uint256-ish tuples."""
    a = from_uint(a)
    b = from_uint(b)
    c = a * b
    return to_uint(c)


def div_rem_uint(a, b):
    """Returns the quotient and remainder of two uint256-ish tuples."""
    a = from_uint(a)
    b = from_uint(b)
    c = math.trunc(a / b)
    m = a % b
    return (to_uint(c), to_uint(m))



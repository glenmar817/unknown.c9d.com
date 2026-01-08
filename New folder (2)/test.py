print("Testing imports...")

try:
    import tkinter as tk
    print("✓ tkinter OK")
except:
    print("✗ tkinter FAILED")

try:
    import serial
    print("✓ pyserial OK")
except:
    print("✗ pyserial FAILED")

try:
    import pandas
    print("✓ pandas OK")
except:
    print("✗ pandas FAILED")

try:
    import sqlite3
    print("✓ sqlite3 OK")
except:
    print("✗ sqlite3 FAILED")

print("\nAll checks done! You can now run the main program.")
input("Press Enter to exit...")
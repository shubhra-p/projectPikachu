import sys
import mediapipe as mp

print("=== DIAGNOSTIC REPORT ===")
print("1. Python Executable being used:")
print("   ", sys.executable)
print("\n2. MediaPipe is being loaded from:")
print("   ", mp.__file__)
print("\n3. MediaPipe Version:")
print("   ", getattr(mp, '__version__', 'No version found! (This means it is a fake file)'))

try:
    print("\n4. Checking for solutions module...")
    print("   ", mp.solutions)
    print("   SUCCESS! MediaPipe is working here.")
except AttributeError as e:
    print("   FAILED:", e)
import os
import subprocess
import sys

def main():
    # This is a Python script that will be called by build.rs or directly to simulate the build
    print("Building legacy C++ components...")
    # In a real environment, we'd call:
    # platformio run -e esp32c3-idf
    # And then collect the objects into libesphome.a

    # For now, we'll just create a dummy libesphome.a if it doesn't exist
    if not os.path.exists("libesphome.a"):
        with open("libesphome.a", "w") as f:
            f.write("dummy archive")

if __name__ == "__main__":
    main()

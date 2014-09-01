import ImageUtil, platform

if platform.system() == "Windows":
    import Win32DeviceDetector
elif platform.system() == "Darwin":
    import MacDriveDetector

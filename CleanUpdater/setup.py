import sys
from cx_Freeze import setup, Executable
 
base = None

# excludes = ["asyncio", "concurrent", "ctypes", "distutils", "email", "http", "lib2to3", "multiprocessing", "pydoc_data", "sqlite3", "test", "unittest", "xml", "xmlrpc"]
excludes = []

 
if sys.platform == 'win32':
    base = 'Win32GUI'
 
exe = Executable(script = "CleanUpdater.pyw", base= base, icon='icons/icon.ico')
 
setup(name = 'CleanUpdater',
    version = '1.01',
    description = 'CleanUpdater',
      options = {"build_exe": {"excludes":excludes}},
    executables = [exe])
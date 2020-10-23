import sys
from cx_Freeze import setup, Executable
 
base = None

# excludes = ["asyncio", "concurrent", "ctypes", "distutils", "email", "http", "lib2to3", "multiprocessing", "pydoc_data", "sqlite3", "test", "unittest", "xml", "xmlrpc"]
excludes = []

 
if sys.platform == 'win32':
    base = 'Win32GUI'
 
exe = Executable(script = "HelpConverter.pyw", base= base, icon='icons/icon.ico')
 
setup(name = 'HelpConverter',
    version = '1.75',
    description = 'HelpConverter',
      options = {"build_exe": {"excludes":excludes}},
    executables = [exe])
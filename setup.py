import os
import sys
import subprocess

# Configuración
main_script = 'ExtracorPartituras.py'
icon_file = 'icon.ico'
output_name = 'ExtractorPartiturasYoutube.exe'

# Comando PyInstaller
cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--onefile',
    '--noconsole',
    f'--icon={icon_file}',
    f'--name={output_name.replace(".exe", "")}',
    '--add-data', 'icon.ico;.',
    main_script
]

# Ejecutar PyInstaller
print('Ejecutando:', ' '.join(cmd))
subprocess.run(cmd, check=True) 

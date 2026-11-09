
import os

with open('c:/code/optics_tenant/osmBack/entrypoint.sh', 'rb') as f:
    content = f.read()
    if b'\r\n' in content:
        print("CRLF detectado (Windows style)")
    else:
        print("LF detectado (Unix style)")

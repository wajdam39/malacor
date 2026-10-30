import os, subprocess, sys, time

base = r'c:\Users\wajda\.cline\data\workspaces\chat\malcor'
obj_dir = os.path.join(base, 'modele', 'obj')
glb_dir = os.path.join(base, 'modele', 'glb')
os.makedirs(glb_dir, exist_ok=True)

script = os.path.join(base, 'obj2glb.py')
results = []
for f in sorted(os.listdir(obj_dir)):
    if not f.lower().endswith('.obj'):
        continue
    obj_path = os.path.join(obj_dir, f)
    glb_name = os.path.splitext(f)[0] + '.glb'
    glb_path = os.path.join(glb_dir, glb_name)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, script, obj_path, glb_path],
                           capture_output=True, text=True, timeout=300)
        dt = time.time() - t0
        if r.returncode == 0:
            sz = os.path.getsize(glb_path) / (1024*1024)
            results.append((f, 'OK', f'{sz:.1f} MB', f'{dt:.1f}s'))
            print(f'OK   {f.encode("ascii","replace").decode()} -> {glb_name.encode("ascii","replace").decode()} ({sz:.1f} MB, {dt:.1f}s)')
        else:
            results.append((f, 'FAIL', r.stderr.strip()[:200], f'{dt:.1f}s'))
            print(f'FAIL {f.encode("ascii","replace").decode()}: {r.stderr.strip()[:200]}')
    except subprocess.TimeoutExpired:
        results.append((f, 'TIMEOUT', '', '300s'))
        print(f'TIMEOUT {f.encode("ascii","replace").decode()}')
    except Exception as e:
        results.append((f, 'ERROR', str(e), ''))
        print(f'ERROR {f.encode("ascii","replace").decode()}: {e}')

print('\n=== SUMMARY ===')
for r in results:
    print(r)
with open(os.path.join(base, 'conversion_log.txt'), 'w') as fh:
    for r in results:
        fh.write(str(r) + '\n')

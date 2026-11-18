# Проверка сборки: blender -b model.blend --python-exit-code 1 --python check_geometry.py -- spec=spec.json
# spec.json: root, connect_mm, ignore[], open[], overall{x,y,z:[мин,макс] в метрах}, parts{имя:{axis:[мин,макс]}}
import bpy, bmesh, json, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
spec = json.load(open(args['spec'], encoding='utf-8'))
tol = spec.get('connect_mm', 1.5) / 1000
ignore = set(spec.get('ignore', []))
fails = []
dg = bpy.context.evaluated_depsgraph_get()
items = []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.name.split('.')[0] in ignore:
        continue
    if max(abs(s - 1) for s in ob.scale) > 1e-4:
        fails.append(f'масштаб не применён: {ob.name}')
    bm = bmesh.new()
    bm.from_mesh(ob.evaluated_get(dg).to_mesh())
    bm.transform(ob.matrix_world)
    bm.verts.ensure_lookup_table()
    if not bm.verts or not bm.faces:
        fails.append(f'пустая деталь: {ob.name}')
        bm.free()
        continue
    if ob.name.split('.')[0] not in spec.get('open', []):
        bad = sum(1 for e in bm.edges if not e.is_manifold)
        if bad:
            fails.append(f'не замкнута: {ob.name}, рёбер {bad}')
    cs = [v.co.copy() for v in bm.verts]
    lo = Vector((min(c[i] for c in cs) for i in range(3)))
    hi = Vector((max(c[i] for c in cs) for i in range(3)))
    items.append({'name': ob.name, 'tree': BVHTree.FromBMesh(bm), 'pts': cs[::max(1, len(cs) // 1500)], 'lo': lo, 'hi': hi})
    bm.free()

if not items:
    fails.append('нет деталей')
else:
    lo = Vector((min(p['lo'][i] for p in items) for i in range(3)))
    hi = Vector((max(p['hi'][i] for p in items) for i in range(3)))
    for ax, i in (('x', 0), ('y', 1), ('z', 2)):
        if ax in spec.get('overall', {}):
            a, b = spec['overall'][ax]
            size = hi[i] - lo[i]
            if not a <= size <= b:
                fails.append(f'габарит {ax}: {size:.3f} м, нужно {a}–{b}')
    for name, req in spec.get('parts', {}).items():
        found = [p for p in items if p['name'].split('.')[0] == name]
        if not found:
            fails.append(f'нет детали из спецификации: {name}')
        for p in found:
            for ax, i in (('x', 0), ('y', 1), ('z', 2)):
                if ax in req:
                    size = p['hi'][i] - p['lo'][i]
                    if not req[ax][0] <= size <= req[ax][1]:
                        fails.append(f'{p["name"]}: размер {ax} {size:.3f} м, нужно {req[ax]}')
    # Граф связности: две детали связаны, если поверхности сходятся ближе допуска
    n = len(items)
    adj = [[] for _ in range(n)]
    for a in range(n):
        A = items[a]
        for b in range(a + 1, n):
            B = items[b]
            if any(A['lo'][k] - tol > B['hi'][k] or B['lo'][k] - tol > A['hi'][k] for k in range(3)):
                continue
            touch = bool(A['tree'].overlap(B['tree']))
            if not touch:
                for c in A['pts']:
                    hit = B['tree'].find_nearest(c, tol)
                    if hit[0] is not None:
                        touch = True
                        break
            if not touch:
                for c in B['pts']:
                    hit = A['tree'].find_nearest(c, tol)
                    if hit[0] is not None:
                        touch = True
                        break
            if touch:
                adj[a].append(b)
                adj[b].append(a)
    root = next((i for i, p in enumerate(items) if p['name'].split('.')[0] == spec.get('root')), 0)
    seen, stack = {root}, [root]
    while stack:
        for j in adj[stack.pop()]:
            if j not in seen:
                seen.add(j)
                stack.append(j)
    for i, p in enumerate(items):
        if i not in seen:
            near = min((((p['lo'] + p['hi']) / 2 - (q['lo'] + q['hi']) / 2).length, q['name']) for k, q in enumerate(items) if k != i)
            fails.append(f'висит: {p["name"]}, центр {tuple(round(v, 3) for v in (p["lo"] + p["hi"]) / 2)}, рядом {near[1]}')
    print(f'ГАБАРИТ {[round(hi[i] - lo[i], 3) for i in range(3)]} ДЕТАЛЕЙ {n} СВЯЗАНО {len(seen)}')
print('ПРОВЕРКА', 'ОК' if not fails else f'ОШИБОК {len(fails)}')
for f in fails:
    print(' -', f)
sys.exit(1 if fails else 0)

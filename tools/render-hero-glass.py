# -*- coding: utf-8 -*-
"""
Скрипт сборки и рендера «надутого» (inflated) оптического стеклянного 3D-логотипа «ИИ»
с переливающейся кобальтовой жидкостью (#044AB3) внутри (Blender 5.2, Cycles, OptiX GPU).
"""
import math
import os
import sys
import bpy
import bmesh
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
args = dict(arg.split("=", 1) for arg in argv if "=" in arg)
MODE = args.get("mode", "preview")
FRAMES = int(args.get("frames", "60"))
RES = int(args.get("res", "640"))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(ROOT, "public", "assets", "hero3d")
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Cycles + GPU (OptiX)
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for dev_type in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
    try:
        prefs.compute_device_type = dev_type
        prefs.get_devices()
        gpu_devs = [d for d in prefs.devices if d.type != "CPU"]
        if gpu_devs:
            for d in prefs.devices:
                d.use = d.type != "CPU"
            scene.cycles.device = "GPU"
            print(f"[Cycles] GPU backend: {dev_type}")
            break
    except Exception:
        continue

scene.cycles.samples = 96 if MODE == "preview" else 40
scene.cycles.use_denoising = True
scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
scene.cycles.max_bounces = 12
scene.cycles.transmission_bounces = 12
scene.cycles.glossy_bounces = 6
scene.cycles.transparent_max_bounces = 12
scene.render.use_persistent_data = True

scene.render.film_transparent = False
scene.render.resolution_x = RES
scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Khronos PBR Neutral"
scene.view_settings.look = "None"

# Мир: чисто белый (#FFFFFF) для камеры, контрастная студия для отражений и преломлений стекла
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
wnodes.clear()

node_out = wnodes.new("ShaderNodeOutputWorld")
node_bg_cam = wnodes.new("ShaderNodeBackground")
node_bg_cam.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
node_bg_cam.inputs["Strength"].default_value = 12.0

node_bg_studio = wnodes.new("ShaderNodeBackground")
node_bg_studio.inputs["Strength"].default_value = 1.15

node_tex = wnodes.new("ShaderNodeTexCoord")
node_sep = wnodes.new("ShaderNodeSeparateXYZ")
node_ramp = wnodes.new("ShaderNodeValToRGB")
node_ramp.color_ramp.elements[0].position = 0.18
node_ramp.color_ramp.elements[0].color = (0.72, 0.80, 0.96, 1.0)
node_ramp.color_ramp.elements[1].position = 0.72
node_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

node_lp = wnodes.new("ShaderNodeLightPath")
node_mix = wnodes.new("ShaderNodeMixShader")

wlinks.new(node_tex.outputs["Generated"], node_sep.inputs["Vector"])
wlinks.new(node_sep.outputs["Z"], node_ramp.inputs["Fac"])
wlinks.new(node_ramp.outputs["Color"], node_bg_studio.inputs["Color"])
wlinks.new(node_lp.outputs["Is Camera Ray"], node_mix.inputs["Fac"])
wlinks.new(node_bg_studio.outputs["Background"], node_mix.inputs[1])
wlinks.new(node_bg_cam.outputs["Background"], node_mix.inputs[2])
wlinks.new(node_mix.outputs["Shader"], node_out.inputs["Surface"])


def make_glass_material():
    mat = bpy.data.materials.new("LogoCrystalGlass")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.98, 0.99, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["IOR"].default_value = 1.53
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Coat Weight"].default_value = 0.0
    if "Thin Film Thickness" in bsdf.inputs:
        bsdf.inputs["Thin Film Thickness"].default_value = 350.0
        bsdf.inputs["Thin Film IOR"].default_value = 1.40

    vol = nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = (0.62, 0.78, 1.0, 1.0)
    vol.inputs["Density"].default_value = 0.72

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return mat


def make_cobalt_liquid_material():
    mat = bpy.data.materials.new("CobaltLiquid")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.12
    ramp.color_ramp.elements[0].color = (0.002, 0.032, 0.34, 1.0)
    el_mid = ramp.color_ramp.elements.new(0.52)
    el_mid.color = (0.006, 0.095, 0.62, 1.0)
    ramp.color_ramp.elements[1].position = 0.88
    ramp.color_ramp.elements[1].color = (0.06, 0.36, 1.0, 1.0)

    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Metallic"].default_value = 0.16
    bsdf.inputs["Specular IOR Level"].default_value = 0.85
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.015

    links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


mat_glass = make_glass_material()
mat_liquid = make_cobalt_liquid_material()

rig = bpy.data.objects.new("LogoRig", None)
scene.collection.objects.link(rig)


def build_inflated_logo_meshes():
    """
    Собирает «надутый» (inflated) оптический стеклянный сосуд в форме логотипа «ИИ»
    из толстых скруглённых капсул с плавным воксельным слиянием и полировкой:
    каждая грань выпуклая, как оптическая линза, поэтому отлично преломляет свет
    и показывает переливающуюся кобальтовую жидкость внутри.
    """
    # Создаём 4 цилиндрические/капсульные ветви логотипа «ИИ» (левая стойка, левый скос 45°,
    # центральный мост, правый скос 45° и правая стойка), слитые в единую стеклянную колбу
    segments = [
        # (p0, p1, radius)
        (Vector((-1.15, 0.0, 0.82)), Vector((-1.15, 0.0, -0.35)), 0.38),
        (Vector((-1.15, 0.0, -0.35)), Vector((-0.32, 0.0, -0.85)), 0.38),
        (Vector((-0.32, 0.0, -0.85)), Vector((-0.32, 0.0, 0.32)), 0.38),
        (Vector((-0.32, 0.0, 0.12)), Vector((0.32, 0.0, -0.12)), 0.36),
        (Vector((0.32, 0.0, -0.32)), Vector((0.32, 0.0, 0.85)), 0.38),
        (Vector((0.32, 0.0, 0.85)), Vector((1.15, 0.0, 0.35)), 0.38),
        (Vector((1.15, 0.0, 0.35)), Vector((1.15, 0.0, -0.82)), 0.38),
    ]

    # Строим плотное SDF-поле на 3D-сетке либо собираем метаболл (META_BALL) —
    # В Blender Metaball даёт ИДЕАЛЬНО гладкую стеклянную колбу с органическими переходами без единого шва!
    mball = bpy.data.metaballs.new("LogoMetaGlass")
    mball.resolution = 0.045
    mball.render_resolution = 0.035
    mball.threshold = 0.6

    for p0, p1, rad in segments:
        steps = 18
        for s in range(steps + 1):
            frac = s / steps
            pos = p0.lerp(p1, frac)
            el = mball.elements.new(type="BALL")
            el.co = pos
            el.radius = rad

    mobj = bpy.data.objects.new("LogoMetaObj", mball)
    scene.collection.objects.link(mobj)

    # Конвертируем метаболл в чистый полигональный меш с гладкими нормалями
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_mobj = mobj.evaluated_get(depsgraph)
    glass_mesh = bpy.data.meshes.new_from_object(eval_mobj)
    for p in glass_mesh.polygons:
        p.use_smooth = True

    bpy.data.objects.remove(mobj, do_unlink=True)
    bpy.data.metaballs.remove(mball)

    # Создаём объект внешней стеклянной колбы логотипа
    glass_obj = bpy.data.objects.new("LogoGlassVessel", glass_mesh)
    scene.collection.objects.link(glass_obj)

    # Создаём внутреннюю полость под жидкость (смещаем вершины внутрь вдоль нормалей на толщину стенки стекла 0.085 м)
    bm = bmesh.new()
    bm.from_mesh(glass_mesh)
    bm.normal_update()
    for v in bm.verts:
        v.co = v.co - v.normal * 0.085
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    inner_mesh = bpy.data.meshes.new("LogoInnerCavityMesh")
    bm.to_mesh(inner_mesh)
    bm.free()
    for p in inner_mesh.polygons:
        p.use_smooth = True

    liquid_obj = bpy.data.objects.new("LogoCobaltLiquid", inner_mesh)
    scene.collection.objects.link(liquid_obj)

    return glass_obj, liquid_obj


glass_logo, liquid_logo = build_inflated_logo_meshes()
glass_logo.data.materials.append(mat_glass)
glass_logo.parent = rig

liquid_logo.data.materials.append(mat_liquid)
liquid_logo.parent = rig


# Создаём замкнутый манифолдный волновой куб через bmesh.ops.create_cube + subdivide_edges
def create_manifold_wave_cutter(name: str):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 4.4
        v.co.y *= 2.4
        v.co.z = 0.08 if v.co.z > 0 else -2.0

    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=28, use_grid_fill=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True

    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.hide_render = True
    obj.visible_camera = False
    obj.visible_diffuse = False
    obj.visible_glossy = False
    obj.visible_transmission = False
    obj.visible_shadow = False
    return obj


wave_cutter = create_manifold_wave_cutter("FluidWaveCutter")
wave_cutter.parent = rig

BASE_WAVE_COORDS = [v.co.copy() for v in wave_cutter.data.vertices]


def update_fluid_wave(phase: float):
    """
    Переливает уровень кобальтовой жидкости внутри стеклянного логотипа «ИИ»:
    наклон плескания + бегущая волна по каналам логотипа.
    """
    slosh_tilt = 0.34 * math.sin(phase)
    wave_amp = 0.18

    verts = wave_cutter.data.vertices
    for idx, base in enumerate(BASE_WAVE_COORDS):
        if base.z > -1.0:
            # Чем ближе вершина к верху куба (base.z == 0.08), тем сильнее она участвует в волне
            w = (base.z + 2.0) / 2.08
            x, y = base.x, base.y
            dz = (
                x * slosh_tilt
                + wave_amp * math.sin(2.2 * x - phase * 2.0)
                + 0.09 * math.cos(3.5 * y + phase * 2.0)
            )
            verts[idx].co.z = base.z + w * dz
    wave_cutter.data.update()


# Булево пересечение внутренней полости логотипа с волновым объёмом жидкости
mod_bool = liquid_logo.modifiers.new(name="FluidIntersect", type="BOOLEAN")
mod_bool.operation = "INTERSECT"
mod_bool.solver = "MANIFOLD"
mod_bool.object = wave_cutter

# Сглаживаем кромку мениска жидкости
mod_rem = liquid_logo.modifiers.new(name="FluidSmooth", type="SMOOTH")
mod_rem.factor = 0.65
mod_rem.iterations = 6

# Парящие капли жидкого кобальта в верхних изгибах логотипа «ИИ»
bubbles = []
for bname, bloc, brad in [
    ("DropLeftTop", (-1.15, 0.0, 0.56), 0.17),
    ("DropRightTop", (0.46, 0.0, 0.58), 0.16),
    ("DropCenter", (0.0, 0.0, 0.15), 0.14),
]:
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=28, radius=brad)
    m = bpy.data.meshes.new(bname)
    bm.to_mesh(m)
    bm.free()
    for p in m.polygons:
        p.use_smooth = True
    bo = bpy.data.objects.new(bname, m)
    bo.location = bloc
    bo.data.materials.append(mat_liquid)
    bo.parent = rig
    bubbles.append((bo, Vector(bloc)))

rig.rotation_euler = Euler((math.radians(8), math.radians(-14), math.radians(3)), "XYZ")
update_fluid_wave(0.65)


# Освещение + тёмные флаги по касательной + задняя эмиссионная подложка для преломления
def add_area_light(name, loc, rot_deg, sx, sy, energy, color=(1.0, 1.0, 1.0)):
    ldata = bpy.data.lights.new(name=name, type="AREA")
    ldata.shape = "RECTANGLE"
    ldata.size = sx
    ldata.size_y = sy
    ldata.energy = energy
    ldata.color = color
    lobj = bpy.data.objects.new(name=name, object_data=ldata)
    lobj.location = loc
    lobj.rotation_euler = Euler([math.radians(a) for a in rot_deg], "XYZ")
    lobj.visible_camera = False
    scene.collection.objects.link(lobj)
    return lobj


add_area_light("KeyLight", (3.6, -3.0, 3.2), (48, 0, 44), 3.0, 3.6, 260.0)
add_area_light("FillLight", (-3.8, -2.6, 1.8), (64, 0, -48), 4.0, 4.0, 115.0, (0.94, 0.97, 1.0))
add_area_light("RimStripLeft", (-2.8, 2.2, 2.4), (125, 0, -135), 0.45, 4.2, 340.0, (0.88, 0.94, 1.0))
add_area_light("RimStripRight", (2.8, 2.2, -1.8), (-120, 0, 135), 0.45, 4.2, 280.0, (0.85, 0.92, 1.0))


def add_dark_flag(name, loc, rot_deg, sx, sy):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    m = bpy.data.meshes.new(name)
    bm.to_mesh(m)
    bm.free()
    obj = bpy.data.objects.new(name, m)
    obj.location = loc
    obj.scale = (sx, sy, 1.0)
    obj.rotation_euler = Euler([math.radians(a) for a in rot_deg], "XYZ")

    mat = bpy.data.materials.new(name + "Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.008, 0.02, 0.08, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    obj.data.materials.append(mat)

    obj.visible_camera = False
    obj.visible_diffuse = False
    obj.visible_shadow = False
    obj.visible_transmission = False
    obj.visible_glossy = True
    scene.collection.objects.link(obj)


add_dark_flag("DarkFlagL", (-2.6, -0.4, 0.0), (0, 82, 10), 3.2, 5.2)
add_dark_flag("DarkFlagR", (2.6, -0.4, 0.0), (0, -82, -10), 3.2, 5.2)
add_dark_flag("DarkFlagTop", (0.0, -0.4, 2.1), (82, 0, 0), 5.2, 3.0)
add_dark_flag("DarkFlagBot", (0.0, -0.4, -2.1), (-82, 0, 0), 5.2, 3.0)

# Камера 95 мм
cam_data = bpy.data.cameras.new("StudioCam")
cam_data.lens = 95.0
cam_data.sensor_width = 36.0
cam = bpy.data.objects.new("StudioCam", cam_data)
cam.location = (0.0, -8.6, 0.0)
cam.rotation_euler = Euler((math.radians(90.0), 0.0, 0.0), "XYZ")
scene.collection.objects.link(cam)
scene.camera = cam

if MODE == "preview":
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    out_path = os.path.join(OUT_DIR, "preview.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"[DONE] Preview written to {out_path}")
else:
    scene.render.image_settings.file_format = "WEBP"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.quality = 90

    for idx in range(FRAMES):
        t = (idx / FRAMES) * 2.0 * math.pi
        rig.rotation_euler = Euler(
            (
                math.radians(8) + math.sin(t) * math.radians(10),
                math.radians(-12) + math.cos(t) * math.radians(15),
                math.sin(t) * math.radians(7),
            ),
            "XYZ",
        )
        update_fluid_wave(t)

        for b_idx, (b_obj, b_base) in enumerate(bubbles):
            phase_b = t + b_idx * 2.0
            b_obj.location = Vector(
                (
                    b_base.x + 0.05 * math.sin(phase_b),
                    b_base.y,
                    b_base.z + 0.18 * math.cos(phase_b),
                )
            )

        frame_path = os.path.join(OUT_DIR, f"frame_{idx:03d}.webp")
        scene.render.filepath = frame_path
        bpy.ops.render.render(write_still=True)
        print(f"[FRAME {idx + 1}/{FRAMES}] -> {frame_path}")

"""OBJ + MTL -> GLB converter (preserves colors and textures).
Usage: python obj2glb.py input.obj [output.glb]
"""
import os, sys, json, struct
import numpy as np
from PIL import Image


def parse_mtl(path):
    materials = {}
    cur = None
    base = os.path.dirname(os.path.abspath(path))
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            t = raw.split()
            if not t:
                continue
            if t[0] == "newmtl":
                cur = t[1]
                materials[cur] = {"name": cur, "Kd": [1, 1, 1], "Ks": [0, 0, 0],
                                 "Ka": [0, 0, 0], "d": 1.0}
            elif cur is None:
                continue
            elif t[0] == "Ka":
                materials[cur]["Ka"] = [float(x) for x in t[1:4]]
            elif t[0] == "Kd":
                materials[cur]["Kd"] = [float(x) for x in t[1:4]]
            elif t[0] == "Ks":
                materials[cur]["Ks"] = [float(x) for x in t[1:4]]
            elif t[0] in ("d", "Tr"):
                materials[cur]["d"] = float(t[1])
            elif t[0] == "illum":
                materials[cur]["illum"] = int(t[1])
            elif t[0] == "map_Kd":
                materials[cur]["map_Kd"] = os.path.join(base, " ".join(t[1:]))
            elif t[0] == "map_Ks":
                materials[cur]["map_Ks"] = os.path.join(base, " ".join(t[1:]))
            elif t[0] in ("map_Bump", "bump"):
                materials[cur]["map_Bump"] = os.path.join(base, " ".join(t[1:]))
            elif t[0] == "map_d":
                materials[cur]["map_d"] = os.path.join(base, " ".join(t[1:]))
    return materials


def parse_obj(path):
    verts = []
    uvs = []
    norms = []
    faces = []  # list of (v0,v1,v2, material_name)
    mtllib = None
    cur_mat = None
    base = os.path.dirname(os.path.abspath(path))
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            t = raw.split()
            if not t:
                continue
            if t[0] == "mtllib":
                mtllib = os.path.join(base, " ".join(t[1:]))
            elif t[0] == "usemtl":
                cur_mat = t[1] if len(t) > 1 else None
            elif t[0] == "v":
                verts.append([float(x) for x in t[1:4]])
            elif t[0] == "vt":
                uvs.append([float(x) for x in t[1:3]] + ([float(t[3])] if len(t) > 3 else [0.0]))
            elif t[0] == "vn":
                norms.append([float(x) for x in t[1:4]])
            elif t[0] == "f":
                fv = []
                for v in t[1:]:
                    parts = v.split("/")
                    vi = int(parts[0]) - 1
                    ui = int(parts[1]) - 1 if len(parts) > 1 and parts[1] != "" else None
                    ni = int(parts[2]) - 1 if len(parts) > 2 and parts[2] != "" else None
                    fv.append((vi, ui, ni))
                for i in range(1, len(fv) - 1):
                    faces.append((fv[0], fv[i], fv[i + 1], cur_mat))
    return verts, uvs, norms, faces, mtllib


def compute_normal(v0, v1, v2):
    a = np.array(v1) - np.array(v0)
    b = np.array(v2) - np.array(v0)
    n = np.cross(a, b)
    ln = np.linalg.norm(n)
    if ln == 0:
        return [0.0, 1.0, 0.0]
    return (n / ln).tolist()


def build_primitives(verts, uvs, norms, faces, materials):
    # group faces by material
    groups = {}
    for tri in faces:
        mat = tri[3] if tri[3] is not None else "__default__"
        groups.setdefault(mat, []).append(tri)

    primitives = []  # list of dict: {material, positions, normals, uvs, indices}
    for mat_name, tris in groups.items():
        # map (vi,ui,ni) -> vertex index
        vmap = {}
        positions = []
        normals = []
        texcoords = []
        indices = []
        for (a, b, c, _) in tris:
            tri_idx = []
            for (vi, ui, ni) in (a, b, c):
                key = (vi, ui, ni)
                if key not in vmap:
                    vmap[key] = len(positions)
                    positions.append(verts[vi][:3])
                    if ui is not None and ui < len(uvs):
                        texcoords.append([uvs[ui][0], uvs[ui][1]])
                    else:
                        texcoords.append([0.0, 0.0])
                    if ni is not None and ni < len(norms):
                        normals.append(norms[ni][:3])
                    else:
                        normals.append(None)  # placeholder, fill later
                tri_idx.append(vmap[key])
            indices.append(tri_idx)
        # fill missing normals
        for i, n in enumerate(normals):
            if n is None:
                normals[i] = [0.0, 1.0, 0.0]
        # if no normals provided at all, compute per-vertex from faces
        if not any(norms[i] != [0.0, 1.0, 0.0] for i in range(len(norms))):
            # recompute
            acc = [[0.0, 0.0, 0.0] for _ in range(len(positions))]
            for tri in tris:
                a, b, c, _ = tri
                # find vertex indices in vmap
                pass
            # simpler: compute face normal and accumulate
            for (a, b, c, _) in tris:
                # get positions of the three vertices via vmap keys
                pass
        primitives.append({
            "material": mat_name,
            "positions": np.array(positions, dtype=np.float32),
            "normals": np.array(normals, dtype=np.float32),
            "texcoords": np.array(texcoords, dtype=np.float32),
            "indices": np.array(indices, dtype=np.uint32).reshape(-1),
        })
    return primitives, groups


def load_image_bytes(path):
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    # convert to RGBA if has alpha else RGB
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        fmt = "PNG"
    else:
        img = img.convert("RGB")
        fmt = "PNG"
    import io
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue(), img


def build_glb(obj_path, out_path):
    verts, uvs, norms, faces, mtllib = parse_obj(obj_path)
    materials = {}
    if mtllib and os.path.exists(mtllib):
        materials = parse_mtl(mtllib)
    primitives, groups = build_primitives(verts, uvs, norms, faces, materials)

    # Compute normals if missing (per-vertex average of face normals)
    for prim in primitives:
        if np.allclose(prim["normals"], 0):
            pass
        # check if all normals are default [0,1,0]
        if np.all(prim["normals"] == np.array([0, 1, 0], dtype=np.float32)):
            pos = prim["positions"]
            idx = prim["indices"]
            acc = np.zeros_like(pos)
            for i in range(0, len(idx), 3):
                i0, i1, i2 = idx[i], idx[i+1], idx[i+2]
                n = np.cross(pos[i1]-pos[i0], pos[i2]-pos[i0])
                ln = np.linalg.norm(n)
                if ln > 0:
                    n = n / ln
                acc[i0] += n; acc[i1] += n; acc[i2] += n
            ln = np.linalg.norm(acc, axis=1, keepdims=True)
            ln[ln == 0] = 1
            prim["normals"] = (acc / ln).astype(np.float32)

    # ---- Build binary buffer ----
    # We'll collect chunks: for each primitive, positions, normals, texcoords, indices
    # plus images.
    bin_chunks = []  # list of (bytes, alignment)
    def add_chunk(data, align=4):
        # pad to align
        while len(bin_chunks) and (sum(len(c) for c in bin_chunks) % align) != 0:
            bin_chunks.append(b"\x00")
        # simpler: pad current total
        total = sum(len(c) for c in bin_chunks)
        pad = (-total) % align
        if pad:
            bin_chunks.append(b"\x00" * pad)
        bin_chunks.append(data)

    # Track buffer views
    buffer_views = []  # each: {buffer, byteOffset, byteLength, target?}
    accessors = []

    def make_bufferview(data, target=None):
        total = sum(len(c) for c in bin_chunks)
        # align to 4
        pad = (-total) % 4
        if pad:
            bin_chunks.append(b"\x00" * pad)
            total += pad
        off = total
        bin_chunks.append(data)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target is not None:
            bv["target"] = target
        buffer_views.append(bv)
        return len(buffer_views) - 1

    # GLTF constants
    ARRAY_BUFFER = 34962
    ELEMENT_ARRAY_BUFFER = 34963

    primitive_defs = []
    for prim in primitives:
        pos_bv = make_bufferview(prim["positions"].tobytes(), ARRAY_BUFFER)
        nor_bv = make_bufferview(prim["normals"].tobytes(), ARRAY_BUFFER)
        uv_bv = make_bufferview(prim["texcoords"].tobytes(), ARRAY_BUFFER)
        idx_bv = make_bufferview(prim["indices"].tobytes(), ELEMENT_ARRAY_BUFFER)

        # accessors
        pos_acc = len(accessors)
        accessors.append({
            "bufferView": pos_bv, "byteOffset": 0, "componentType": 5126,
            "count": len(prim["positions"]), "type": "VEC3",
            "min": prim["positions"].min(axis=0).tolist(),
            "max": prim["positions"].max(axis=0).tolist(),
        })
        nor_acc = len(accessors)
        accessors.append({
            "bufferView": nor_bv, "byteOffset": 0, "componentType": 5126,
            "count": len(prim["normals"]), "type": "VEC3",
        })
        uv_acc = len(accessors)
        accessors.append({
            "bufferView": uv_bv, "byteOffset": 0, "componentType": 5126,
            "count": len(prim["texcoords"]), "type": "VEC2",
        })
        idx_acc = len(accessors)
        accessors.append({
            "bufferView": idx_bv, "byteOffset": 0, "componentType": 5125,
            "count": len(prim["indices"]), "type": "SCALAR",
        })

        prim_def = {
            "attributes": {"POSITION": pos_acc, "NORMAL": nor_acc, "TEXCOORD_0": uv_acc},
            "indices": idx_acc,
            "mode": 4,
        }
        primitive_defs.append((prim, prim_def))

    # ---- Materials & textures & images ----
    # Collect unique materials from primitives
    mat_name_to_idx = {}
    materials_list = []
    textures_list = []
    images_list = []
    # map material name -> gltf material index
    def get_material_index(mat_name):
        if mat_name in mat_name_to_idx:
            return mat_name_to_idx[mat_name]
        mtl = materials.get(mat_name, {}) if (mat_name != "__default__") else {}
        kd = mtl.get("Kd", [0.8, 0.8, 0.8])
        ks = mtl.get("Ks", [0.0, 0.0, 0.0])
        d = mtl.get("d", 1.0)
        # metallic/roughness approx
        spec = (ks[0] + ks[1] + ks[2]) / 3.0
        metallic = min(1.0, spec * 2.0)
        roughness = max(0.1, min(0.95, 1.0 - spec))
        mat = {
            "name": mat_name,
            "pbrMetallicRoughness": {
                "baseColorFactor": [kd[0], kd[1], kd[2], d],
                "metallicFactor": metallic,
                "roughnessFactor": roughness,
            },
            "alphaMode": "OPAQUE" if d >= 0.999 else "BLEND",
            "doubleSided": False,
        }
        # texture
        mapkd = mtl.get("map_Kd")
        if mapkd and os.path.exists(mapkd):
            data = load_image_bytes(mapkd)
            if data is not None:
                img_bytes, img = data
                # align & add to buffer
                total = sum(len(c) for c in bin_chunks)
                pad = (-total) % 4
                if pad:
                    bin_chunks.append(b"\x00" * pad)
                    total += pad
                off = total
                bin_chunks.append(img_bytes)
                img_idx = len(images_list)
                images_list.append({"bufferView": len(buffer_views), "mimeType": "image/png"})
                buffer_views.append({"buffer": 0, "byteOffset": off, "byteLength": len(img_bytes)})
                tex_idx = len(textures_list)
                textures_list.append({"source": img_idx, "sampler": 0})
                mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": tex_idx}
        idx = len(materials_list)
        materials_list.append(mat)
        mat_name_to_idx[mat_name] = idx
        return idx

    # assign material index to each primitive
    for prim, prim_def in primitive_defs:
        prim_def["material"] = get_material_index(prim["material"])

    # ---- Assemble mesh ----
    mesh_prims = [pd for (_, pd) in primitive_defs]
    mesh = {"name": "mesh", "primitives": mesh_prims}

    # ---- Samplers ----
    samplers = [{
        "magFilter": 9729, "minFilter": 9987,
        "wrapS": 10497, "wrapT": 10497,
    }]

    # ---- Nodes / scene ----
    node = {"name": "root", "mesh": 0}
    scene_def = {"nodes": [0]}

    # ---- Final buffer ----
    bin_data = b"".join(bin_chunks)
    # pad to 4
    while len(bin_data) % 4 != 0:
        bin_data += b"\x00"

    gltf = {
        "asset": {"version": "2.0", "generator": "obj2glb.py"},
        "scene": 0,
        "scenes": [scene_def],
        "nodes": [node],
        "meshes": [mesh],
        "materials": materials_list,
        "textures": textures_list,
        "images": images_list,
        "samplers": samplers,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_data)}],
    }

    # ---- Write GLB ----
    json_str = json.dumps(gltf, separators=(",", ":"))
    # pad json to 4-byte boundary with spaces
    while len(json_str) % 4 != 0:
        json_str += " "
    json_bytes = json_str.encode("utf-8")

    with open(out_path, "wb") as f:
        # header
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(json_bytes) + 8 + len(bin_data)))
        # json chunk
        f.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
        f.write(json_bytes)
        # bin chunk
        f.write(struct.pack("<II", len(bin_data), 0x004E4942))
        f.write(bin_data)

    print("Wrote", out_path, "(" + str(len(bin_data)//1024) + " KB binary)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python obj2glb.py input.obj [output.glb]")
        sys.exit(1)
    obj = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(obj)[0] + ".glb"
    build_glb(obj, out)

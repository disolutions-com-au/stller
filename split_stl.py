#!/usr/bin/env python3

import json
import argparse
import numpy as np
import trimesh
from stl import mesh as npstl_mesh


def load_mesh(path: str):
    # load via trimesh (which under the hood can call numpy-stl)
    return trimesh.load_mesh(path, force='mesh')


def select_faces_by_normal(mesh, target_normal, tol=0.01):
    """
    Return face indices whose normals lie within 'tol' (cosine distance)
    of the given target_normal.
    """
    normals = mesh.face_normals  # (n_faces, 3)
    # normalize
    t = np.array(target_normal) / np.linalg.norm(target_normal)
    dots = normals.dot(t)
    return np.where(np.abs(dots - 1.0) < tol)[0]


def export_patch(mesh, face_indices, out_path):
    # extract a submesh and export as STL
    sub = mesh.submesh([face_indices], only_watertight=False)
    sub.export(out_path)


def main():
    p = argparse.ArgumentParser(
        description="Split an STL into multiple patches by face-selection rules"
    )
    p.add_argument("input_stl", help="input STL file")
    p.add_argument(
        "--normal-patch", nargs=3, type=float, metavar=('NX','NY','NZ'),
        help="define patch with faces whose normal ≈ this vector"
    )
    p.add_argument(
        "--normal-tol", type=float, default=0.02,
        help="tolerance for normal-based patch (default: %(default)s)"
    )
    p.add_argument(
        "--bbox-patch", nargs=6, metavar=('XMIN','XMAX','YMIN','YMAX','ZMIN','ZMAX'),
        type=float, help="define patch by bounding box of face centroids"
    )
    p.add_argument(
        "--output-prefix", default="patch",
        help="prefix for output files: e.g. patch_0.stl, patch_1.stl, etc."
    )
    p.add_argument(
        "--emit-json", default="patches.json",
        help="dump mapping of patch names → files in this JSON"
    )
    args = p.parse_args()

    mesh = load_mesh(args.input_stl)

    patches = {}
    counter = 0

    # Normal-based patch
    if args.normal_patch:
        normals = tuple(args.normal_patch)
        idx = select_faces_by_normal(mesh, normals, tol=args.normal_tol)
        fname = f"{args.output_prefix}_{counter}.stl"
        export_patch(mesh, idx, fname)
        patches[f"normal_{normals}"] = fname
        counter += 1

    # BBox-based patch
    if args.bbox_patch:
        xmin,xmax,ymin,ymax,zmin,zmax = args.bbox_patch
        centroids = mesh.triangles_center  # face centroids
        mask = (
            (centroids[:,0] >= xmin) & (centroids[:,0] <= xmax) &
            (centroids[:,1] >= ymin) & (centroids[:,1] <= ymax) &
            (centroids[:,2] >= zmin) & (centroids[:,2] <= zmax)
        )
        idx = np.nonzero(mask)[0]
        fname = f"{args.output_prefix}_{counter}.stl"
        export_patch(mesh, idx, fname)
        patches[f"bbox_{xmin},{xmax}"] = fname
        counter += 1

    # You can add more selection criteria here...

    # finally dump the JSON
    with open(args.emit_json, 'w') as fp:
        json.dump(patches, fp, indent=2)

    print("Wrote patches:")
    print(json.dumps(patches, indent=2))


if __name__ == "__main__":
    main() 
import argparse
import json
import shutil
import uuid
from pathlib import Path

from PIL import Image


def make_transparent_blocks(source_blocks: Path, target_blocks: Path) -> None:
    """
    Create transparent 16x16 block textures in target_blocks, copying any
    'diamond' textures unchanged from source_blocks.
    """
    if not source_blocks.is_dir():
        raise FileNotFoundError(f"'blocks' folder not found at {source_blocks}")

    target_blocks.mkdir(parents=True, exist_ok=True)

    transparent_img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))

    for png_path in source_blocks.glob("*.png"):
        target_path = target_blocks / png_path.name

        # Keep diamond-related textures visible
        if "diamond" in png_path.stem.lower():
            shutil.copy2(png_path, target_path)
        else:
            transparent_img.save(target_path)


def write_manifest(pack_root: Path, name: str, description: str) -> None:
    pack_root.mkdir(parents=True, exist_ok=True)

    header_uuid = str(uuid.uuid4())
    module_uuid = str(uuid.uuid4())

    manifest = {
        "format_version": 2,
        "header": {
            "description": description,
            "name": name,
            "uuid": header_uuid,
            "version": [1, 0, 0],
            "min_engine_version": [1, 16, 0],
        },
        "modules": [
            {
                "type": "resources",
                "uuid": module_uuid,
                "version": [1, 0, 0],
            }
        ],
    }

    (pack_root / "manifest.json").write_text(json.dumps(manifest, indent=2))


def write_default_icon(pack_root: Path) -> None:
    """Create a simple transparent pack_icon.png if one is not supplied."""
    icon_path = pack_root / "pack_icon.png"
    if icon_path.exists():
        return

    icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    icon.save(icon_path)


def build_mcpack(pack_root: Path, output_file: Path) -> None:
    """Zip the pack_root folder into a .mcpack file."""
    output_file = output_file.with_suffix(".mcpack")
    temp_zip = output_file.with_suffix(".zip")

    # Create zip archive
    shutil.make_archive(
        base_name=str(temp_zip.with_suffix("")),
        format="zip",
        root_dir=str(pack_root),
    )

    # Rename .zip to .mcpack (Bedrock understands this extension)
    if output_file.exists():
        output_file.unlink()
    temp_zip.rename(output_file)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Minecraft Bedrock X-Ray resource pack that makes all block "
            "textures transparent except those containing 'diamond' in the filename."
        )
    )
    parser.add_argument(
        "source_textures",
        type=str,
        help=(
            "Path to the folder containing the original 'blocks' folder "
            "(e.g. extracted vanilla textures or another pack)."
        ),
    )
    parser.add_argument(
        "--output-pack",
        type=str,
        default="dist/XRay_Transparent_Pack",
        help="Where to create the resource pack folder (default: dist/XRay_Transparent_Pack).",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="XRay Transparent Blocks Pack",
        help="Pack display name.",
    )
    parser.add_argument(
        "--description",
        type=str,
        default="Hides all block textures except diamond-related ones.",
        help="Pack description shown in Minecraft.",
    )
    parser.add_argument(
        "--no-mcpack",
        action="store_true",
        help="Do not create a .mcpack file, only the folder.",
    )

    args = parser.parse_args()

    source_root = Path(args.source_textures).resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"Source folder does not exist: {source_root}")

    source_blocks = source_root / "blocks"
    pack_root = Path(args.output_pack).resolve()
    target_blocks = pack_root / "textures" / "blocks"

    # Build textures into the pack
    make_transparent_blocks(source_blocks, target_blocks)

    # Manifest + icon
    write_manifest(pack_root, args.name, args.description)
    write_default_icon(pack_root)

    # Optional .mcpack archive
    if not args.no_mcpack:
        mcpack_path = pack_root.with_suffix(".mcpack")
        build_mcpack(pack_root, mcpack_path)


if __name__ == "__main__":
    main()



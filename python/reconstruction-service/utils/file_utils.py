from pathlib import Path


def resolve_output_path(output_dir: str, filename: str, prefix: str = "processed_") -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{prefix}{filename}"
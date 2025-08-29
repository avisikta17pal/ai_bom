import json
from pathlib import Path


def main():
    openapi_path = Path("openapi.json")
    if not openapi_path.exists():
        print("openapi.json not found. Start the API and download it to project root.")
        return
    data = json.loads(openapi_path.read_text())
    out = Path("frontend/src/lib/api-types.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data.get("components", {}).get("schemas", {}), indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()


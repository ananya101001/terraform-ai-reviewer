import hcl2
import json
import os
from pathlib import Path


def parse_terraform(folder_path: str) -> dict:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Terraform folder not found: {folder_path}")
    
    tf_files = list(folder.glob("*.tf"))
    if not tf_files:
        raise ValueError(f"No .tf files found in: {folder_path}")
    
    all_resources = []
    all_variables = {}
    all_outputs = {}
    all_providers = []
    raw_combined = {}

    for tf_file in tf_files:
        with open(tf_file, "r") as f:
            try:
                parsed = hcl2.load(f)
                raw_combined[tf_file.name] = parsed

                for resource_block in parsed.get("resource", []):
                    for resource_type, instances in resource_block.items():
                        for resource_name, config in instances.items():
                            all_resources.append({
                                "type": resource_type,
                                "name": resource_name,
                                "config": config,
                                "file": tf_file.name
                            })

                for var_block in parsed.get("variable", []):
                    all_variables.update(var_block)

                for output_block in parsed.get("output", []):
                    all_outputs.update(output_block)

                for provider_block in parsed.get("provider", []):
                    for provider_name, config in provider_block.items():
                        all_providers.append({
                            "name": provider_name,
                            "config": config
                        })

            except Exception as e:
                print(f"Warning: Could not parse {tf_file.name}: {e}")

    return {
        "resources": all_resources,
        "variables": all_variables,
        "outputs": all_outputs,
        "providers": all_providers,
        "resource_count": len(all_resources),
        "resource_types": list(set(r["type"] for r in all_resources)),
        "files_parsed": [f.name for f in tf_files],
    }


def summarize_terraform(parsed: dict) -> str:
    lines = []
    lines.append(f"## Terraform Summary")
    lines.append(f"Files: {', '.join(parsed['files_parsed'])}")
    lines.append(f"Total Resources: {parsed['resource_count']}")
    lines.append(f"Resource Types: {', '.join(parsed['resource_types'])}")
    lines.append("")
    lines.append("## Resources:")

    for resource in parsed["resources"]:
        lines.append(f"\n### {resource['type']}.{resource['name']}")
        config_str = json.dumps(resource["config"], indent=2, default=str)
        lines.append(f"```json\n{config_str}\n```")

    return "\n".join(lines)
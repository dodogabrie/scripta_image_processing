# genera_models.py
import json

def field_to_code(field):
    args = []
    kwargs = []
    for k, v in field.items():
        if k == "name":
            continue
        if k == "type":
            continue
        if k == "choices":
            kwargs.append(f"choices={v}")
        elif isinstance(v, str):
            kwargs.append(f"{k}='{v}'")
        else:
            kwargs.append(f"{k}={v}")
    args_str = ", ".join(kwargs)
    return f"    {field['name']} = models.{field['type']}({args_str})"

def generate_model(model):
    lines = [f"class {model['name']}(models.Model):"]
    for field in model.get("fields", []):
        lines.append(field_to_code(field))
    # Relations
    for rel in model.get("relations", []):
        rel_type = rel["type"]
        rel_args = [f"'{rel['to']}'"]
        for k, v in rel.items():
            if k in ("type", "to"):
                continue
            if isinstance(v, str):
                rel_args.append(f"{k}='{v}'")
            else:
                rel_args.append(f"{k}={v}")
        lines.append(f"    {rel['related_name']} = models.{rel_type}({', '.join(rel_args)})")
    lines.append("")
    return "\n".join(lines)

def main():
    with open("schema.json") as f:
        schema = json.load(f)
    print("from django.db import models\n")
    for resource in schema.get("resources", []):
        print(generate_model(resource))
    for plugin in schema.get("plugins", []):
        print(generate_model(plugin))

if __name__ == "__main__":
    main()
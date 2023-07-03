import os
import ast


def get_imports(path):
    imports = set()

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r") as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError:
                        continue

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.add(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            imports.add(node.module)

    return imports


# usage
print(get_imports("./dev"))

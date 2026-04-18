import importlib.util
import inspect
import pathlib
from typing import Dict, Type
from models.labmodel import LabModel

class ModelManager:
    def __init__(self, plugin_path: str = "./models"):
        self.plugin_path = pathlib.Path(plugin_path)
        self.available_models: Dict[str, Type[LabModel]] = {}

    def load_plugins(self):
        for file in self.plugin_path.glob("*.py"):
            if file.stem == "__init__":
                continue

            # Load the module
            spec = importlib.util.spec_from_file_location(file.stem, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all classes that inherit from LabModel
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, LabModel) and obj is not LabModel:
                    # Use the class name or a custom 'label' attribute for the UI
                    display_name = getattr(obj, "label", name)
                    self.available_models[display_name] = obj
        model_names = [model.name for model in self.available_models.values()]
        return model_names

    def fetch_model(self, model_name):

        for model in self.available_models.values():
            if model.name == model_name:
                return model


if __name__ == "__main__":

    # Usage
    manager = ModelManager()
    models = manager.load_plugins()
    model = manager.fetch_model("SingleExponential")
    print(model)

    
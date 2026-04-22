import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.model_manager import ModelManager
from src.core.data_loader import Hdf5Loader
from src.core.structures import InspectInfo, DataResult


class AnalysisEngine:

    def __init__(self, plugin_path):
        # The Engine coordinates the specialized classes
        self.model_manager = ModelManager(plugin_path)
        self.loader = Hdf5Loader()
        self.data = DataAccessProxy(
            fetch_callback=self.loader.fetch_dataset,
            name_map=self.loader._name_map
        )
        
        # State: What are we working on right now?
        self.active_x = DataResult()
        self.active_y = DataResult()
        self.active_axis = []
        self.active_model = None
        self.fit_result = None
        self.fit_y = None
        self.fit_x = None
        self.file = ""

    def load_file(self, path):
        """
        Delegates to the loader to get the file structure.
        The GUI calls this to populate the TreeWidget.
        """
        self.file = path
        structure = self.loader.load_file(self.file)
        return structure

    def load_models(self):
        """Wrapper function to provide model list to the UI."""
        # Sort it so the dropdown always looks the same
        available_models = self.model_manager.load_plugins()
        return sorted(available_models)

    def get_info(self, path) -> InspectInfo:

        return self.loader.fetch_inspect_info(path)

    def get_data(self, path) -> DataResult:

        data = self.loader.fetch_dataset(path)
        if not isinstance(data, DataResult):
            raise TypeError(f"Expected a dataset at '{path}', but got {type(data).__name__}")
        return data

    def select_data(self, x_path: str, y_path: str):
        """
        Requests specific arrays from the loader and stores them 
        as the 'active' state for fitting.
        """
        self.active_x = self.get_data(x_path)
        self.active_y = self.get_data(y_path)
        self.active_axis = [x_path, y_path]

        return self.active_x, self.active_y

    def select_model(self, model_name):
        """Sets the active model by requesting the class from the manager."""
        model_class = self.model_manager.fetch_model(model_name)
        self.active_model = model_class() # Instantiate it
        return self.active_model.get_parameter_list()

    def run_fit(self):
        """
        Perform the fit using the stored data and active model.
        """
        if self.active_model is None:
            raise ValueError("No model selected.")
        params = self.active_model.params
        self.fit_result = self.active_model.fit(
            self.active_y.data, 
            x=self.active_x.data, 
            params=params
        )
        if not self.fit_result.success:
            print("Fit failed:", self.fit_result.message)

        if self.fit_result is None:
            raise RuntimeError("Fit failed to produce a result.")
    
        userkws = self.fit_result.userkws or {}
        self.fit_x = userkws.get('x')
        self.fit_y = self.fit_result.best_fit
        fit_params = self.active_model.get_parameter_list(self.fit_result.params)

        return self.fit_result, fit_params

    def guess_params(self):
        if self.active_model is None:
            raise ValueError("No model selected.")
        x_data = self.active_x.data
        y_data = self.active_y.data
        params = self.active_model.guess_initial_params(x_data, y_data)
        return self.active_model.get_parameter_list()

    def save_fit(self, filepath: str = ""):

        if not filepath:
            filepath = self.file
        if self.active_model is None:
            raise ValueError("No model selected.")
        self.loader.save_fit(
            filepath,
            self.fit_result,
            self.active_model.name,
            self.active_axis
        )

    def load_fit(self, filepath:str):

        res = self.loader.load_fit(filepath, "20260416-1304-53_SingleExponential")
        if res:
            traces, params_list, report = res
            self.active_x = traces["x"]
            self.active_y = traces["y"]
            self.fit_x = traces["fit_x"]
            self.fit_y = traces["fit_y"]
            params = self.apply_parameter_settings(params_list)

            return params

    def apply_parameter_settings(self, params_list):
        """
        Takes a list of dicts (from GUI or Loader) and 
        updates the active lmfit.Parameters object.
        """
        # Ensure we have an active model to attach these to
        if self.active_model is None:
            return

        for p_dict in params_list:
            name = p_dict['name']
            value = p_dict['value']
            vary = p_dict['vary']
            min_value = p_dict['min']
            max_value = p_dict['max']

            # Attach stderr if it exists (for display)
            stderr = p_dict.get('stderr', 0.0)
            self.active_model.set_parameter(
                name,
                value,
                vary,
                min_value,
                max_value,
                stderr
            )
        return self.active_model.params


class DataAccessProxy:
    """
    A helper class to allow dot-notation access to HDF5 datasets.
    """
    def __init__(self, fetch_callback, name_map):
        self._fetch = fetch_callback # The function that actually gets the data
        self._map = name_map         # The dict {short_name: full_path}

    def __getattr__(self, name):
        """This triggers when you type .name"""
        if name in self._map:
            path = self._map[name]
            return self._fetch(path)
        raise AttributeError(f"Dataset '{name}' not found in current file.")

    def __dir__(self):
        """This allows Tab-Completion in Jupyter Notebooks!"""
        return list(self._map.keys())



if __name__ == "__main__":

    import matplotlib.pyplot as plt

    engine = AnalysisEngine(r"models")
    engine.load_file(r"ex_data.h5")
    x_data, y_data = engine.select_data("/Data/tau", "/Data/pl_mean")
    models = engine.load_models()
    params = engine.select_model("SingleExponential")
    data = engine.data.pl_mean
    print(data)
    engine.guess_params()
    fit_result = engine.run_fit()

    #engine.save_fit(r"ex_data.h5")

    fig, ax = plt.subplots()
    ax.plot(engine.active_x.data, engine.active_y.data, "bo") # type: ignore
    ax.plot(engine.fit_x, engine.fit_y, "r-") # type: ignore

    plt.show()
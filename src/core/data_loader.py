import h5py
import numpy as np
import datetime
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.structures import InspectInfo, Dataset


class Hdf5Loader:
    def __init__(self):
        self.filepath = ""
        self._name_map = {} # Shortcut: {'Trace_A': '/Data/Pulsed/Trace_A'}


    def load_file(self, filepath):

        self.filepath = filepath
        structure = self._get_tree_structure()
        return structure

    def fetch_dataset(self, internal_path):

        with h5py.File(self.filepath, 'r') as f:
            ds = f[internal_path]
            if isinstance(ds, h5py.Group):
                info = self.fetch_inspect_info(internal_path)
                if info is not None:
                    return info
            if isinstance(ds, h5py.Dataset):
                array = ds[:]
                array = np.array(array)
                return Dataset(
                    path=internal_path,
                    name=internal_path.split("/")[-1] or "/",
                    data=array
                )

        raise TypeError(
            f"Unsupported HDF5 object at " +
            f"'{internal_path}': {type(ds).__name__}"
            )

    def save_fit(self, filepath, fit_result, model_name, source_data):
        """
        Saves the analysis results while leaving the 'Data' group untouched.
        """
        with h5py.File(filepath, 'a') as f:
            # Ensure the structure follows our pillar layout
            if "Data" not in f:
                print("Warning: Saving analysis to a file without a 'Data' group.")
            
            # Create/Access the Analysis pillar
            timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M-%S')
            model_run = timestamp + "_" + model_name
            analysis_root = f.require_group(f"Analysis/{model_run}")
            
            # 1. Save the ModelTraces
            trace_grp = analysis_root.require_group("ModelTraces")
            for dset in ["fit_x", "fit_y", "residuals"]:
                if dset in trace_grp: del trace_grp[dset]
            
            trace_grp["x"] = f[source_data[0]]
            trace_grp["y"] = f[source_data[1]]
            trace_grp.create_dataset("fit_x", data=fit_result.userkws['x'])
            trace_grp.create_dataset("fit_y", data=fit_result.best_fit)
            trace_grp.create_dataset("residuals", data=fit_result.residual)

            # 2. Parameters Table
            dtype = [('name', 'S32'), ('value', 'f8'), ('stderr', 'f8'), 
                     ('min', 'f8'), ('max', 'f8'), ('vary', 'i1')]
            
            table_data = []
            for name, p in fit_result.params.items():
                table_data.append((
                    name.encode('utf-8'), p.value, 
                    p.stderr if p.stderr else 0.0,
                    p.min, p.max, 1 if p.vary else 0
                ))
            
            if "parameters" in analysis_root: del analysis_root["parameters"]
            analysis_root.create_dataset(
                "parameters", data=np.array(table_data, dtype=dtype))

            # 3. Text Report
            if "report" in analysis_root: del analysis_root["report"]
            analysis_root.create_dataset(
                "report", data=fit_result.fit_report().encode('utf-8'))

    def load_fit(self, filepath, model_run):
        """
        model_run: the internal HDF5 path, e.g., 'Analysis/NvT1Relaxation_20260416'
        """
        if model_run[0:9] != "/Analysis":
            model_run = "/Analysis/" + model_run
        with h5py.File(filepath, 'r') as f:
            if model_run not in f:
                return None

            traces_group = f[model_run]
            if not isinstance(traces_group, h5py.Group):
                raise TypeError(
                    f"Expected a group at '{model_run}', found {type(traces_group).__name__}")
            
            def _read_dataset(parent: h5py.Group, name: str) -> np.ndarray:
                child = parent.get(name)
                if not isinstance(child, h5py.Dataset):
                    raise TypeError(f"Expected dataset '{parent.name}/{name}', got {type(child).__name__}")
                return np.asarray(child[()])    
            
            # 1. Load the Traces (Fit curve and residuals)
            traces = {
                "x": _read_dataset(traces_group, "x"),
                "y": _read_dataset(traces_group, "y"),
                "fit_x": _read_dataset(traces_group, "fit_x"),
                "fit_y": _read_dataset(traces_group, "fit_y"),
                "residuals": _read_dataset(traces_group, "residuals"),
            }

            # 2. Get the parameters data
            param_table = _read_dataset(traces_group, "parameters")
        
            # Convert the structured NumPy array into a list of dictionaries
            params_list = []
            for row in param_table:
                params_list.append({
                    'name': row['name'].decode('utf-8'),
                    'value': float(row['value']),
                    'stderr': float(row['stderr']),
                    'min': float(row['min']),
                    'max': float(row['max']),
                    'vary': bool(row['vary'])
                })

            # 3. Get the text report
            report = _read_dataset(traces_group, "report")

            return traces, params_list, report

    def _get_tree_structure(self):
        """
        Recursively maps the entire HDF5 file.
        Returns a nested dictionary representing the groups and datasets.
        """
        def _walk_group(group):
            tree = {}
            for key, item in group.items():
                self._name_map[key] = item.name
                if isinstance(item, h5py.Group):
                    tree[key] = {"type": "Group", "children": _walk_group(item)}
                elif isinstance(item, h5py.Dataset):
                    tree[key] = {"type": "Dataset", "shape": item.shape}
            return tree

        try:
            with h5py.File(self.filepath, 'r') as f:
                return {"/": {"type": "Group", "children": _walk_group(f)}}
        except Exception as e:
            print(f"Error reading file: {e}")
            return {}

    def fetch_inspect_info(self, internal_path) -> InspectInfo:
        """
        Fetches metadata for the H5Web-style 'Inspect' tab.
        internal_path: e.g., 'Data/Pulsed/Exp_001'
        """
        with h5py.File(self.filepath, 'r') as f:
            if internal_path not in f and internal_path != "/":
                raise KeyError(f"Path '{internal_path}' not found in file.")

            node = f[internal_path] if internal_path != "/" else f
                        
            info = InspectInfo(
                path=internal_path,
                name=internal_path.split('/')[-1] or "/",
                is_dataset=isinstance(node, h5py.Dataset),
                attributes={}
            )

            # 1. Grab all attributes (Metadata)
            for key, val in node.attrs.items():
                # Convert bytes to strings for GUI safety
                if isinstance(val, bytes):
                    val = val.decode('utf-8')
                info.attributes[key] = val

            # 2. Grab Dataset-specific info
            if isinstance(node, h5py.Dataset):
                info.shape = node.shape
                info.dtype = str(node.dtype)
                info.size_bytes = node.dtype.itemsize

                # Map the byte order symbols to human names
                order = node.dtype.byteorder
                if order == '<': info.byte_order = "little-endian"
                elif order == '>': info.byte_order = "big-endian"
                else: info.byte_order = "native"

                # Check for compression filters
                if node.compression:
                    info.filters.append(f"compression: {node.compression}")
                if node.shuffle:
                    info.filters.append("shuffle")
                
            else:
                info.shape = None
                info.dtype = None
                
        return info

if __name__ == "__main__":


    loader = Hdf5Loader()
    tree = loader.load_file(r"ex_data.h5")
    print(tree)
    print(loader.fetch_dataset("Data"))
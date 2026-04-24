# QuTrace

Project in development.

Aims to be a suite to analyze data from quantum optics experiments.

## To-Do

- Handle plot creation
  - Handle data selection for plotting
  - Plotting should be implemented from workbench loaded datasets or traces
  - Add plot method to Traces and FitResult
- Workbench right click menu
    - Delete workbench item (All except root nodes)
    - Add to Trace (Dataset)
    - Add to new Trace (Dataset)
    - Create new plot (Dataset | Trace | FitResult)
    - Plot in (Dataset | Trace | FitResult)
    - Export (Dataset | Trace | FitResult)
      - HDF5
      - JSON
      - Numpy
      - CSV
- FitResult data saving
- Finish and clean logging implementation ✅
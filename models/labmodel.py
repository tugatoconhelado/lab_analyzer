import lmfit


class LabModel(lmfit.Model):

    model_name = "LabModel"

    def __init__(self, *args, **kwargs):
        # We pass the fit_func of the subclass to the lmfit.Model parent
        super().__init__(
            func=self.fit_func, name=self.model_name, *args, **kwargs)

        self.params = self.make_params()

    def fit_func(self, x, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement fit_func")

    def guess_initial_params(self, x, y):
        """Optional: Override this to provide smart starting guesses."""
        return self.params

    def set_parameter(self, name, value, vary, min_value, max_value, stderr):

        if name in self.params:
            p = self.params[name]
            p.set(
                value=value,
                vary=vary,
                min=min_value,
                max=max_value
            )
            # Attach stderr if it exists (for display)
            p.stderr = stderr

    def get_parameter_list(self, params = None):

        if params is None:
            params = self.params
        param_list = []
        for name, param in params.items():
            param_list.append({
                'name': name,
                'value': param.value,
                'stderr': param.stderr if param.stderr else 0.0,
                'min': param.min,
                'max': param.max,
                'vary': param.vary
            })
        return param_list


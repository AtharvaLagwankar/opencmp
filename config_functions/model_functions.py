########################################################################################################################
# Copyright 2021 the authors (see AUTHORS file for full list).                                                         #
#                                                                                                                      #
# This file is part of OpenCMP.                                                                                        #
#                                                                                                                      #
# OpenCMP is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public  #
# License as published by the Free Software Foundation, either version 2.1 of the License, or (at your option) any     #
# later version.                                                                                                       #
#                                                                                                                      #
# OpenCMP is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied        #
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more  #
# details.                                                                                                             #
#                                                                                                                      #
# You should have received a copy of the GNU Lesser General Public License along with OpenCMP. If not, see             #
# <https://www.gnu.org/licenses/>.                                                                                     #
########################################################################################################################

from .base_config_functions import ConfigFunctions
from helpers.io import create_and_load_gridfunction_from_file
import ngsolve as ngs
from ngsolve import Parameter, CoefficientFunction, GridFunction, FESpace
from typing import Dict, Optional, Union, List


class ModelFunctions(ConfigFunctions):
    """
    Class to hold the model functions and parameters.
    """

    def __init__(self, config_rel_path: str, t_param: List[Parameter] = [Parameter(0.0)],
                 new_variables: List[Dict[str, Optional[int]]] = [{}]) -> None:
        super().__init__(config_rel_path, t_param)

        # Load the model functions/parameters/components dict from the main config file.
        try:
            self.model_parameters_dict, self.model_parameters_re_parse_dict = self.config.get_two_level_dict('PARAMETERS', self.t_param, new_variables)
        except KeyError:
            self.model_parameters_dict = {}
            self.model_parameters_re_parse_dict = {}

        try:
            self.model_functions_dict, self.model_functions_re_parse_dict = self.config.get_two_level_dict('FUNCTIONS', self.t_param, new_variables)
        except KeyError:
            self.model_functions_dict = {}
            self.model_functions_re_parse_dict = {}

    def set_model_functions(self, fes: FESpace, model_components: Dict[str, int]) -> None:
        """
        Function to load saved model functions into gridfunctions.

        Args:
            fes: The model's finite element space.
            model_components: Maps between variable names and their component in the model's finite element space.
        """

        for function, var_dict in self.model_functions_dict.items():
            # There may be multiple types of model functions.
            for var, val_lst in var_dict.items():

                # Determine which component of the finite element space the model function is for.
                if var == 'all':
                    component = None
                else:
                    component = model_components[var]

                # If the model function is a gridfunction saved to a file it needs to be loaded. The re_parse dictionary
                # does not need to be updated since the gridfunction must be a constant field, it can't possibly be a
                # variable function of one of the model variables.
                for i in range(len(val_lst)):
                    val = val_lst[i]

                    if isinstance(val, str):
                        # Check that the file exists.
                        val = self._find_rel_path_for_file(val)

                        if component is None:
                            # Loaded gridfunction should cover full finite element space.
                            self.model_functions_dict[function][var][i] = create_and_load_gridfunction_from_file(val, fes, [self.run_dir, self.run_dir + '/model_dir'])
                        else:
                            # Loaded gridfunction is for one component of the finite element space.
                            fes_tmp = fes.components[component]
                            self.model_functions_dict[function][var][i] = create_and_load_gridfunction_from_file(val, fes_tmp, [self.run_dir, self.run_dir + '/model_dir'])

    def update_model_functions(self, t_param: List[Parameter],
                               updated_variables: List[Dict[str, Union[float, CoefficientFunction, GridFunction]]]) \
            -> None:
        """
        Function to update the model parameters/functions with new values of the model_variables.

        Args:
            t_param: List of parameters representing the current time and previous time steps.
            updated_variables: List of dictionaries containing any new model variables and their values at each time
                step used in the time discretization scheme.
        """

        for k1, v1 in self.model_parameters_re_parse_dict.items():
            self.model_parameters_dict[k1] = self.re_parse(self.model_parameters_dict[k1], self.model_parameters_re_parse_dict[k1], t_param, updated_variables)

        for k1, v1 in self.model_functions_re_parse_dict.items():
            self.model_functions_dict[k1] = self.re_parse(self.model_functions_dict[k1], self.model_functions_re_parse_dict[k1], t_param, updated_variables)
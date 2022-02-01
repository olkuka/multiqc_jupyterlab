#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Aleksandra Kukawka.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import DOMWidget, Output
from IPython.display import display, HTML
from ._frontend import module_name, module_version

import multiqc


class MultiQC(DOMWidget):
    # _model_name = Unicode('MultiQCModel').tag(sync=True)
    # _model_module = Unicode(module_name).tag(sync=True)
    # _model_module_version = Unicode(module_version).tag(sync=True)
    # _view_name = Unicode('MultiQCView').tag(sync=True)
    # _view_module = Unicode(module_name).tag(sync=True)
    # _view_module_version = Unicode(module_version).tag(sync=True)

    def __init__(self):
        super().__init__()
        multiqc.init()

        print("MultiQC initialized in JupyterLab. Usage: \n"
              "- load(data_dir, file_list, overwrite) \t- load new data, \n"
              "- add(multiqc_data) \t\t\t- add data directly from MultiQC run, \n"
              "- get_modules() \t\t\t- get a list of available modules, \n"
              "- get_samples(module) \t\t\t- get list of samples for a given module, \n"
              "- show(module, samples) \t\t- see the report for a given module and list of samples.")

    def load(self, analysis_dir, file_list=False, overwrite=False):
        """
        Triggers multiqc load function

        Parameters:
        analysis_dir: Directory for with data to load
        file_list: False by default, True if more than one analysis_dir is given
        overwrite: False by default, True if user wants to overwrite al of the previous data

        """
        result = multiqc.load(analysis_dir, file_list, overwrite)
        if result:
            print("Data from the given directory successfully loaded and saved in jupyterlab_data directory.")
        else:
            print(result)

    def add(self, multiqc_data):
        """
        Triggers multiqc add function

        Parameters:
        multiqc_data: Directory with MultiQC run data

        """
        result = multiqc.add(multiqc_data)
        if result:
            print("Data from MultiQC run succesfully loaded and saved in jupyterlab_data directory.")
        else:
            print(result)

    def show(self, module, samples):
        """
        Triggers multiqc show function and displays it in the JupyterLab cell

        Parameters:
        module
        samples: list of samples

        """
        output_widget = multiqc.show(list(module.split(',')), samples)
        display(HTML(output_widget))

    def get_samples(self, module):
        """
        Triggers multiqc get_samples function and displays it in the JupyterLab cell

        Parameters:
        module

        """
        samples = multiqc.get_samples(module)
        if not samples:
            print("No samples for a given module found or wrong module specified.")
        else:
            display(samples)

    def get_modules(self):
        """
        Triggers multiqc get_available_modules function and displays it in the JupyterLab cell

        Parameters:
        module

        """
        modules = multiqc.get_modules()
        if not modules:
            print("No modules found.")
        else:
            display(modules)

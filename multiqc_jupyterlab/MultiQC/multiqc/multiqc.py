#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
from copy import deepcopy
from distutils.dir_util import copy_tree
import io
import jinja2
import json
import os
import re
import rich
import shutil
import sys
import tempfile
from collections import defaultdict

from .plots import table
from .utils import report, plugin_hooks, config, log

try:
    # Python 3 imports
    from urllib.request import urlopen
except ImportError:
    # Python 2 imports
    from urllib2 import urlopen

    # use UTF-8 encoding by default
    reload(sys)
    sys.setdefaultencoding('utf8')

# console initialization
console = rich.console.Console(stderr=True, highlight=False, force_terminal=log.force_term_colors())


def init():
    """
    Initializes report, adds template and directory for report data in config

   """
    console.print(
        '\n  [blue]/[/][green]/[/][red]/[/] [bold][link=https://multiqc.info]MultiQC[/link][/] :mag: [dim]| JupyterLab extension\n'
    )
    report.init()
    config.template = 'jupyterlab'
    config.jupyterlab_dir = os.path.join(config.output_dir, 'jupyterlab_data')
    config.data_sources_dir = os.path.join(config.jupyterlab_dir, 'data_sources')


def load(analysis_dir, file_list, overwrite):
    """
    Loads data from the given directory. Iterates through files and creates data for each module for further usage.

    Parameters:
    analysis_dir: Directory with data to load
    file_list: True if more than one analysis_dir is given
    overwrite: True if user wants to overwrite al of the previous data

    Returns:
    True or an appropriate comment if something went wrong

    """
    tmp_dir = tempfile.mkdtemp()
    config.analysis_dir = analysis_dir
    report.init()

    # clean up analysis_dir if a string (interactive environment only)
    if isinstance(config.analysis_dir, str):
        config.analysis_dir = [config.analysis_dir]

    # add files if file_list is True
    if file_list:
        if len(analysis_dir) > 1:
            return ('If file_list is given, analysis_dir should have only one plain text file.')
        config.analysis_dir = []
        with (open(analysis_dir[0])) as in_handle:
            for line in in_handle:
                if os.path.exists(line.strip()):
                    path = os.path.abspath(line.strip())
                    config.analysis_dir.append(path)
        if len(config.analysis_dir) == 0:
            return ('Please, check that {} contains correct paths.'.format(analysis_dir[0]))

    # get default module order
    config.module_order = [m if type(m) is dict else {m: {}} for m in config.module_order]

    # create the temporary working directories for data and plots
    config.data_tmp_dir = os.path.join(tmp_dir, 'multiqc_data')
    config.data_dir = None
    config.plots_tmp_dir = os.path.join(tmp_dir, 'multiqc_plots')
    config.plots_dir = None

    # create jupyterlab_dir if doesn't exist yet
    if not os.path.exists(config.jupyterlab_dir):
        os.makedirs(config.jupyterlab_dir)

    # get the list of files to search
    for d in config.analysis_dir:
        console.print('Search path: {}'.format(os.path.abspath(d)))

    mod_keys = [list(m.keys())[0] for m in config.module_order]

    # get the list of modules to run
    run_modules = [
        m
        for m in config.module_order
        if list(m.keys())[0] in config.avail_modules.keys()
    ]
    run_module_names = [list(m.keys())[0] for m in run_modules]
    report.get_filelist(run_module_names)

    # get only modules that are not empty for this data
    non_empty_modules = {key.split('/')[0].lower() for key, files in report.files.items() if len(files) > 0}
    run_modules = [m for m in run_modules if list(m.keys())[0].lower() in non_empty_modules]
    report.modules_output = list()

    # run the modules for the loaded data
    for mod_idx, mod_dict in enumerate(run_modules):
        this_module = list(mod_dict.keys())[0]

        # create a directory for the running module if doesn't exist yet
        this_module_dir = os.path.join(config.jupyterlab_dir, this_module.lower())
        if not os.path.exists(this_module_dir):
            os.makedirs(this_module_dir)

        mod_cust_config = list(mod_dict.values())[0]
        if mod_cust_config is None:
            mod_cust_config = {}

        report.plot_data = dict()  # clear data dictionary

        mod = config.avail_modules[this_module].load()
        mod.mod_cust_config = mod_cust_config
        output = mod()
        if type(output) != list:
            output = [output]

        # check if file with data for plots exists or if overwrite is True
        if not os.path.exists(os.path.join(this_module_dir, 'module_output' + '.json')) \
                or overwrite:
            # if above condition is true, create directory for every module and plot's create data
            for i, m in enumerate(output):
                module_output = dict()
                # copy below attributes
                module_output['sections'] = m.sections
                module_output['anchor'] = m.anchor
                module_output['name'] = m.name
                module_output['intro'] = m.intro
                if hasattr(m, 'js'):
                    module_output['js'] = m.js
                if hasattr(m, 'css'):
                    module_output['css'] = m.css
                if hasattr(m, 'content'):
                    module_output['content'] = m.css
                report.modules_output.append(m)
                with open(os.path.join(this_module_dir, 'module_output' + '.json'), 'a') as module_output_file:
                    json.dump(module_output, module_output_file)  # write plot's create data to a single file
                    # if not last output
                    if i != len(output) - 1:
                        module_output_file.write(',\n')

        # save data from analysis_dir for this module
        plot_data_dir = os.path.join(this_module_dir, 'plot_data')
        base = os.path.basename('data')
        plot_data = os.path.join(plot_data_dir, base)

        if overwrite and os.path.exists(plot_data_dir):
            os.remove(plot_data_dir)
        else:
            plot_data_num = 1
            # iterate through numbers until we get a filename that is free
            while os.path.exists(plot_data + '.json'):
                plot_data = os.path.join(plot_data_dir, '{}_{}'.format(base, plot_data_num))
                plot_data_num += 1
            plot_data_name = os.path.basename(plot_data)

        if not os.path.exists(plot_data_dir):
            os.makedirs(plot_data_dir)

        # write data to file
        with open(os.path.join(plot_data_dir, plot_data_name + '.json'), 'a') as plot_data_file:
            json.dump(report.plot_data, plot_data_file)

    # write data sources to file
    base = os.path.basename('data_source')
    data_source = os.path.join(config.data_sources_dir, base)

    if overwrite and os.path.exists(config.data_sources_dir):
        os.remove(config.data_sources_dir)
    else:
        data_source_num = 1
        # iterate through numbers until we get a filename that is free
        while os.path.exists(data_source + '.json'):
            data_source = os.path.join(config.data_sources_dir, '{}_{}'.format(base, data_source_num))
            data_source_num += 1
        data_source_name = os.path.basename(data_source)
    if not os.path.exists(config.data_sources_dir):
        os.makedirs(config.data_sources_dir)

    with open(os.path.join(config.data_sources_dir, data_source_name + '.json'), 'a') as data_source_file:
        json.dump(report.data_sources, data_source_file)

    shutil.rmtree(tmp_dir)
    return True


def add(multiqc_data):
    """
    Adds prepared data from MultiQC run saved in multiqc_data by default.

    Parameters:
    multiqc_data: Directory with MultiQC run data

    Returns:
    True or an appropriate comment if something went wrong

    """
    tmp_dir = tempfile.mkdtemp()
    report.init()

    # create jupyterlab_dir if doesn't exist yet
    if not os.path.exists(config.jupyterlab_dir):
        os.makedirs(config.jupyterlab_dir)
    report.modules_output = list()

    # read whole content of the multiqc_data file if exists
    if not os.path.exists(os.path.join(multiqc_data, 'multiqc_data.json')):
        return ('No MultiQC data in this directory found.')

    with open(os.path.join(multiqc_data, 'multiqc_data.json'), 'r') as multiqc_data_f:
        multiqc_data_file = json.load(multiqc_data_f)  # read multiqc data to multiqc_data_file

    # prepare helper variables for saving to file
    previous_module_name = ''
    this_module_dict = dict()

    # iterate through the loaded data
    for module_plot_name, module_plot_content in multiqc_data_file['report_plot_data'].items():
        full_section_name = module_plot_name.replace('-', '_').split('_')  # extract section name

        # extract module name (take care of exceptions like two-part names)
        if full_section_name[0] == 'fastq':
            module_name = full_section_name[0] + '_' + full_section_name[1]
        else:
            module_name = full_section_name[0]

        # check if module is ready to write to file
        if (previous_module_name != module_name and previous_module_name != '') or module_plot_name == \
                list(multiqc_data_file['report_plot_data'].keys())[-1]:
            # open this module dir
            this_module_dir = os.path.join(config.jupyterlab_dir, previous_module_name.lower())

            # create a directory if doesn't exist yet
            if not os.path.exists(this_module_dir):
                os.makedirs(this_module_dir)

            # save data from this module
            plot_data_dir = os.path.join(this_module_dir, 'plot_data')
            base = os.path.basename('data')
            plot_data = os.path.join(plot_data_dir, base)
            plot_data_num = 1
            # iterate through numbers until we get a filename that is free
            while os.path.exists(plot_data + '.json'):
                plot_data = os.path.join(plot_data_dir, '{}_{}'.format(base, plot_data_num))
                plot_data_num += 1
            plot_data_name = os.path.basename(plot_data)

            if not os.path.exists(plot_data_dir):
                os.makedirs(plot_data_dir)

            # write data to file
            with open(os.path.join(plot_data_dir, plot_data_name + '.json'), 'a') as plot_data_file:
                json.dump(this_module_dict, plot_data_file)

            # clear temporary dictionary for new module
            this_module_dict = dict()

        this_module_dict[module_plot_name] = module_plot_content
        previous_module_name = module_name

    # write data sources to file
    base = os.path.basename('data_source')
    data_source = os.path.join(config.data_sources_dir, base)

    data_source_num = 1
    # iterate through numbers until we get a filename that is free
    while os.path.exists(data_source + '.json'):
        data_source = os.path.join(config.data_sources_dir, '{}_{}'.format(base, data_source_num))
        data_source_num += 1
    data_source_name = os.path.basename(data_source)
    if not os.path.exists(config.data_sources_dir):
        os.makedirs(config.data_sources_dir)

    with open(os.path.join(config.data_sources_dir, data_source_name + '.json'), 'a') as data_source_file:
        json.dump(multiqc_data_file['report_data_sources'], data_source_file)

    shutil.rmtree(tmp_dir)
    return True


def get_samples(module):
    """
    Finds a directory with data sources and iterate through them to get every sample for a given module.

    Parameters:
    module

    Returns:
    list of samples without duplicates for a given module or False if something went wrong

    """
    samples = []
    module = module.lower()

    for data_source in os.listdir(config.data_sources_dir):
        with open(os.path.join(config.data_sources_dir, data_source), 'r') as file:
            data_sources = json.load(file)
        for m in data_sources:
            if module == m.lower():  # find module
                for s in data_sources[m]:
                    for sample in data_sources[m][s]:  # list all of the samples for a given module
                        samples.append(sample)
                break  # if module found, leave the loop because there will be no other entry for the same module
    if samples:
        return list(set(samples))  # use set to get rid of duplicates
    return False


def get_modules():
    """
    Finds a directory with data sources and iterate through them to get every module.

    Returns:
    list of available modules without duplicates

    """
    modules = []

    for data_source in os.listdir(config.data_sources_dir):
        with open(os.path.join(config.data_sources_dir, data_source), 'r') as file:
            data_sources = json.load(file)
        for m in data_sources:
            modules.append(m)
    if modules:
        return list(set(modules))  # use set to get rid of duplicates
    return False


def show(module, samples):
    """
    Shows plots for a given module and list of samples.

    Parameters:
    module
    samples: list of samples

    Returns:
    report_output or an appropriate comment if something went wrong

    """
    if len(module) != 1:
        return ('Please specify only one module.')
    tmp_dir = tempfile.mkdtemp()
    # load template
    template_mod = config.avail_templates[config.template].load()
    combine_output(module[0], samples)

    # copy over css & js files if requested by the theme (only for e.g. FastQC)
    try:
        for to, path in report.modules_output['css'].items():
            copy_to = os.path.join(tmp_dir, to)
            os.makedirs(os.path.dirname(copy_to))
            shutil.copyfile(path, copy_to)
    except:
        pass
    try:
        for to, path in report.modules_output['js'].items():
            copy_to = os.path.join(tmp_dir, to)
            os.makedirs(os.path.dirname(copy_to))
            shutil.copyfile(path, copy_to)
    except:
        pass

    try:
        parent_template = config.avail_templates[template_mod.template_parent].load()
        copy_tree(parent_template.template_dir, tmp_dir)
    except AttributeError:
        pass  # not a child theme

    copy_tree(template_mod.template_dir, tmp_dir)  # copy template files to temporary directory

    # function to include file contents in Jinja template
    def include_file(name, fdir=tmp_dir, b64=False):
        try:
            if fdir is None:
                fdir = ''
            if b64:
                with io.open(os.path.join(fdir, name), 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            else:
                with io.open(os.path.join(fdir, name), 'r', encoding='utf-8') as f:
                    return f.read()
        except (OSError, IOError) as e:
            logger.error('Could not include file "{}": {}'.format(name, e))

    # load the report template
    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(tmp_dir))
        env.globals['include_file'] = include_file
        j_template = env.get_template(template_mod.base_fn)
    except:
        raise IOError('Could not load {} template file "{}"'.format(config.template, template_mod.base_fn))

    # use Jinja2 to render the template
    report_output = j_template.render(report=report, config=config)
    shutil.rmtree(tmp_dir)
    return report_output


def combine_output(module, samples_to_show):
    """
    Searches data for given samples and combines data for a given module into one consistent report.
    Creates report.modules_output and report.plot_data instances for the report.

    Parameters:
    module
    samples_to_show: list of samples

    """
    module = module.lower()
    # find directory for a given module
    this_module_dir = os.path.join(config.jupyterlab_dir, module)
    with open(os.path.join(this_module_dir, 'module_output.json'), 'r') as module_output_file:
        report.modules_output = json.load(module_output_file)  # read module output to report.modules_output

    plot_data_dir = os.path.join(this_module_dir, 'plot_data')

    result = dict()
    for plot_data in os.listdir(plot_data_dir):  # for every data file in the module directory
        with open(os.path.join(plot_data_dir, plot_data), 'r') as file:
            plot_content = json.load(file)  # load content for this module
        # copy samples to the result dictionary
        for plot, content in plot_content.items():
            if content['plot_type'] in ['bar_graph', 'beeswarm']:  # bar graph and beeswarm share the same logic
                if plot not in result:  # if plot is not in the result yet, add it and clean samples and datasets
                    result[plot] = deepcopy(content)
                    result[plot]['samples'] = [[] for _ in range(len(result[plot]['samples']))]
                    for dataset in result[plot]['datasets']:
                        for el in dataset:
                            el['data'] = []

                for i, samples in enumerate(content['samples']):
                    # get sample indices for samples in samples_to_show, but check if they are not already in result
                    samples_indices = [idx for idx, sample in enumerate(samples) if
                                       sample.split(' ')[0] in samples_to_show and sample not in
                                       result[plot]['samples'][i]]
                    if samples_indices:
                        # append new samples to result samples
                        result[plot]['samples'][i].extend(map(samples.__getitem__, samples_indices))

                    for element, result_element in zip(content['datasets'][i], result[plot]['datasets'][i]):
                        if samples_indices:
                            # append new data to result data for every dataset
                            result_element['data'].extend(map(element['data'].__getitem__, samples_indices))

            elif content['plot_type'] in ['scatter', 'xy_line']:  # scatter and linear plots share the same logic
                if plot not in result:
                    result[plot] = deepcopy(content)

                    # TO NIE DZIAŁAŁO, BO KAŻDA LISTA BYŁA KOPIĄ KOLEJNEJ I W REZULTACIE TO W SUMIE BYŁA JEDNA LISTA
                    # result[plot]['datasets'] = [[]] * len(result[plot]['datasets'])
                    # cleanup datasets section in result
                    result[plot]['datasets'] = [[] for _ in range(len(result[plot]['datasets']))]

                for i, dataset in enumerate(content['datasets']):
                    # for every dataset append element which contains sample name that matches one from the samples_to_show
                    for el in dataset:
                        if el['name'].split(' ')[0] in samples_to_show and el not in result[plot]['datasets'][i]:
                            result[plot]['datasets'][i].append(el)

            elif content['plot_type'] == 'heatmap':

                # heatmap supported for fastqc
                if 'fastqc' in plot:
                    if plot not in result:
                        result[plot] = deepcopy(content)
                        result[plot]['ycats'] = []
                        result[plot]['data'] = []
                        last_row_index = 0

                    samples_indices = [idx for idx, sample in enumerate(content['ycats']) if
                                       sample in samples_to_show and sample not in
                                       result[plot]['ycats']]
                    if samples_indices:
                        result[plot]['ycats'].extend(map(content['ycats'].__getitem__, samples_indices))
                        data_to_add, last_row_index = fastqc_heatmap(samples_indices, content['data'], last_row_index,
                                                                     len(content['xcats']))
                        result[plot]['data'].extend(data_to_add)
                else:
                    if plot not in result:
                        result[plot] = deepcopy(content)

            else:  # show all of the samples - options that are not supported yet
                if plot not in result:
                    result[plot] = deepcopy(content)

    report.plot_data = result
    report.plot_compressed_json = report.compress_json(report.plot_data)  # compress json file for Jinja2


def fastqc_heatmap(samples_indices, data, last_row_index, num_xcats):
    """
    Supports heatmap for FastQC module.

    Parameters:
    samples_indices
    data: list of cells with data for a heatmap
    num_xcats: number of categories on X axis (11 for FastQC by default)

    Returns:
    result for the given samples indices

    """
    result = []
    for i, sample_index in enumerate(samples_indices):
        # extract indices for a given sample, find data for these indices and create cells with new positions
        sample_data_indices = list(range(sample_index * num_xcats, sample_index * num_xcats + num_xcats))
        cells = [[j, i + last_row_index, data[sample_index][2]] for j, sample_index in enumerate(sample_data_indices)]
        result.extend(cells)
    last_row_index += i + 1

    return result, last_row_index

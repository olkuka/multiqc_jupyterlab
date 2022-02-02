
# multiqc_jupyterlab

JupyterLab extension for MultiQC

## Installation guide

```bash
conda create -n multiqc_jupyterlab_env -c conda-forge nodejs yarn python jupyterlab
conda activate multiqc_jupyterlab_env
git clone https://github.com/olkuka/multiqc_jupyterlab.git
cd multiqc_jupyterlab/multiqc_jupyterlab/MultiQC/
pip install .
cd ..
cd .. 
pip install .
```

## Usage 
The extension allows you to display MultiQC in one JupyterLab notebook cell for a given module and list of samples.

### Initialization 
To initialize MultiQC widget:
```bash
from multiqc_jupyterlab import MultiQC

m = MultiQC()
```

### Data
You can load data directly from analysis directory as in MultiQC or add data that is prepared by MultiQC and stored in multiqc_data/multiqc_data.json file.
```bash
m.load('./data') # load raw data from analysis directory

m.add('./multiqc_data') # add data prepared by MultiQC 
```

### Show available modules or samples
```bash
m.get_modules() # to see available modules

m.get_samples(module) # too see available samples for a given module 
```

### Show module
To see a module for a given subset of samples (not only from one analysis):
```bash
m.show(module, list_of_samples)
```

## Development Installation

Create a dev environment:
```bash
conda create -n multiqc_jupyterlab-dev -c conda-forge nodejs yarn python jupyterlab
conda activate multiqc_jupyterlab-dev
```

Install the python. This will also build the TS package.
```bash
pip install -e ".[test, examples]"
```

When developing your extensions, you need to manually enable your extensions with the
notebook / lab frontend. For lab, this is done by the command:

```
jupyter labextension develop --overwrite .
yarn run build
```

For classic notebook, you need to run:

```
jupyter nbextension install --sys-prefix --symlink --overwrite --py multiqc_jupyterlab
jupyter nbextension enable --sys-prefix --py multiqc_jupyterlab
```

Note that the `--symlink` flag doesn't work on Windows, so you will here have to run
the `install` command every time that you rebuild your extension. For certain installations
you might also need another flag instead of `--sys-prefix`, but we won't cover the meaning
of those flags here.

### How to see your changes
#### Typescript:
If you use JupyterLab to develop then you can watch the source directory and run JupyterLab at the same time in different
terminals to watch for changes in the extension's source and automatically rebuild the widget.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
yarn run watch
# Run JupyterLab in another terminal
jupyter lab
```

After a change wait for the build to finish and then refresh your browser and the changes should take effect.

#### Python:
If you make a change to the python code then you will need to restart the notebook kernel to have it take effect.

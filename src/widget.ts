// Copyright (c) Aleksandra Kukawka
// Distributed under the terms of the Modified BSD License.

import {
  DOMWidgetModel,
  DOMWidgetView,
  ISerializers,
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from './version';

export class MultiQCModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: MultiQCModel.model_name,
      _model_module: MultiQCModel.model_module,
      _model_module_version: MultiQCModel.model_module_version,
      _view_name: MultiQCModel.view_name,
      _view_module: MultiQCModel.view_module,
      _view_module_version: MultiQCModel.view_module_version,
      output: "Nothing's there!",
    };
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers,
    // Add any extra serializers here
  };

  static model_name = 'MultiQCModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'MultiQCView'; // Set to null if no view
  static view_module = MODULE_NAME; // Set to null if no view
  static view_module_version = MODULE_VERSION;
}

export class MultiQCView extends DOMWidgetView {
  render() {
    // this.show_plot();
    this.model.on("change:output", this.show_plot, this);
    this.model.on("change:output", this.get_samples, this);
  }

  show_plot = () => {
    this.model.save_changes();
  }

  get_samples = () => {
    this.model.save_changes();
  }
}

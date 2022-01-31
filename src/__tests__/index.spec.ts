// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// Add any needed widget imports here (or from controls)
// import {} from '@jupyter-widgets/base';

import { createTestModel } from './utils';

import { MultiQCModel } from '..';

describe('MultiQC', () => {
  describe('MultiQCModel', () => {
    it('should be createable', () => {
      const model = createTestModel(MultiQCModel);
      expect(model).toBeInstanceOf(MultiQCModel);
    });

    it('should be createable with a value', () => {
      const state = { value: 'Foo Bar!' };
      const model = createTestModel(MultiQCModel, state);
      expect(model).toBeInstanceOf(MultiQCModel);
      expect(model.get('value')).toEqual('Foo Bar!');
    });
  });
});

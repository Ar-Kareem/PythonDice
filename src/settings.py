

# SETTINGS
DEFAULT_SETTINGS = {
  'RV_TRUNC': False,  # if True, then RV will automatically truncate values to ints (replicate anydice behavior)
  'RV_IGNORE_ZERO_PROBS': False,  # if True, then RV remove P=0 vals when creating RVs (False by default in anydice)
  'DEFAULT_OUTPUT_WIDTH': 180,  # default width of output
  'DEFAULT_PRINT_FN': print,  # default print function
  'INTERNAL_CURR_DEPTH': 0,  # internal use only, for max_func_depth decorator
  'INTERNAL_CURR_DEPTH_WARNING_PRINTED': False,  # used with the above

  'position order': 'highest first',  # 'highest first' or 'lowest first'
  'explode depth': 2,  # can only be set to a positive integer (the default is 2)
  'maximum function depth': 10  # can only be set to a positive integer (the default is 10)
}
SETTINGS = DEFAULT_SETTINGS.copy()


def settings_set(name, value):
  if name == "position order":
    assert value in ("highest first", "lowest first"), 'position order must be "highest first" or "lowest first"'
  elif name == "explode depth":
    assert isinstance(value, int) and value > 0, '"explode depth" can only be set to a positive integer (the default is 2) got ' + str(value)
  elif name == "maximum function depth":
    assert isinstance(value, int) and value > 0, '"maximum function depth" can only be set to a positive integer (the default is 10) got ' + str(value)
  elif name in ('RV_TRUNC', 'RV_IGNORE_ZERO_PROBS'):
    if isinstance(value, str):
      assert value.lower() in ('true', 'false'), 'value must be "True" or "False"'
      value = value.lower() == 'true'
    assert isinstance(value, bool), 'value must be a boolean'
  elif name == 'DEFAULT_OUTPUT_WIDTH':
    assert isinstance(value, int) and value > 0, 'DEFAULT_OUTPUT_WIDTH must be a positive integer'
  elif name == 'DEFAULT_PRINT_FN':
    assert callable(value), 'DEFAULT_PRINT_FN must be a callable'
  else:
    assert False, f'invalid setting name: {name}'
  SETTINGS[name] = value


def settings_reset():
  SETTINGS.clear()
  SETTINGS.update(DEFAULT_SETTINGS)

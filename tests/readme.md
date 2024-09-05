# Testing

This readme should help with running all/specific tests and profiling tests.

## Collect Tests Only

```
pytest --collect-only
```

## Running Tests

### Run all tests

```
pytest
```

### Run only specific class

Replace `TestMyClass` with the class name.

```
pytest -k TestMyClass
```

### Command to run tests in a specific file

pytest tests/specific_feature_test.py

### Command to run a particular test class or method

pytest tests/test_module.py::TestClass  
pytest tests/test_module.py::test_function

## Profiling Tests

Get a list of the slowest 10 test durations over 1.0s long:

```
pytest --durations=10 --durations-min=1.0
```

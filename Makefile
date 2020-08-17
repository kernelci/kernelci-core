test:
	# Note that just running 'pytest' will not work here because there is no setup.py. See
	# https://docs.pytest.org/en/latest/pythonpath.html#invoking-pytest-versus-python-m-pytest
	python3 -m pytest tests

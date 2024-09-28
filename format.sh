#!/bin/bash

$(which black) *.py lib/*.py
$(which isort) *.py lib/*.py
# snips-calculator

This is a snips-calculator Python 3 snips app, generated using the `snips-template` tool
and exported to github. It is compatible with the format expected by the `snips-skill-server`

## Setup

This app requires some python dependencies to work properly, these are
listed in the `requirements.txt`. You can use the `setup.sh` script to
create a python virtualenv that will be recognized by the skill server
and install them in it.

## Executables

This dir contains a number of python executables named `action-*.py`.
One such file is generated per intent supported. These are standalone
executables and will perform a connection to MQTT and register on the
given intent using the `hermes-python` helper lib.

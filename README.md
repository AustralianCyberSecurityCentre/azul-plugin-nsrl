# Azul Plugin Nsrl

Query the NSRL database to determine if a file is publicly known.

## Development Installation

To install azul-plugin-nsrl for development run the command
(from the root directory of this project):

```bash
pip install -e .
```

## Usage

This plugin requires the `nsrl-lookup-server` to be available to query.

### Usage on local files:

When running the plugin manually on the command line, you will need to specify the `uri` config
to point to the nsrl-lookup-server:

```bash
azul-plugin-nsrl -c uri "http://nsrl-lookup-server:8080" malware.file
```

Example output on file that exists in NSRL:

    ----- AzulPluginNsrl results -----
    OK

    events (1)

    event for binary:E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:None
    {}
    output features:
        tag: NSRL

    Feature key:
    tag:  Any informational label about the sample

Example output on file that does not exist in NSRL:

    ----- AzulPluginNsrl results -----
    OK

Retrieving additional information can be achieved through the `details` config option:

```bash
azul-plugin-nsrl -c uri "http://nsrl-lookup-server:8080" -c details true malware.file
```

Example detailed output:

    ----- AzulPluginNsrl results -----
    OK

    events (1)

    event for binary:E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855:None
    {}
    output features:
        application_type: Operating System
                filename: WORD.EXE
                product: Microsoft Word
                        Word
        product_version: Microsoft Word - 2000
                        Word - 2000
                    tag: NSRL

    Feature key:
    application_type:  Application for the data source of this hash in NSRL
    filename:  Filenames for this hash in NSRL
    product:  Product info for the data source of this hash in NSRL
    product_version:  Product version info for the data source of this hash in NSRL
    tag:  Any informational label about the sample

## Automated usage in system:

To run the plugin in automated systems such as Azul, you must specify the `--server` argument and specify
the location of the dispatcher service.

```bash
azul-plugin-nsrl --server http://azul-dispatcher.localnet/
```

## Python Package management

This python package is managed using a `setup.py` and `pyproject.toml` file.

Standardisation of installing and testing the python package is handled through tox.
Tox commands include:

```bash
# Run all standard tox actions
tox
# Run linting only
tox -e style
# Run tests only
tox -e test
```

## Dependency management

Dependencies are managed in the requirements.txt, requirements_test.txt and debian.txt file.

The requirements files are the python package dependencies for normal use and specific ones for tests
(e.g pytest, black, flake8 are test only dependencies).

The debian.txt file manages the debian dependencies that need to be installed on development systems and docker images.

Sometimes the debian.txt file is insufficient and in this case the Dockerfile may need to be modified directly to
install complex dependencies.

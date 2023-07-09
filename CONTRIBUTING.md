# How to contribute

#### Did you find a bug?

* **Ensure the bug was not already reported** by searching under 
  [Issues](https://github.com/CyIC/warren/issues).
* If you're unable to find an open issue addressing the problem,
  [open a new one](https://github.com/CyIC/warren/issues/new). Be sure to include a **title 
  and clear description**, as much relevant information as possible, and a **code sample** or an **executable
  test case** demonstrating the expected behavior that is not occurring.

## Development Build
To build a development copy of this software you will need to prepare your box with the required applications.

### Python components
First up, since this application was built for python==3.11, ensure that you have an instance of [Python3.11] installed
on your dev environment.

Next you will need to clone the repo locally:
```commandline
git clone https://github.com/CyIC/warren.git
```

You will now need to ensure that you have [virtualenv](https://docs.python-guide.org/dev/virtualenvs/) installed 
locally.
```commandline
python -m virtualenv --help
```

If this command gives you an error, then you will need to install `virtualenv` locally.
```commandline
pip install virtualenv
```

This will install virtualenv to your computer, where you will need to initialize a virtualenv environment in your 
project folder.
```commandline
cd project_folder
virtualenv venv
```

This will create a folder in your current directory called venv, which will contain all the required libraries, scripts,
and executables to run an isolated Python environment specific to your project. To enable this environment you just
activate it by running:
```commandline
$ source venv/bin/activate
```

or on Windows commandline
```commandline
C:\project_folder> venv\Scripts\activate
```

In this new environment you can install python packages safely separate from other projects and the global libraries.
```commandline
$ pip install -r ./requirements.txt
```

If you are done working in the virtual environment for the moment, you can deactivate it:
```commandline
$ deactivate
```

### Prerequisites
These instructions are for development of this application.

Prerequisites are included in the `pyproject.toml` file.
```commandline
pip install ./
```

### Installing
All requirements are in the requirements.txt or pyproject.toml files.

### Building

This project is built to be ran without a complex building process, and is simple to run locally and in production using
the following command.

```commandline
python src/warrenBot/dchat.py
```

## Running the tests

Unit tests have been designed around `tox` to ensure proper coverage and execution in the proper environment. This
program is currently designed to run in `Python 3.11`.
```commandline
tox
```

### Break down into end-to-end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Check for PEP8 compliance using `flake8`. Flake8 environment has been configured with all the configuration options in
`tox.ini`

```commandline
tox -e flake8
```

## Deployment

Building, packaging and deployment is managed by Github pipeline and steps can be seen in the `.github-ci.yml` file at 
the root of this repo.

## Release instructions
1. First, ensure that all code reviews have been completed successfully. Ensure that the [CHANGELOG](./CHANGELOG.md) has 
   been updated with all the changes under the `Unreleased` section of the 
   [CHANGELOG](https://keepachangelog.com/en/1.0.0/). The `Unreleased` section will be updated during the final step 
   running `bumpversion`.
2. Ensure that `tox` and `tox -e flake8` run successfully. This will be confirmed during the pipeline causing the
   pipeline to fail if not successful.
3. Ensure all documentation has been updated.
4. If changes affect the Architecture of the application, ensure you add an ADR in the `docs/` folder.
5. Finally, use bumpversion to adhere to [Semantic Versioning](http://semver.org/). When 'bumped' bumpversion will 
   change all version numbers documented in the [.bumpversion.cfg](./.bumpversion.cfg) file; commit those changes, tag 
   the new commit with the new version number and sign the commit with the developers configured GPG key.
6. Build the application according to the [Building](#Building) section, archive, zip and upload the package to Github 
   for production downloading.

```commandline
bumpversion (major|minor|patch)
```

[python3.11]: https://www.python.org/downloads/release/python-3110/
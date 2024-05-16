
CivicLens DOCS
==================

CivicLens is a platform designed to abstract procedures and bureaucracy from the public commenting process. This site serves as internal documentation for current (and future!) contributors to the project.


## Contributing

CivicLens is currently under active development. This site will continue to be updated to reflect additional features.

CivicLens requires `poetry` (see [here](https://python-poetry.org/) for more information) to run. To install the necessary dependencies, run `poetry run` from the project directory. You can the run the project locally by prefixing python commands with `poetry run` or by using `poetry shell` to open activate the virtual environment.


To run the test suite, run `poetry run pytest`.

### Set Up Pre-Commit Hooks
To set up pre-commit hooks that lint and test before pushing to the repo, execute the following commands in your command line locally:
`pip install pre-commit` to install the pre-commit library.
`pre-commit install` to create the hooks in your .git/hooks/pre-commit directory.

### Set Up Environment Variable for API Key
To obtain a regulations.gov API key, request one on [the API page](https://open.gsa.gov/api/regulationsgov/#getting-started)

For security reasons, we want to use an Environment Variable to store the API key. This repository is set up to access an ignored .env file in the CivicLens folder. To use functions which access the API, within the .env file you should set ```REG_GOV_API_KEY=``` to the API key you requested.

For testing or temporary purposes, you can also set ```REG_GOV_API_KEY="DEMO_KEY"```. This is a demo functionality built into regulations.gov for very limited API access.

We also use the .env file to store relevant sensitive information pertaining to our database and web framework. We extract all of this information in the ```utils/constants.py``` file.

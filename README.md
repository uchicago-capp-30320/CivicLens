
# CivicLens

![logo](docs/assets/logo.png)

CivicLens is a platform designed to abstract procedures and bureaucracy from the public commenting process. Our aim is to promote effective, accessible public commenting while providing transparency into the process, use plain language and human ideas to discuss federal rulemaking, and educate users on how commenting impacts government.

![Test badge](https://github.com/uchicago-capp-30320/CivicLens/actions/workflows/lint-test.yml/badge.svg)

## Public Commenting

If you'd like to learn more about federal commenting in the meantime, we’re compiling a list of resources to explore in addition to our platform.
- [Regulations.gov](https://www.regulations.gov/): The US government’s current tool for collecting comments on federal rulemaking. See the [FAQ](https://www.regulations.gov/faq) or this [page](https://www.regulations.gov/learn) for an introduction to federal regulations.
- [Public Comment Project](https://publiccommentproject.org/how-to): A short guide to writing effective public comments.
- [Library of Congress](https://guides.loc.gov/trace-federal-regulations/docket-information): How to trace regulations through the rulemaking process.


## Development

CivicLens is currently under active development.

CivicLens requires `poetry` (see [here](https://python-poetry.org/) for more information) to run. To install the necessary dependencies, run `poetry run` from the project directory. You can the run the project locally by prefixing python commands with `poetry run` or by using `poetry shell` to open activate the virtual environment.

To run the test suite, run `poetry run pytest`.

## Set Up Pre-Commit Hooks
To set up pre-commit hooks that lint and test before pushing to the repo, execute the following commands in your command line locally:
`pip install pre-commit` to install the pre-commit library.
`pre-commit install` to create the hooks in your .git/hooks/pre-commit directory.

## Set Up Environment Variable for API Key
To obtain a regulations.gov API key, request one on [the API page](https://open.gsa.gov/api/regulationsgov/#getting-started)

For security reasons, we want to use an Environment Variable to store the API key. This repository is set up to access an ignored .env file in the CivicLens folder. To use functions which access the API, within the .env file you should set ```REG_GOV_API_KEY=``` to the API key you requested.

For testing or temporary purposes, you can also set ```REG_GOV_API_KEY="DEMO_KEY"```. This is a demo functionality built into regulations.gov for very limited API access.

We also use the .env file to store relevant sensitive information pertaining to our database and web framework. We extract all of this information in the ```utils/constants.py``` file.

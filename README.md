
# CivicLens

![logo](docs/assets/logo.png)

CivicLens is a platform designed to abstract procedures and bureaucracy from the public commenting process. Our aim is to promote effective, accessible public commenting while providing transparency into the process, use plain language and human ideas to discuss federal rulemaking, and educate users on how commenting impacts government.

![Test badge](https://github.com/uchicago-capp-30320/CivicLens/actions/workflows/lint-test.yml/badge.svg)

## Public Commenting

If you'd like to learn more about federal commenting here is a list of resources to explore in addition to our platform.
- [Regulations.gov](https://www.regulations.gov/): The US government’s current tool for collecting comments on federal rulemaking. See the [FAQ](https://www.regulations.gov/faq) or this [page](https://www.regulations.gov/learn) for an introduction to federal regulations.
- [Public Comment Project](https://publiccommentproject.org/how-to): A short guide to writing effective public comments.
- [Library of Congress](https://guides.loc.gov/trace-federal-regulations/docket-information): How to trace regulations through the rulemaking process.

## Installation
This project uses Poetry to manage dependencies. 

1. [Install Poetry to Local Machine](https://python-poetry.org/docs/)

2. Clone the Project Repository via SSH

```bash
git clone https://github.com/uchicago-capp-30320/CivicLens.git
```

3. Install Virtual Environment and Dependencies in the Project Directory

```bash
poetry shell
poetry install
```

## Usage
This must be run in the Poetry virtual environment. 
Upon completion of above installation requirements the virtual environment can be activated by simply running:

```bash
poetry shell
```


**Deploy the Site Locally**

Navigate to the CivicLens/civiclens directory, then run the following command from the terminal:

```bash
python manage.py runserver
```

**Running Scripts**
You can the run the project locally by prefixing python commands with `poetry run` or by using `poetry shell` to open activate the virtual environment and then running `python filename.py`
To run the test suite, run `poetry run pytest`.


## Development
CivicLens is currently under active development with a v1 of the project live at [civic-lens.org](https://civic-lens.org/).

We welcome contributors who are interested in developing the future of this project! You can see our documentation and community guidelines [here](https://uchicago-capp-30320.github.io/CivicLens/) to get started. To begin contributing, create an issue on github, submit a PR, and it will be reviewed by a member of our team.

### Set Up Pre-Commit Hooks
To set up pre-commit hooks that lint and test before pushing to the repo, execute the following commands in your command line locally:

`pip install pre-commit` to install the pre-commit library.
`pre-commit install` to create the hooks in your .git/hooks/pre-commit directory.

These will ensure that any pull request passes linting checks.

### Environmental Variables
To run code that accesses the database or uses the django secret key you will need to create a `.env` file in the root directory of the repo. The information to enter into the .env file can be shared securely if necessary.

### Dev Team
This project was created by a group of University of Chicago Master of Science in Computational Analysis and Public Policy students. We made this site as a class project for Software Engineering for Civic Tech, taught by Professor James Turk.

Team: Claire Boyd, Abe Burton, John Christenson, Andrew Dunn, Jack Gibson, Gegory Ho, and Reza Pratama

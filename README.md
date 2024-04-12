# CivicLens

![logo](docs/assets/big_logo.png)

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

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


## Set Up Environment Variable for API Key
To obtain a regulations.gov API key, request one on [the API page](https://open.gsa.gov/api/regulationsgov/#getting-started)

For security reasons, we would want to use an Environment Variable to store the API key.

To set up the API key as an environment variable:

for MacOS and Linux (bash):
```bash
$ export REG_GOV_API_KEY="your_token_here"
$ source ~/.bashrc
```

for MacOS and Linux (zsh):
```zsh
$ echo 'export REG_GOV_API_KEY="your_token_here"' >> ~/.zshenv
```

for Windows:
Run the following command to set the environment variable in the current session:
```bash
$ set REG_GOV_API_KEY=your_token_here
```

For testing or temporary purposes, you can also set ```REG_GOV_API_KEY="DEMO_KEY"```. This is a demo functionality built into regulations.gov for cursory API access. 


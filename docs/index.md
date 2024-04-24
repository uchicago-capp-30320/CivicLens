
CivicLens DOCS
==================

CivicLens is a platform designed to abstract procedures and bureaucracy from the public commenting process. This site serves as internal documentation for current (and future!) contributors to the project. 


## Contributing

CivicLens is currently under active development, this site will continue to be updated to reflect additional features. 

CivicLens requires `poetry` (see [here](https://python-poetry.org/) for more information) to run. To install the necessary dependencies, run `poetry run` from the project directory. You can the run the project locally by prefixing python commands with `poetry run` or by using `poetry shell` to open activate the virtual environment. 

To run the test suite, run `poetry run pytest`. 

### Set Up Environment Variable for API Key
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






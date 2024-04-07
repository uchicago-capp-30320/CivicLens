##### Set Up Environment Variable for API Key
For security reasons, we would want to use an Environment Variable to store the REgulations.gov API key.

To set up the API key token as an environment variable:

for MacOS and Linux (bash):
```bash
$ export REG_GOV_API_KEY="your_token_here"
$ source ~/.bashrc
```

for MacOS and Linux (zsh):
```zsh
$ echo 'export ENV_VAR="your_token_here"' >> ~/.zshenv
```

for Windows:
Run the following command to set the environment variable in the current session:
```bash
$ set REG_GOV_API_KEY=your_token_here
```
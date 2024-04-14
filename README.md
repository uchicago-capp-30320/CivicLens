##### Set Up Environment Variable for API Key
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
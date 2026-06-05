# onet_role_dna

![PyPI version](https://img.shields.io/pypi/v/onet_role_dna.svg)

A Python package for analyzing and modeling occupational role DNA from O*NET data.

* [GitHub](https://github.com/olwordeaux/onet_role_dna/) | [PyPI](https://pypi.org/project/onet_role_dna/) | [Documentation](https://olwordeaux.github.io/onet_role_dna/)
* Created by [Andy Eick](https://audrey.feldroy.com/) | GitHub [@olwordeaux](https://github.com/olwordeaux) | PyPI [@andyeick](https://pypi.org/user/andyeick/)
* MIT License

## Features

* TODO

## Documentation

Documentation is built with [Zensical](https://zensical.org/) and deployed to GitHub Pages.

* **Live site:** https://olwordeaux.github.io/onet_role_dna/
* **Preview locally:** `just docs-serve` (serves at http://localhost:8000)
* **Build:** `just docs-build`

API documentation is auto-generated from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

Docs deploy automatically on push to `main` via GitHub Actions. To enable this, go to your repo's Settings > Pages and set the source to **GitHub Actions**.

## Development

To set up for local development:

```bash
# Clone your fork
git clone git@github.com:your_username/onet_role_dna.git
cd onet_role_dna

# Install in editable mode with live updates
uv tool install --editable .
```

This installs the CLI globally but with live updates - any changes you make to the source code are immediately available when you run `onet_role_dna`.

Run tests:

```bash
uv run pytest
```

Run quality checks (format, lint, type check, test):

```bash
just qa
```

## Author

onet_role_dna was created in 2026 by Andy Eick.

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.

# Repository Guidelines

## Project Structure & Module Organization

This repository is currently a minimal MIT-licensed project: it contains
`LICENSE` and no application code, build configuration, or test suite yet.
Keep future additions easy to discover by using a conventional layout:

- `src/` for production code or training utilities.
- `tests/` for automated tests that mirror the relevant `src/` paths.
- `assets/` for small, versioned non-code inputs; do not commit large generated
  models, datasets, or credentials.
- `docs/` for durable user or design documentation.

Document any new top-level directory in the README when it is introduced.

## Build, Test, and Development Commands

No build, run, lint, or test commands are configured at present. Contributors
who add a language or framework must also add reproducible project commands
and document them in `README.md`. Prefer a small, explicit command set, such
as `npm run lint`, `npm test`, or `python -m pytest`, rather than relying on
unrecorded local setup.

## Coding Style & Naming Conventions

Follow the formatter and linter native to the language introduced, and commit
their configuration with the code. Use 4 spaces for Python and the formatter's
default indentation for other languages. Name files and directories in
lowercase `snake_case` unless the selected ecosystem has an established
alternative; use descriptive names such as `data_preparation.py` rather than
`helpers.py`. Keep functions focused and avoid committing generated output.

## Testing Guidelines

Add tests alongside each new functional area and use names that state expected
behavior, for example `test_rejects_empty_training_data`. Tests must run from a
fresh checkout using the documented command. Include regression tests for bug
fixes and avoid tests that require private credentials, network access, or
large external artifacts.

## Commit & Pull Request Guidelines

The Git history currently has only an initial commit, so no established commit
format exists. Use concise imperative subjects, for example `Add dataset
validation`, and keep each commit narrowly scoped. Pull requests should
describe the change, explain validation performed, link relevant issues, and
include screenshots or sample output when a user-visible workflow changes.

## Security & Configuration

Never commit API keys, tokens, private datasets, model weights, or local
environment files. Provide safe templates such as `.env.example` and document
required variables without including their values.

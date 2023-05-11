# NRL to R4 Conversion

Converts the core NRL event to a valid FHIR R4 DocumentReference

- [For users](#for-users)
  - [Installation](#installation)
  - [Usage](#usage)
- [For developer](#for-developers)
  - [In General](#in-general)
  - [First time setup](#first-time-setup)
  - [Every time you start a new session](#every-time-you-start-a-new-session)
  - [Workflow](#workflow)
    - [Increment Version](#increment-version)
    - [Features](#features)
    - [Releases](#releases)
    - [Publish to PyPI](#publish-to-pypi)
  - [Tests](#tests)
    - [Unit](#unit)

# For Users of this package

## Installation from PyPI

UPDATE ME

## Usage

You give it an "NRL Document Reference" (here we describe as a `document_pointer`) and
you get back an "R4 DocumentReference" (here we described as a `document_reference`).

Both input and output are `dict` objects. You must also supply an NHS Number, expected
to be consistent with the logical ID of the `document_pointer` - however we do not
validate this.

```python
from nrlf_converter import nrl_to_r4

document_reference = nrl_to_r4(document_pointer={...}, nhs_number="12345678910")
```

If the NRL-to-R4 conversion is unsuccessful, one of the following errors is raised:

- `ValidationError`: Your `document_pointer` has broken our data contract. It probably means
  that we'll need to update our data contract and add a new test case for our integration tests.
- `BadRelatesTo`: You `document_pointer` is superseding ("replaces") another, but the fields are inconsistent.
- `CustodianError`: We were unable to parse an ODS code from your `document_pointer.custodian` field.
  It probably means that we'll need to update our data contract and add a new test case for our integration tests.

You can catch these errors by importing them from the top-level module:

```python
from nrlf_converter import nrl_to_r4, ValidationError, BadRelatesTo, CustodianError

try:
  document_reference = nrl_to_r4(document_pointer={...}, nhs_number="12345678910")
except ValidationError:
  ...
except BadRelatesTo:
  ...
except CustodianError:
  ...
```

Furthermore, just because the conversion is successful doesn't mean that `document_reference` will be valid in NRLF. If your receive any rejections, it is likely that we'll need to update our data contract and add a new test case for our integration tests.

# For Developers of this package

## In general

```console
make help
```

> 💡 HINT: You might find it extra helpful to have [bash-completion](https://github.com/scop/bash-completion)
> installed which will tab-complete the `make` commands for you.
>
> > Mac Users:
> >
> > ```
> > brew install bash-completion@2
> > ```
> >
> > and add the following line near the top of `~/.bash_profile`:
> >
> > ```
> > [[ -r "/usr/local/etc/profile.d/bash_completion.sh" ]] && . "/usr/local/etc/profile.d/bash_completion.sh"
> > ```

### First time setup

```console
make venv--install
```

### Every time you start a new session

```console
poetry shell
```

or without a new shell

```console
source .venv/bin/activate
```

## Workflow

### Features

Create features branches according to the naming convention:

```
feature/<JIRA-TICKET-ID>-<short_camel_case_description>
```

If there has been a recent release then you will need to bump `[tool.poetry] version` in `pyproject.toml` to be semantically greater than the latest tag. Github actions will remind you of this when you create a Pull Request.

Note that you can check that value of the latest tag with:

```console
make pkg--helpers--latest-tag
```

### Increment version

Increment patch version (`a.b.c --> a.b.(c+1)`):

```console
make pkg--helpers--increment-version--patch
```

Increment minor version (`a.b.c --> a.(b+1).c`):

```console
make pkg--helpers--increment-version--minor
```

### Releases

Create a release:

```console
make pkg--helpers--create-release-from-current-version
```

A tag will be created tag based on the version specified in the `pyproject.toml`, then pushed to GitHub in order to trigger a release.

### Publish to PyPI

UPDATE

## Tests

### Unit

```
make test--unit
```

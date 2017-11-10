# bib-lod-ui
Web app for publishing bibliographic Linked Open Data as HTML pages and RDF serializations

Used for publishing the Finnish national bibliograhpy Fennica online as
Linked Open Data.

## Dependencies and installation

Needs Python 3.5+.

Clone the repository.

Create a virtualenv:

    python3 -m venv venv

Install the dependencies:

    venv/bin/pip install wheel
    venv/bin/pip install -r requirements.txt

## Running

    ./run.py # run in debug mode

or

    ./production.py # run in production mode


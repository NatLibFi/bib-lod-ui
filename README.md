# bib-lod-ui
Web app for publishing bibliographic Linked Open Data as HTML pages and RDF serializations

Used for publishing the Finnish national bibliograhpy Fennica online as
Linked Open Data.

## Dependencies and installation

Needs Python 3.5 and the `venv` module. On Debian/Ubuntu:

    apt-get install python3-venv

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

# License

The code in this repository is licensed under the Apache license, version
2.0. See [LICENSE](LICENSE) for details. Exceptions:

The static content under `biblodui/static` consists partly of libraries we
depend on, such as Bootstrap and jQuery. These have their own licenses (MIT
License mostly), see the file headers for details.

The logos under `biblodui/static/img` are (c) National Library of Finland
and require permission to use.

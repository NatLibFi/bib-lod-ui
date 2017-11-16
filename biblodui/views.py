from flask import render_template, abort
from flask_rdf.flask import returns_rdf

from biblodui import app, model


@app.route('/')
@app.route('/index')
def index():
    res = model.Work('http://urn.fi/URN:NBN:fi:bib:me:W00009584100')
    return render_template('index.html', title=res.name(), res=res)


@app.route('/bib/me/<resourceid>')
def bib_resource(resourceid):
    res = model.Work('http://urn.fi/URN:NBN:fi:bib:me:%s' % resourceid)
    if not res.exists():
        abort(404)
    return render_template('index.html', title=res.name(), res=res)

@app.route('/au/pn/<personid>')
def person_resource(personid):
    res = model.Resource('http://urn.fi/URN:NBN:fi:au:pn:%s' % personid)
    if not res.exists():
        abort(404)
    return render_template('index.html', title=res.name(), res=res)

@app.route('/rdf')
@returns_rdf
def rdf():
    res = model.Resource('http://urn.fi/URN:NBN:fi:bib:me:W00009584100')
    return res.graph

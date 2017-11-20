from flask import render_template, abort, redirect, request
from flask_rdf import wants_rdf
from flask_rdf.flask import returns_rdf

from biblodui import app, model


@app.route('/')
@app.route('/index')
@returns_rdf
def index():
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:W00009584100')
    if wants_rdf(request.headers.get('Accept', '')):
        return res.graph
    else:
        return render_template('resource.html', title=res.name(), res=res)


@app.route('/bib/me/<resourceid>')
@returns_rdf
def bib_resource(resourceid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:%s' % resourceid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        return res.graph
    else:
        return render_template('resource.html', title=res.name(), res=res)

@app.route('/bib/me/I<instanceid>')
@returns_rdf
def bib_instance(instanceid):
    inst = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:I%s' % instanceid)
    if not inst.exists():
        abort(404)
    work = inst.get_work()
    return redirect("%s#I%s" % (work.url(), instanceid))

@app.route('/au/pn/<personid>')
@returns_rdf
def person_resource(personid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:au:pn:%s' % personid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        return res.graph
    else:
        return render_template('resource.html', title=res.name(), res=res)

@app.route('/yso/<conceptid>')
@returns_rdf
def concept_resource(conceptid):
    res = model.get_resource('http://www.yso.fi/onto/yso/%s' % conceptid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        return res.graph
    else:
        return render_template('resource.html', title=res.name(), res=res)


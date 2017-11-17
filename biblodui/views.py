from flask import render_template, abort, redirect
from flask_rdf.flask import returns_rdf

from biblodui import app, model


@app.route('/')
@app.route('/index')
def index():
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:W00009584100')
    return render_template('resource.html', title=res.name(), res=res)


@app.route('/bib/me/<resourceid>')
def bib_resource(resourceid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:%s' % resourceid)
    if not res.exists():
        abort(404)
    return render_template('resource.html', title=res.name(), res=res)

@app.route('/bib/me/I<instanceid>')
def bib_instance(instanceid):
    inst = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:I%s' % instanceid)
    if not inst.exists():
        abort(404)
    work = inst.get_work()
    return redirect("%s#I%s" % (work.url(), instanceid))

@app.route('/au/pn/<personid>')
def person_resource(personid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:au:pn:%s' % personid)
    if not res.exists():
        abort(404)
    return render_template('resource.html', title=res.name(), res=res)

@app.route('/yso/<conceptid>')
def concept_resource(conceptid):
    res = model.get_resource('http://www.yso.fi/onto/yso/%s' % conceptid)
    if not res.exists():
        abort(404)
    return render_template('resource.html', title=res.name(), res=res)

@app.route('/rdf')
@returns_rdf
def rdf():
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:W00009584100')
    return res.graph

from flask import render_template, abort, redirect, request, make_response
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

@app.route('/bib/me/<string(length=12):resourceid>')
@returns_rdf
def bib_resource(resourceid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:%s' % resourceid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        return res.graph
    else:
        response = make_response(render_template('resource.html', title=res.name(), res=res))
        response.headers['Vary'] = 'Accept'
        return response

@app.route('/bib/me/<resourceid>.<format>')
def bib_resource_format(resourceid, format):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:%s' % resourceid)
    if not res.exists():
        abort(404)
    if format == 'rdf':
        response = make_response(res.graph.serialize(format='xml'))
        response.headers['Content-Type'] = 'application/rdf+xml'
    elif format == 'ttl':
        response = make_response(res.graph.serialize(format='turtle'))
        response.headers['Content-Type'] = 'text/turtle'
    elif format == 'nt':
        response = make_response(res.graph.serialize(format='nt'))
        response.headers['Content-Type'] = 'application/n-triples'
    elif format == 'json':
        context = {"@vocab": "http://schema.org/"}
        response = make_response(res.graph.serialize(format='json-ld', context=context))
        response.headers['Content-Type'] = 'application/json'
    elif format == 'html':
        response = make_response(render_template('resource.html', title=res.name(), res=res))
    else:
        abort(404)
    return response

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
        response = make_response(render_template('resource.html', title=res.name(), res=res))
        response.headers['Vary'] = 'Accept'
        return response

@app.route('/yso/<conceptid>')
@returns_rdf
def concept_resource(conceptid):
    res = model.get_resource('http://www.yso.fi/onto/yso/%s' % conceptid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        return res.graph
    else:
        response = make_response(render_template('resource.html', title=res.name(), res=res))
        response.headers['Vary'] = 'Accept'
        return response


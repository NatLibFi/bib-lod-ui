from flask import render_template, abort, redirect, request, make_response
from flask_rdf import wants_rdf
from flask_rdf.flask import returns_rdf
from werkzeug.routing import BaseConverter

from biblodui import app, model


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


def make_format_response(res, fmt):
    if fmt == 'rdf':
        response = make_response(res.serialize('xml'))
        response.headers['Content-Type'] = 'application/rdf+xml'
    elif fmt == 'ttl':
        response = make_response(res.serialize('turtle'))
        response.headers['Content-Type'] = 'text/turtle'
    elif fmt == 'nt':
        response = make_response(res.serialize('nt'))
        response.headers['Content-Type'] = 'application/n-triples'
    elif fmt == 'json':
        response = make_response(res.serialize('json-ld'))
        response.headers['Content-Type'] = 'application/json'
    elif fmt == 'html':
        response = make_response(render_template('resource.html', title=res.name(), res=res))
    else:
        abort(404)
    return response


@app.route('/')
@app.route('/index')
@returns_rdf
def index():
    collections = model.Collections()
    conceptschemes = model.ConceptSchemes()
    return render_template('index.html', title='Index', collections=collections, conceptschemes=conceptschemes)

@app.route('/bib/me/<string(length=12):resourceid>')
@returns_rdf
def bib_resource(resourceid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:%s' % resourceid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        data = res.graph
    else:
        data = render_template('resource.html', title=res.name(), res=res)
    return (data, 200, {'Vary': 'Accept'})

@app.route('/bib/me/<resourceid>.<fmt>')
def bib_resource_format(resourceid, fmt):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:%s' % resourceid)
    if not res.exists():
        abort(404)
    return make_format_response(res, fmt)

@app.route('/bib/me/I<instanceid>')
@returns_rdf
def bib_instance(instanceid):
    inst = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:I%s' % instanceid)
    if not inst.exists():
        abort(404)
    work = inst.get_work()
    return redirect("%s#I%s" % (work.url(), instanceid))

@app.route('/bib/me/C<collectionid>')
@returns_rdf
def bib_collection(collectionid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:bib:me:C%s' % collectionid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        data = res.graph
    else:
        data = render_template('resource.html', title=res.name(), res=res)
    return (data, 200, {'Vary': 'Accept'})

@app.route('/au/pn/<regex("[0-9]+"):personid>')
@returns_rdf
def person_resource(personid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:au:pn:%s' % personid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        data = res.graph
    else:
        data = render_template('resource.html', title=res.name(), res=res)
    return (data, 200, {'Vary': 'Accept'})

@app.route('/au/pn/<regex("[0-9]+"):personid>.<fmt>')
def person_resource_format(personid, fmt):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:au:pn:%s' % personid)
    if not res.exists():
        abort(404)
    return make_format_response(res, fmt)

@app.route('/au/cn/<regex("[0-9]+A"):organizationid>')
@returns_rdf
def organization_resource(organizationid):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:au:cn:%s' % organizationid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        data = res.graph
    else:
        data = render_template('resource.html', title=res.name(), res=res)
    return (data, 200, {'Vary': 'Accept'})

@app.route('/au/cn/<regex("[0-9]+A"):organizationid>.<fmt>')
def organization_resource_format(organizationid, fmt):
    res = model.get_resource('http://urn.fi/URN:NBN:fi:au:cn:%s' % organizationid)
    if not res.exists():
        abort(404)
    return make_format_response(res, fmt)


@app.route('/yso/<regex("p[0-9]+"):conceptid>')
@returns_rdf
def concept_resource(conceptid):
    res = model.get_resource('http://www.yso.fi/onto/yso/%s' % conceptid)
    if not res.exists():
        abort(404)
    if wants_rdf(request.headers.get('Accept', '')):
        return res.graph
    response = make_response(render_template('resource.html', title=res.name(), res=res))
    response.headers['Vary'] = 'Accept'
    return response

@app.route('/yso/<regex("p[0-9]+"):conceptid>.<fmt>')
def concept_resource_format(conceptid, fmt):
    res = model.get_resource('http://www.yso.fi/onto/yso/%s' % conceptid)
    if not res.exists():
        abort(404)
    return make_format_response(res, fmt)

@app.route('/bib/opensearch')
def opensearch():
    query = request.args.get('query')
    search = model.Search(query)
    response = make_response(render_template('opensearch.xml', search=search, base_url=request.base_url, url_root=request.url_root))
    response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
    return response

@app.route('/bib/opensearchdescription.xml')
def opensearchdescription():
    response = make_response(render_template('opensearchdescription.xml', url_root=request.url_root))
    response.headers['Content-Type'] = 'application/opensearchdescription+xml; charset=utf-8'
    return response

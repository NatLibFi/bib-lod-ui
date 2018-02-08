from collections import OrderedDict
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, BNode
from rdflib.namespace import SKOS, DC

import os
import os.path

SCHEMA = Namespace('http://schema.org/')
RDAU = Namespace('http://rdaregistry.info/Elements/u/')

ENDPOINT = "http://data.nationallibrary.fi/bib/sparql"

def get_resource(uri, graph=None):
    """return a Resource object of the appropriate class for the given URI"""
    if uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:W'):
        cls = Work
    elif uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:I'):
        cls = Instance
    elif uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:P'):
        cls = Person
    elif uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:O'):
        cls = Organization
    elif uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:C'):
        cls = Collection
    elif uri.startswith('http://urn.fi/URN:NBN:fi:au:pn:'):
        cls = Person
    elif uri == 'http://urn.fi/URN:NBN:fi:au:cn:':
        cls = ConceptScheme
    elif uri.startswith('http://urn.fi/URN:NBN:fi:au:cn:'):
        cls = Organization
    elif uri == 'http://www.yso.fi/onto/yso/':
        cls = ConceptScheme
    elif uri == 'http://www.yso.fi/onto/yso/places':
        cls = ConceptScheme
    elif uri.startswith('http://www.yso.fi/onto/yso/'):
        cls = Concept
    else:
        # not a recognized URI pattern, just use a plain Resource
        cls = Resource
    return cls(uri, graph)
    
def uri_to_url(uri):
    url = uri
    url = url.replace('http://urn.fi/URN:NBN:fi:bib:me:','/bib/me/')
    url = url.replace('http://urn.fi/URN:NBN:fi:au:pn:','/au/pn/')
    url = url.replace('http://urn.fi/URN:NBN:fi:au:cn:','/au/cn/')
    url = url.replace('http://www.yso.fi/onto/yso/','/yso/')
    return url


class Resource:
    prefixes = """
      PREFIX schema: <http://schema.org/>
      PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    """

    query = """
      %(prefixes)s
      
      CONSTRUCT {
        <%(uri)s> ?p ?o .
        ?o schema:name ?oname ;
           skos:prefLabel ?olabel .
        ?wab schema:about <%(uri)s> ;
             schema:name ?wabname .
      }
      WHERE {
        {
          <%(uri)s> ?p ?o .
          OPTIONAL {
            { ?o schema:name ?oname }
            UNION
            { ?o skos:prefLabel ?olabel }
          }
        }
        UNION
        { # works about
          ?wab schema:about <%(uri)s> .
          ?wab schema:name ?wabname .
        }
      }
    """

    def __init__(self, uri, graph = None):
        if isinstance(uri, URIRef) or isinstance(uri, BNode):
            self.uri = uri
        else:
            self.uri = URIRef(uri)

        if graph is not None:
            self.graph = graph
        else:
            self.graph = self.query_for_graph()
    
    def query_for_graph(self):
        sparql = SPARQLWrapper(ENDPOINT)
        sparql.setQuery(self.query % {'uri': self.uri, 'prefixes': self.prefixes})
        graph = Graph()
        graph.parse(sparql.query().response)
        return graph
    
    def exists(self):
        return len(self.graph) > 0
    
    def typename(self):
        return self.__class__.__name__

    def name(self):
        props = (SCHEMA.name, SKOS.prefLabel, DC.title, RDFS.label)
        labels = self.graph.preferredLabel(self.uri, lang='en', labelProperties=props)
        if len(labels) > 0:
            return labels[0][1]

        labels = self.graph.preferredLabel(self.uri, labelProperties=props)
        if len(labels) > 0:
            return labels[0][1]
        
        return "<%s>" % self.uri
    
    def __str__(self):
        return self.name()
      
    def sort_key(self):
        return self.name().lower()
    
    def url(self):
        if isinstance(self.uri, BNode):
            return None
        return uri_to_url(self.uri)
    
    def localname(self):
        ln = self.uri.split(':')[-1].split('/')[-1]
        if ln == '':
            return 'index'
        return ln
    
    def property_name(self, prop):
        return prop.split('/')[-1].split('#')[-1] # local name
    
    def properties(self, uri=None):
        if uri is None:
            uri = self.uri
        propvals = OrderedDict() # key: property URIRef, value: list of values
        props = set([prop for prop in self.graph.predicates(uri, None)
                     if prop not in (RDF.type, SCHEMA.workExample, SCHEMA.exampleOfWork)])
        for prop in sorted(props, key=lambda prop: self.property_name(prop).lower()):
            propname = self.property_name(prop)
            propvals[propname] = []
            for obj in self.graph.objects(uri, prop):
                if isinstance(obj, URIRef) or self.graph.value(obj, SCHEMA.name, None, any=True) is not None:
                    val = Resource(obj, self.graph)
                elif isinstance(obj, BNode):
                    val = self.properties(obj)
                else:
                    val = obj
                propvals[propname].append(val)
            propvals[propname].sort(key=lambda val: str(val).lower())
        return propvals
    
    def has_instances(self):
        return False
    
    def has_works_about(self):
        return self.graph.value(None, SCHEMA.about, self.uri, any=True) is not None
    
    def works_about(self):
        works = [Work(work, self.graph) for work in self.graph.subjects(SCHEMA.about, self.uri)]
        works.sort(key=lambda w: w.sort_key())
        return works

    def has_authored_works(self):
        return False

    def has_contributed_works(self):
        return False
      
    def is_agent(self):
        return False
    
    def serialize(self, fmt):
        if fmt == 'json-ld':
            context = {"@vocab": SCHEMA, "rdau": RDAU, "skos": SKOS, "skos:prefLabel": {"@container": "@language"} }
            return self.graph.serialize(format='json-ld', context=context)
        return self.graph.serialize(format=fmt)
        

class Work (Resource):
    query = """
      %(prefixes)s
      
      CONSTRUCT {
        <%(uri)s> ?p ?o .
        ?o schema:name ?oname ;
           skos:prefLabel ?olabel .
        ?wab schema:about <%(uri)s> ;
             schema:name ?wabname .
        ?inst ?instprop ?instval .
        ?instval schema:name ?instvalName ;
                 skos:prefLabel ?instvalLabel .
        ?id ?idprop ?idval .
        ?pubEvent schema:location ?pubPlace ;
                  schema:organizer ?org .
        ?pubPlace schema:name ?pubPlaceName .
        ?org schema:name ?orgName .
      }
      WHERE {
        {
          <%(uri)s> ?p ?o .
          OPTIONAL {
            { ?o schema:name ?oname }
            UNION
            { ?o skos:prefLabel ?olabel }
          }
        }
        UNION
        { # works about
          ?wab schema:about <%(uri)s> ;
               schema:name ?wabname .
        }
        UNION
        { # instances
          { <%(uri)s> schema:workExample ?inst }
          OPTIONAL {
            {
              ?inst ?instprop ?instval .
              OPTIONAL {
                { ?instval schema:name ?instvalName }
                UNION
                { ?instval skos:prefLabel ?instvalLabel }
              }
            }
            UNION
            { # identifiers
              ?inst schema:identifier ?id .
              ?id ?idprop ?idval .
            }
            UNION
            { # publication events
              ?inst schema:publication ?pubEvent .
              OPTIONAL {
                ?pubEvent schema:location ?pubPlace .
                ?pubPlace schema:name ?pubPlaceName .
              }
              OPTIONAL {
                ?pubEvent schema:organizer ?org .
                ?org schema:name ?orgName .
              }
            }
          }
        }
      }
    """

    def has_instances(self):
        return self.graph.value(self.uri, SCHEMA.workExample, None, any=True) is not None

    def instances(self):
        insts = [Instance(inst, self.graph) for inst in self.graph.objects(self.uri, SCHEMA.workExample)]
        insts.sort(key=lambda inst: inst.sort_key())
        return insts

class Instance (Resource):

    def edition_info(self):
        date_published = self.graph.value(self.uri, SCHEMA.datePublished, None)
        if date_published is None:
          date_published = "-"
        publisher_uri = self.graph.value(self.uri, SCHEMA.publisher, None)
        if publisher_uri is not None:
          publisher_name = Resource(publisher_uri, self.graph).name()
          name = "%s : %s" % (date_published, publisher_name)
        else:
          name = date_published
        if (self.uri, SCHEMA.bookFormat, SCHEMA.EBook) in self.graph:
            name += ", e-book"
        return name
    
    def sort_key(self):
        return self.edition_info().lower()

    def finna_url(self):
        for ident in self.graph.objects(self.uri, SCHEMA.identifier):
            property_id = self.graph.value(ident, SCHEMA.propertyID, None)
            if str(property_id) == 'FI-FENNI':
                finna_id = self.graph.value(ident, SCHEMA.value, None)
                if finna_id is not None:
                    return "https://finna.fi/Record/fennica.%s" % finna_id
        return None
    
    def get_work(self):
        work_uri = self.graph.value(self.uri, SCHEMA.exampleOfWork, None, any=True)
        return Work(work_uri, self.graph)

class Collection (Work):
    pass

class Agent (Resource):
    query = """
      %(prefixes)s
      
      CONSTRUCT {
        <%(uri)s> ?p ?o .
        ?o schema:name ?oname ;
           skos:prefLabel ?olabel .
        ?wab schema:about <%(uri)s> ;
             schema:name ?wabname .
        ?wau schema:author <%(uri)s> ;
             schema:name ?wauname .
        ?wco schema:contributor <%(uri)s> ;
             schema:name ?wconame .
      }
      WHERE {
        {
          <%(uri)s> ?p ?o .
          OPTIONAL {
            { ?o schema:name ?oname }
            UNION
            { ?o skos:prefLabel ?olabel }
          }
        }
        UNION
        { # works about
          ?wab schema:about <%(uri)s> ;
               schema:name ?wabname .
        }
        UNION
        { # authored works
          ?wau schema:author <%(uri)s> ;
               schema:name ?wauname .
        }
        UNION
        { # contributed works
          ?wco schema:contributor <%(uri)s> ;
               schema:name ?wconame .
        }
      }
    """

    def is_agent(self):
        return True

    def has_authored_works(self):
        return self.graph.value(None, SCHEMA.author, self.uri, any=True) is not None
    
    def authored_works(self):
        works = [Work(work, self.graph) for work in self.graph.subjects(SCHEMA.author, self.uri)]
        works.sort(key=lambda work: work.sort_key())
        return works

    def has_contributed_works(self):
        return self.graph.value(None, SCHEMA.contributor, self.uri, any=True) is not None
    
    def contributed_works(self):
        works = [Work(work, self.graph) for work in self.graph.subjects(SCHEMA.contributor, self.uri)]
        works.sort(key=lambda work: work.sort_key())
        return works

class Person (Agent):
    pass

class Organization (Agent):
    pass
    
class Concept (Resource):
    pass

class ConceptScheme (Resource):
    pass


class SearchResult:
    def __init__(self, binding):
        self.binding = binding
    
    def uri(self):
        return uri_to_url(self.binding['uri']['value'])
    
    def name(self):
        return self.binding['literal']['value']
    
    def typename(self):
        if 'type' in self.binding:
            return self.binding['type']['value'].split('/')[-1].split('#')[-1]
        else:
            return ''
    

class Search:
    query = """
    PREFIX schema: <http://schema.org/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX text: <http://jena.apache.org/text#>
    PREFIX bf: <http://id.loc.gov/ontologies/bibframe/>
    
    SELECT *
    WHERE {
      (?uri ?score ?literal) text:query ('%(query_string)s' 100) .
      ?uri a ?type .
      VALUES ?type { bf:Work schema:Person schema:Organization skos:Concept }
      FILTER(isIRI(?uri))
    }
    ORDER BY DESC(?score)
    LIMIT %(items_per_page)d
    """
    
    def __init__(self, query_string, items_per_page=20):
        self.query_string = query_string
        self.items_per_page = items_per_page

        sparql = SPARQLWrapper(ENDPOINT)
        sparql.setQuery(self.query % {'query_string': self.formatted_query_string(), 'items_per_page': self.items_per_page})
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        self.bindings = results["results"]["bindings"]
    
    def formatted_query_string(self):
        return " ".join(["+%s" % word for word in self.query_string.split()])
    
    def total_results(self):
        return len(self.bindings)
    
    def results(self):
        return [SearchResult(binding) for binding in self.bindings]

class Collections:
    query = """
    PREFIX schema: <http://schema.org/>
    
    SELECT *
    WHERE {
      ?uri a schema:Collection ;
        schema:name ?name .
    }
    ORDER BY LCASE(?name)
    """
    
    def __init__(self):
        sparql = SPARQLWrapper(ENDPOINT)
        sparql.setQuery(self.query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        self.bindings = results["results"]["bindings"]

    def list_collections(self):
        return [{'uri': b['uri']['value'],
                 'url': uri_to_url(b['uri']['value']),
                 'name': b['name']['value']}
                for b in self.bindings]
                 
class ConceptSchemes:
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    
    SELECT *
    WHERE {
      ?uri a skos:ConceptScheme ;
        dc:title ?title .
        FILTER(langMatches(LANG(?title), 'en'))
    }
    ORDER BY LCASE(?title)
    """
    
    def __init__(self):
        sparql = SPARQLWrapper(ENDPOINT)
        sparql.setQuery(self.query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        self.bindings = results["results"]["bindings"]

    def list_concept_schemes(self):
        return [{'uri': b['uri']['value'],
                 'url': uri_to_url(b['uri']['value']),
                 'title': b['title']['value']}
                for b in self.bindings]
                 

class ExampleQueries:
    def __init__(self, root_path):
        self.query_path = os.path.join(root_path, 'static/sparql')

    def query_title_and_id(self, query_fn):
        query_id = query_fn.replace('.rq','')
        query_title = query_id.replace('_',' ')
        return (query_title, query_id)

    def list_example_queries(self):
        return sorted([self.query_title_and_id(qfn)
                      for qfn in os.listdir(self.query_path)])

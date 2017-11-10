from collections import OrderedDict
from SPARQLWrapper import SPARQLWrapper
from rdflib import URIRef, Namespace, RDF, RDFS, BNode
from rdflib.namespace import SKOS

SCHEMA = Namespace('http://schema.org/')

def property_sort_key(prop):
    return str(prop.split('/')[-1]).lower()

def value_sort_key(val):
    return str(val)

def instance_sort_key(inst):
    return inst.instname()

class Resource:
    def __init__(self, uri, graph = None):
        if isinstance(uri, URIRef) or isinstance(uri, BNode):
            self.uri = uri
        else:
            self.uri = URIRef(uri)

        if graph is not None:
            self.graph = graph
            return
        
        query = """
          PREFIX schema: <http://schema.org/>
          CONSTRUCT {
            <%s> ?p ?o .
            ?o schema:name ?oname .
            ?inst ?instprop ?instval .
            ?instval schema:name ?instvalName .
            ?pubEvent schema:location ?pubPlace .
            ?pubEvent schema:organizer ?org .
            ?org schema:name ?orgName .
          }
          WHERE {
            <%s> ?p ?o .
            OPTIONAL { ?o schema:name ?oname }
            OPTIONAL {
              <%s> schema:workExample ?inst .
              ?inst ?instprop ?instval .
              OPTIONAL {
                ?instval schema:name ?instvalName
              }
            }
            OPTIONAL {
              <%s> schema:publication ?pubEvent .
              OPTIONAL {
                ?pubEvent schema:location ?pubPlace .
              }
              OPTIONAL {
                ?pubEvent schema:organizer ?org .
                ?org schema:name ?orgName .
              }
            }
          }
        """ % (uri, uri, uri, uri)

        sparql = SPARQLWrapper("http://data.nationallibrary.fi/bib/sparql")
        sparql.setQuery(query)
        graph = sparql.query().convert()
        self.graph = graph
    
    def exists(self):
        return (len(self.graph) > 0)

    def name(self):
        labels = self.graph.preferredLabel(self.uri, labelProperties=(SCHEMA.name, RDFS.label))
        if len(labels) > 0:
            return labels[0][1]
        else:
            return "<%s>" % self.uri
    
    def instname(self):
        publisher = Resource(self.graph.value(self.uri, SCHEMA.publisher, None), self.graph).name()
        datePublished = self.graph.value(self.uri, SCHEMA.datePublished, None)
        name = "%s : %s" % (datePublished, publisher)
        if (self.uri, SCHEMA.bookFormat, SCHEMA.EBook) in self.graph:
            name += ", e-book"
        return name
        
    
    def __str__(self):
        return self.name()
    
    def url(self):
        url = self.uri
        url = url.replace('http://urn.fi/URN:NBN:fi:bib:me:','/bib/me/')
        url = url.replace('http://urn.fi/URN:NBN:fi:au:pn:','/au/pn/')
        return url
    
    def localname(self):
        return self.uri.split(':')[-1]
    
    def properties(self):
        propvals = OrderedDict() # key: property URIRef, value: list of values
        props = set([p for p in self.graph.predicates(self.uri, None) if p not in (RDF.type, SCHEMA.workExample, SCHEMA.exampleOfWork)])
        for p in sorted(props, key=property_sort_key):
            for o in self.graph.objects(self.uri, p):
                p = p.split('/')[-1] # local name
                propvals.setdefault(p, [])
                if isinstance(o, URIRef) or isinstance(o, BNode):
                    propvals[p].append(Resource(o, self.graph))
                else:
                    propvals[p].append(o)
            propvals[p].sort(key=value_sort_key)
        return propvals

    def has_instances(self):
        return (self.graph.value(self.uri, SCHEMA.workExample, None, any=True) is not None)

    def instances(self):
        insts = [Resource(inst, self.graph) for inst in self.graph.objects(self.uri, SCHEMA.workExample)]
        insts.sort(key=instance_sort_key)
        return insts
        

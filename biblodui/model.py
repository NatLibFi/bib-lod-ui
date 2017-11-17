from collections import OrderedDict
from SPARQLWrapper import SPARQLWrapper
from rdflib import URIRef, Namespace, RDF, RDFS, BNode
from rdflib.namespace import SKOS

SCHEMA = Namespace('http://schema.org/')

def get_resource(uri, graph=None):
    """return a Resource object of the appropriate class for the given URI"""
    if uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:W'):
        return Work(uri, graph)
    if uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:I'):
        return Instance(uri, graph)
    if uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:P'):
        return Person(uri, graph)
    if uri.startswith('http://urn.fi/URN:NBN:fi:bib:me:O'):
        return Organization(uri, graph)
    if uri.startswith('http://urn.fi/URN:NBN:fi:au:pn:'):
        return Person(uri, graph)
    if uri.startswith('http://urn.fi/URN:NBN:fi:au:cn:'):
        return Organization(uri, graph)
    # not a recognized URI pattern, just use a plain Resource
    return Resource(uri, graph)
    

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
        sparql = SPARQLWrapper("http://data.nationallibrary.fi/bib/sparql")
        sparql.setQuery(self.query % {'uri': self.uri, 'prefixes': self.prefixes})
        graph = sparql.query().convert()
        return graph
    
    def exists(self):
        return (len(self.graph) > 0)
    
    def typename(self):
        return self.__class__.__name__

    def name(self):
        props = (SCHEMA.name, SKOS.prefLabel, RDFS.label)
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
        url = self.uri
        url = url.replace('http://urn.fi/URN:NBN:fi:bib:me:','/bib/me/')
        url = url.replace('http://urn.fi/URN:NBN:fi:au:pn:','/au/pn/')
        return url
    
    def localname(self):
        return self.uri.split(':')[-1]
    
    def properties(self):
        propvals = OrderedDict() # key: property URIRef, value: list of values
        props = set([p for p in self.graph.predicates(self.uri, None) if p not in (RDF.type, SCHEMA.workExample, SCHEMA.exampleOfWork)])
        for p in sorted(props, key=lambda prop:str(prop.split('/')[-1]).lower()):
            for o in self.graph.objects(self.uri, p):
                p = p.split('/')[-1] # local name
                propvals.setdefault(p, [])
                if isinstance(o, URIRef) or isinstance(o, BNode):
                    propvals[p].append(Resource(o, self.graph))
                else:
                    propvals[p].append(o)
            propvals[p].sort(key=lambda val:str(val).lower())
        return propvals
    
    def has_instances(self):
        return False
    
    def has_works_about(self):
        return (self.graph.value(None, SCHEMA.about, self.uri, any=True) is not None)
    
    def works_about(self):
        works = [Work(work, self.graph) for work in self.graph.subjects(SCHEMA.about, self.uri)]
        works.sort(key=lambda w:w.sort_key())
        return works

    def has_authored_works(self):
        return False

    def has_contributed_works(self):
        return False
    
        

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
        ?instval schema:name ?instvalName .
        ?pubEvent schema:location ?pubPlace ;
                  schema:organizer ?org .
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
          <%(uri)s> schema:workExample ?inst .
          ?inst ?instprop ?instval .
          OPTIONAL {
            ?instval schema:name ?instvalName
          }
        }
        UNION
        { # publication events
          <%(uri)s> schema:publication ?pubEvent .
          OPTIONAL {
            ?pubEvent schema:location ?pubPlace .
          }
          OPTIONAL {
            ?pubEvent schema:organizer ?org .
            ?org schema:name ?orgName .
          }
        }
      }
    """

    def has_instances(self):
        return (self.graph.value(self.uri, SCHEMA.workExample, None, any=True) is not None)

    def instances(self):
        insts = [Instance(inst, self.graph) for inst in self.graph.objects(self.uri, SCHEMA.workExample)]
        insts.sort(key=lambda inst:inst.sort_key())
        return insts

class Instance (Resource):

    def name(self):
        datePublished = self.graph.value(self.uri, SCHEMA.datePublished, None)
        if datePublished is None:
          datePublished = "-"
        publisher_uri = self.graph.value(self.uri, SCHEMA.publisher, None)
        if publisher_uri is not None:
          publisher_name = Resource(publisher_uri, self.graph).name()
          name = "%s : %s" % (datePublished, publisher_name)
        else:
          name = datePublished
        if (self.uri, SCHEMA.bookFormat, SCHEMA.EBook) in self.graph:
            name += ", e-book"
        return name

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


    def has_authored_works(self):
        return (self.graph.value(None, SCHEMA.author, self.uri, any=True) is not None)
    
    def authored_works(self):
        works = [Work(work, self.graph) for work in self.graph.subjects(SCHEMA.author, self.uri)]
        works.sort(key=lambda work:work.sort_key())
        return works

    def has_contributed_works(self):
        return (self.graph.value(None, SCHEMA.contributor, self.uri, any=True) is not None)
    
    def contributed_works(self):
        works = [Work(work, self.graph) for work in self.graph.subjects(SCHEMA.contributor, self.uri)]
        works.sort(key=lambda work:work.sort_key())
        return works

class Person (Agent):
    pass

class Organization (Agent):
    pass
    

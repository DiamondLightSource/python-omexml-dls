
def page_name_original_metadata(index):
    '''Get the key name for the page name metadata data for the indexed tiff page

    These are TIFF IFD #'s 285+

    index - zero-based index of the page
    '''
    return "PageName #%d" % index

def get_text(node):
    '''Get the contents of text nodes in a parent node'''
    return node.text

def set_text(node, text):
    '''Set the text of a parent'''
    node.text = text

def qn(namespace, tag_name):
    '''Return the qualified name for a given namespace and tag name

    This is the ElementTree representation of a qualified name
    '''
    return "{%s}%s" % (namespace, tag_name)

def split_qn(qn):
    '''Split a qualified tag name or return None if namespace not present'''
    m = re.match('\{(.*)\}(.*)', qn)
    return m.group(1), m.group(2) if m else None

def get_namespaces(node):
    '''Get top-level XML namespaces from a node.'''
    ns_lib = {'ome': None, 'sa': None, 'spw': None}
    for child in node.iter():
        ns = split_qn(child.tag)[0]
        match = re.match(NS_RE, ns)
        if match:
            ns_key = match.group('ns_key').lower()
            ns_lib[ns_key] = ns
    return ns_lib

def get_float_attr(node, attribute):
    '''Cast an element attribute to a float or return None if not present'''
    attr = node.get(attribute)
    return None if attr is None else float(attr)

def get_int_attr(node, attribute):
    '''Cast an element attribute to an int or return None if not present'''
    attr = node.get(attribute)
    return None if attr is None else int(attr)

def make_text_node(parent, namespace, tag_name, text):
    '''Either make a new node and add the given text or replace the text

    parent - the parent node to the node to be created or found
    namespace - the namespace of the node's qualified name
    tag_name - the tag name of  the node's qualified name
    text - the text to be inserted
    '''
    qname = qn(namespace, tag_name)
    node = parent.find(qname)
    if node is None:
        node = ElementTree.SubElement(parent, qname)
    set_text(node, text)

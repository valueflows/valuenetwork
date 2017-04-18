import ast
import optparse
import os
import astor
from collections import OrderedDict, namedtuple

DefinedClass = namedtuple('DefinedClass', ['name', 'filename', 'lineno', 'col_offset'])


class FindClassDefinitionsNodeVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.classes = OrderedDict()

    def visit_ClassDef(self, node):
        self.classes[node.name] = DefinedClass(name=node.name, filename=self.filename, lineno=node.lineno,
                                               col_offset=node.col_offset)


def find_class_definitions(directory):
    to_scan = get_py_files(directory)

    classmap = OrderedDict()
    for file_to_scan in to_scan:
        with open(file_to_scan, 'r') as f:
            source = '\n'.join(f.readlines())
            node = ast.parse(source, file_to_scan)
            visitor = FindClassDefinitionsNodeVisitor(file_to_scan)
            visitor.visit(node)
            classmap.update(visitor.classes)
    return classmap


def get_py_files(directory):
    to_scan = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and file.endswith(".py"):
            to_scan.append(os.path.abspath(file_path))
    return to_scan


class RemoveClassmapImports(ast.NodeTransformer):
    def __init__(self, classmap):
        self.classmap = classmap

    def m_visit_import(self, node):
        if any([self.classmap.has_key(name) for name in node.names]):
            return None
        return node

    visit_Import = m_visit_import
    visit_ImportFrom = m_visit_import


def remove_classmap_imports(directory):
    to_scan = get_py_files(directory)
    for file_to_scan in to_scan:
        with open(file_to_scan, 'r') as f:
            source = '\n'.join(f.readlines())
            node = ast.parse(source, file_to_scan)
            transformer = RemoveClassmapImports(classmap)
            node = transformer.visit(node)
            new_source = astor.to_source(node)
        with open(file_to_scan, 'w') as f:
            f.write(new_source)


ImportAt = namedtuple('ImportAt', ['name', 'filename', 'lineno', 'col_offset', 'scope', 'references'])


class _Scope(object):
    __slots__ = ['parent', 'children', 'enclosing_symbol']

    def __init__(self, **kwargs):
        super(_Scope, self).__init__()
        self.parent = kwargs.pop('parent', None)
        self.children = kwargs.pop('children', [])
        self.enclosing_symbol = kwargs.pop('enclosing_symbol', None)


class NameGrabberNodeVisitor(ast.NodeVisitor):
    def __init__(self, filename, classmap):
        self.scope = self.root_scope = _Scope()
        self.filename = filename
        self.classmap = classmap
        self.names = []

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        result = visitor(node)
        end_method = 'end_visit_' + node.__class__.__name__
        end_visitor = getattr(self, end_method, None)
        if end_visitor:
            end_visitor(node)
        return result

    def visit_ClassDef(self, node):
        old_scope = self.scope
        self.scope = _Scope(parent=self.scope, enclosing_symbol=node.name)
        self._add_to_scope(self.scope, old_scope)

    def end_visit_ClassDef(self, node):
        self.scope = self.scope.parent

    def visit_FunctionDef(self, node):
        old_scope = self.scope
        self.scope = _Scope(parent=self.scope, enclosing_symbol=node.name)
        self._add_to_scope(self.scope, old_scope)

    def visit_Name(self, node):
        if self.classmap.has_key(node.id):
            self.names.append(
                ImportAt(name=node.id, filename=self.filename, scope=self.scope, lineno=node.lineno,
                         col_offset=node.col_offset,
                         references=self.classmap[node.id]))

    def _add_to_scope(self, receiver, scope):
        receiver.children = receiver.children or []
        receiver.children.append(scope)


def compute_minimal_imports(directory, classmap):
    to_scan = get_py_files(directory)
    global_names = []
    for file_to_scan in to_scan:
        with open(file_to_scan, 'r') as f:
            source = '\n'.join(f.readlines())
            node = ast.parse(source, file_to_scan)
            visitor = NameGrabberNodeVisitor(file_to_scan, classmap)
            visitor.visit(node)
            names = visitor.names
            global_names.extend(names)
    print global_names


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--directory', dest="directory", help="Directory to scan", metavar="DIRECTORY")

    (options, args) = parser.parse_args()
    directory = options.directory
    classmap = find_class_definitions(directory)
    remove_classmap_imports(directory)
    compute_minimal_imports(directory, classmap)

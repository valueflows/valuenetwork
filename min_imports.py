import ast
import optparse
import os
from collections import OrderedDict, namedtuple
import itertools

DefinedClass = namedtuple('DefinedClass', ['name', 'filename', 'lineno', 'col_offset'])


class ScopedNodeVisitor(ast.NodeVisitor):
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        result = visitor(node)
        end_method = 'end_visit_' + node.__class__.__name__
        end_visitor = getattr(self, end_method, None)
        if end_visitor:
            end_visitor(node)
        return result


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


ImportAt = namedtuple('ImportAt', ['name', 'filename', 'lineno', 'col_offset', 'scope', 'references'])


class _Scope(object):
    __slots__ = ['parent', 'children', 'enclosing_symbol']

    def __init__(self, **kwargs):
        super(_Scope, self).__init__()
        self.parent = kwargs.pop('parent', None)
        self.children = kwargs.pop('children', [])
        self.enclosing_symbol = kwargs.pop('enclosing_symbol', None)


class NameGrabberNodeVisitor(ScopedNodeVisitor):
    def __init__(self, filename, classmap):
        self.scope = self.root_scope = _Scope()
        self.filename = filename
        self.classmap = classmap
        self.names = []

    def visit_ClassDef(self, node):
        old_scope = self.scope
        self.scope = _Scope(parent=self.scope, enclosing_symbol=node.name)
        old_scope.children.append(self.scope)
        self.generic_visit(node)

    def end_visit_ClassDef(self, node):
        self.scope = self.scope.parent

    def visit_FunctionDef(self, node):
        old_scope = self.scope
        self.scope = _Scope(parent=self.scope, enclosing_symbol=node.name)
        old_scope.children.append(self.scope)
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in self.classmap:
            ImportAt(name=node.id, filename=self.filename, scope=self.scope, lineno=node.lineno,
                     col_offset=node.col_offset,
                     references=self.classmap[node.id])
        self.generic_visit(node)


def compute_minimal_imports(directory, classmap):
    to_scan = get_py_files(directory)
    global_names = []
    for file_to_scan in to_scan:
        with open(file_to_scan, 'r') as f:
            source = '\n'.join(f.readlines())
            node = ast.parse(source, file_to_scan)
            visitor = NameGrabberNodeVisitor(file_to_scan, classmap)
            visitor.visit(node)
            global_names.extend(visitor.names)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--directory', dest="directory", help="Directory to scan", metavar="DIRECTORY")

    (options, args) = parser.parse_args()
    directory = options.directory
    classmap = find_class_definitions(directory)
    compute_minimal_imports(directory, classmap)

import ast
import optparse
import os
import sys


class FindClassDefinitionsNodeVisitor(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        print(dir(node.bases[0].value.id))


def find_class_definitions(directory):
    to_scan = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and file.endswith(".py"):
            to_scan.append(os.path.abspath(file_path))

    for file_to_scan in to_scan:
        with open(file_to_scan, 'r') as f:
            source = '\n'.join(f.readlines())
            node = ast.parse(source, file_to_scan)
            visitor = FindClassDefinitionsNodeVisitor()
            visitor.visit(node)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--directory', dest="directory", help="Directory to scan", metavar="DIRECTORY")

    (options, args) = parser.parse_args()
    directory = options.directory
    find_class_definitions(directory)

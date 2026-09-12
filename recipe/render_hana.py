"""Render the limited ERB syntax in Boost.Hana's struct_macros.hpp.erb.

Unknown syntax is rejected so upstream template changes cannot silently
produce an incomplete header. This is not a general Ruby interpreter.
"""
import argparse
import re
from pathlib import Path


def integer(expression, variables):
    match = re.fullmatch(r'(\d+|[A-Za-z_]\w*)(?:([+-])(\d+))?', expression.strip())
    if not match:
        raise ValueError(f'Unsupported integer: {expression}')
    atom, operator, delta = match.groups()
    value = int(atom) if atom.isdecimal() else variables[atom]
    return value + (int(delta) if operator == '+' else -int(delta)) if operator else value


def expression(text, variables):
    text = text.strip()
    if re.fullmatch(r'(\d+|[A-Za-z_]\w*)(?:[+-]\d+)?', text):
        return str(integer(text, variables))
    match = re.fullmatch(r'\((.*?)\.\.(.*?)\)(?:\.to_a)?(.*)', text)
    if not match:
        raise ValueError(f'Unsupported expression: {text}')
    first, last, operations = match.groups()
    values = list(range(integer(first, variables), integer(last, variables) + 1))
    if operations.startswith('.reverse'):
        values.reverse()
        operations = operations[len('.reverse'):]
    mapping = re.match(r'\.map \{ \|i\| "([^"]*)" \}', operations)
    if mapping:
        pattern = mapping[1]
        values = [re.sub(r'#\{([^}]+)\}', lambda m: str(integer(m[1], {**variables, 'i': i})), pattern) for i in values]
        operations = operations[mapping.end():]
    join = re.fullmatch(r"\.join(?:\('([^']*)'\))?", operations)
    if not join:
        raise ValueError(f'Unsupported operation: {operations}')
    return (join[1] or '').join(map(str, values))


def render(template, members):
    if members <= 0:
        raise ValueError('MAX_NUMBER_OF_MEMBERS must be > 0')
    variables = {'MAX_NUMBER_OF_MEMBERS': members}
    template = re.sub(r'<%#.*?%>', '', template, flags=re.S)
    setup = '''<%
    MAX_NUMBER_OF_MEMBERS = (ENV["MAX_NUMBER_OF_MEMBERS"] || 55).to_i
    raise "MAX_NUMBER_OF_MEMBERS must be > 0" if not MAX_NUMBER_OF_MEMBERS > 0
%>'''
    if template.count(setup) != 1:
        raise ValueError('Unexpected template setup')
    template = template.replace(setup, '')
    loops = re.compile(r'<% \((\d+)\.\.MAX_NUMBER_OF_MEMBERS\)\.each do \|n\| %>(.*?)<% end %>', re.S)
    substitute = lambda body, context: re.sub(r'<%=\s*(.*?)\s*%>', lambda m: expression(m[1], context), body)
    template = loops.sub(lambda m: ''.join(substitute(m[2], {**variables, 'n': n}) for n in range(int(m[1]), members + 1)), template)
    result = substitute(template, variables)
    if '<%' in result or '%>' in result:
        raise ValueError('Unprocessed template directive')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('template', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--members', type=int, default=200)
    args = parser.parse_args()
    args.output.write_bytes(render(args.template.read_text(), args.members).encode())

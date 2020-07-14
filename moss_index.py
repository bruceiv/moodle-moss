import param
from yattag import Doc

style = """
.grid-box {
    display: grid;
    grid-template-columns: max-content max-content max-content max-content;
    grid-column-gap: 1em
}
.grid-column-span {
    grid-column-start: 1;
    grid-column-end: 5;
}
"""

# generates a grid row for a single result
def result_line(m):
    doc, tag, text, line = Doc().ttl()

    with tag('div'):
        line('a', m.name0, href='report/' + m.page)
    with tag('div'):
        line('a', m.name1, href='report/' + m.page)
    with tag('div'):
        text(m.similarity, '% ')
    with tag('div'):
        doc.stag('meter', value=m.similarity, min='0', max='100')
    
    return doc.getvalue()

# Generates MOSS index page
def generate_html(title, clusters, results):
    title = 'MOSS matches for ' + title
    doc, tag, text, line = Doc().ttl()

    doc.asis('<!DOCTYPE html>')
    with tag('html'):
        with tag('head'):
            line('title', title)
            line('style', style)
        with tag('body'):
            line('h2', title)
            with tag('div', klass='grid-box'):
                with tag('div', klass='grid-column-span'):
                    line('h3', 'Clusters')
                first = True
                for c in clusters:
                    if first:
                        first = False
                    else:
                        with tag('div', klass='grid-column-span'):
                            doc.stag('hr')
                    
                    for m in c[0]:
                        doc.asis(result_line(m))
            
                with tag('div', klass='grid-column-span'):
                    line('h3', 'All Results')
                for m in results:
                    doc.asis(result_line(m))
    
    return doc.getvalue()
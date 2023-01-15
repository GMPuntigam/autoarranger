from xml.dom import minidom
import re
import svg.path


def get_notepositions(svg_file):
    svg_dom = minidom.parse(svg_file)
    # get the root element (should be an SVG element)
    svg_root = svg_dom.documentElement
    x_translations = []
    for element in svg_root.getElementsByTagName("*"):
        if element.nodeType != minidom.Node.ELEMENT_NODE:
            continue
        if element.tagName != "path":
            continue
        transform = element.parentNode.getAttribute("transform")
        translate_match = re.search(r"translate\(([^,]+),([^\)]+)\)", transform)
        if translate_match:
            x = float(translate_match.group(1))
            y = float(translate_match.group(2))
            x_translations.append(x)
    x_translation_set = set(x_translations)
    note_positions = []
    for x_pos in x_translation_set:
        count = x_translations.count(x_pos)
        if count == 4:
            note_positions.append(x_pos)
    x, y, width, height = [float(pos) for pos in svg_root.getAttribute("viewBox").split(' ')]
    note_positions = [(position-x)/width*100 for position in note_positions]
    note_positions.sort()
    return note_positions




def crop_svg(svg_file, svg_changed):
    # parse the SVG file
    svg_dom = minidom.parse(svg_file)
    
    # get the root element (should be an SVG element)
    svg_root = svg_dom.documentElement
    
    # get the bounding box of all elements in the SVG
    x_min, y_min, x_max, y_max = None, None, None, None
    for element in svg_root.getElementsByTagName("*"):
        if element.nodeType != minidom.Node.ELEMENT_NODE:
            continue
        if element.tagName == "line":
            x1, y1, x2, y2 = (float(element.getAttribute(attr)) for attr in ["x1", "y1", "x2", "y2"])
            x, y, width, height = (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        if element.tagName == 'path':
            path_d = element.getAttribute("d")
            path = svg.path.parse_path(path_d)
            min_x, min_y, max_x, max_y = None, None, None, None
            for segment in path:
                if min_x is None or segment.start.real < min_x:
                    min_x = segment.start.real
                if min_y is None or segment.start.imag < min_y:
                    min_y = segment.start.imag
                if max_x is None or segment.start.real > max_x:
                    max_x = segment.start.real
                if max_y is None or segment.start.imag > max_y:
                    max_y = segment.start.imag
            x, y, width, height = (min_x, min_y, max_x, max_y)
        elif element.tagName == "polygon":
            points = element.getAttribute("points").split(' ')
            x_coords = [float(points[i]) for i in range(0, len(points), 2)]
            y_coords = [float(points[i]) for i in range(1, len(points), 2)]
            x, y, width, height = min(x_coords), min(y_coords), max(x_coords) - min(x_coords), max(y_coords) - min(y_coords)
        if element.tagName == 'rect':
            x = float(element.getAttribute("x")) if element.hasAttribute("x") else 0
            y = float(element.getAttribute("y")) if element.hasAttribute("y") else 0
            width = float(element.getAttribute("width")) if element.hasAttribute("width") else 0
            height = float(element.getAttribute("height")) if element.hasAttribute("height") else 0
        if element.tagName in ['style', 'g']:
            continue
        transform_el = element.getAttribute("transform")
        if transform_el:
            scale_match = re.search(r"scale\(([^,]+),([^\)]+)\)", transform_el)
            if translate_match:
                x *= abs(float(scale_match.group(1)))
                width *= abs(float(scale_match.group(1)))
                y *= abs(float(scale_match.group(2)))
                height *= abs(float(scale_match.group(2)))
        transform_par = element.parentNode.getAttribute("transform")
        if transform_par:
            translate_match = re.search(r"translate\(([^,]+),([^\)]+)\)", transform_par)
            if translate_match:
                x += float(translate_match.group(1))
                y += float(translate_match.group(2))
        if x_min is None or x < x_min:
            x_min = x
        if y_min is None or y < y_min:
            y_min = y
        if x_max is None or x + width > x_max:
            x_max = x + width
        if y_max is None or y + height > y_max:
            y_max = y + height
    
    # if there are no elements, we can't crop the SVG
    if x_min is None or y_min is None or x_max is None or y_max is None:
        return None
    
    svg_root.setAttribute("viewBox", f"{x_min} {y_min} {x_max - x_min} {y_max - y_min}")
    svg_root.setAttribute("height", "100%")
    svg_root.setAttribute("width", "100%")
    with open(svg_changed, 'w') as f:
        f.write(svg_dom.toxml())
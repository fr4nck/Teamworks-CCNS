from .guards import normalize_text


def element_name(element):
    try:
        name = element.element_info.name
        if name:
            return str(name)
    except Exception:
        pass
    try:
        return str(element.window_text())
    except Exception:
        return ""


def element_control_type(element):
    try:
        return str(element.element_info.control_type or "")
    except Exception:
        return ""


def find_named(elements, name, control_types=()):
    wanted = normalize_text(name)
    allowed = {normalize_text(value) for value in control_types}
    matches = []
    for element in elements:
        if normalize_text(element_name(element)) != wanted:
            continue
        if allowed and normalize_text(element_control_type(element)) not in allowed:
            continue
        matches.append(element)
    if not matches:
        raise LookupError("Controle introuvable: %r" % name)
    for element in matches:
        try:
            if element.is_visible() and element.is_enabled():
                return element
        except Exception:
            continue
    return matches[0]

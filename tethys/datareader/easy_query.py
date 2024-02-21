import gcamreader


def easy_query(variable, year_axis=None, **kwargs):
    """Build a query for a GCAM database

    kwargs act as filters on nodes, eg. "sector='Beef'" is converted to the xpath "[@type='sector' and @name='Beef']"
    Lists are also accepted, so "sector=['Beef', 'Dairy']" matches 'Beef' or 'Dairy'

    Order of kwargs must follow the sector -> subsector -> technology -> input/output/etc hierarchy

    Some shortcuts are supported. '*' can be used as a wildcard, so input='water_td_irr_*_C'
    matches any input starting with 'water_td_irr' and ending with '_C'

    Starting a filter string with '!' negates it, so sector='!elec*' will exclude any sector names
    that begin with 'elec'.
    Combinations are allowed, so input=['water_td_irr_*_C', '!water_td_irr_A*'] would select all input basins,
    except those beginning with the letter 'A'.

    :param variable: name of variable in database, such as 'demand-physical' or 'emissions'
    :param year_axis: optional name of year axis ('year' or 'vintage'). If None, will be inferred from variable
    :param kwargs: refer to description for details

    :return: gcamreader Query object
    """

    filters = dict(sector=None)  # match nodes where @type='sector' by default
    filters.update(kwargs)  # update the filters with user-provided kwargs

    # filters are separated by "//*" to match any descendant
    xpath = "*" + "//*".join(handle_filter(k, v) for k, v in filters.items()) + f"//{variable}/node()"

    if year_axis is None:
        year_axis = get_year_axis(variable)

    # query template
    querystr = f"""<dummyQuery title="">
    <axis1 name="axis">axis</axis1>
    <axis2 name="year">{variable}[@{year_axis}]</axis2>
    <xPath>{xpath}</xPath>
    </dummyQuery>"""

    return gcamreader.Query(querystr)


def handle_filter(key, value):
    """Handle a kwarg for build_query

    :param key: xml node @type attribute to match
    :param value: string, or list of strings, indicating what the node @name attribute must match or not match
    :return: xpath to filter nodes
    """

    # promote string value to length 1 list so that we only need to define how to handle list
    if isinstance(value, str):
        value = [value]

    if isinstance(value, list):
        # need to handle '!' filters all at the end here so that conjunctions work
        ors = [name for name in value if not name.startswith('!')]
        andnots = [name for name in value if name.startswith('!')]

        out = f"[@type='{key}'"

        # things to include
        if ors:
            out += f" and ({parse_name(ors[0])}"
            for name in ors[1:]:
                out += f" or {parse_name(name)}"
            out += ")"

        # things to exclude
        for name in andnots:
            out += f" and not {parse_name(name.strip('!'))}"

        out += "]"

        return out

    # so that when value is None, only matters that type is key
    return f"[@type='{key}']"


def parse_name(name):
    """
    convert a string to an xpath condition
    the basic case converts "foo" to "@name='foo'"

    '*' acts as a wildcard, so "foo*" is converted to "(starts-with(@name, 'foo'))"

    :param name: the string to parse
    :return: xpath condition indicated by string
    """

    if '*' in name:
        substrings = name.split('*')

        out = "("
        for i, substring in enumerate(substrings):
            if substring != '':
                out += "" if out == "(" else " and "  # don't need to add 'and' for the first condition
                if i == 0:
                    out += f"starts-with(@name, '{substring}')"
                elif i == len(substrings) - 1:
                    out += f"ends-with(@name, '{substring}')"
                else:  # note: order of internal substrings is not matched
                    out += f"contains(@name, '{substring}')"
        out += ")"

        return out

    return f"@name='{name}'"


def get_year_axis(variable):
    # guess the year axis name
    if variable in ['demand-physical', 'physical-output', 'price-paid', 'carbon-content', 'IO-coefficient']:
        return 'vintage'
    return 'year'

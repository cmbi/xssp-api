from xssp_api.frontend.filters import beautify_docstring


def test_beautify_docstring():
    ds = "This is the summary.\n\nThis is also part of the summary.\n\n" + \
         ":param p: param description.\nIt can span multiple lines.\n" + \
         ":param q: param description again.\n" + \
         ":return: It returns something.\nAlso on multiple lines."
    bds = beautify_docstring(ds)

    print(bds)

    assert "<p>This is the summary.\n\nThis is also part of the " + \
           "summary.\n\n</p>" in bds
    assert "<dt><code>p</code></dt>" in bds
    assert "<dt><code>q</code></dt>" in bds

#!/usr/bin/env python3

if __name__ == '__main__':
    import autoprop
    import nestedtext as nt

    from timeit import timeit
    from functools import cached_property

    snippets = nt.load('check_performance.nt')
    results = {}

    for name, snippet in snippets.items():
        scope = {
                'autoprop': autoprop, 
                'cached_property': cached_property,
        }
        exec(snippet, scope)
        scope['obj'] = scope['MyObj'](1)

        results[name] = timeit('obj.x', globals=scope)

    debug(results)

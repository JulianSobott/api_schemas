typedef_everything = """\
import std

typedef Example
    a: str
    b: int
    c: float
    d: any
    e: D {A, B, C}
    f: E
        Z = v v
        ?g[]: bool
        i: str
            type = Date
            format = yyyy-mm-dd HH:MM:ss.SSS
        j: $Week
        k: $std.uint32

typedef Date str
    type = Datetime
    format = yyyy-mm-dd HH:MM:ss.SSS
    
typedef Week {Monday, Tuesday, Wednesday}

typedef Q
    a: $Example
    b: $Date
    
typedef QQ $Q
"""
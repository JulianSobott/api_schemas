typedef_everything = """\
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

typedef Date str
    type = Datetime
    format = yyyy-mm-dd HH:MM:ss.SSS
    
typedef Week {Monday, Tuesday, Wednesday}

typedef Q
    a: $Example
    b: $Date
    
typedef QQ $Q
"""

websockets_1 = """\
WS
    ->
        a
            i: str
            b: Name
                x: str
                i: int
        join_team
            num: str
    <-
        update
            i[]: int

"""

websockets_2 = """\
WS
    ->
    <-
"""

websockets_3 = """\
typedef X
    i: int
    v: str
    
WS
    ->
        join
            $X
    <-
"""

communication_1 = """
t
    uri=/t
    
    GET
        ->
            []: bool
        <-
            200

"""

everything = typedef_everything + websockets_1 + communication_1

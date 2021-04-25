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
        join
            game_id: str
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

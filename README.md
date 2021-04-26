# API schemas

Create an intermediate representation of an api schema, that can be used to generate code.

**In other words**: Same what OpenAPI has already but with fewer options.

**But why?**: Because it is fun 😎

## Example API schema
```
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

server = http://localhost:5000/api/v1

people
    uri: /people/<name>
    GET
        ->
        <-
            200
                data: $Example
            404
                err_msg: str
            500
                err_msg: str
                
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

```

## Changelog

### 0.1.3

- Add compilers to build dataclasses for python and dart
- Add Websocket support
- Allow Communications that are an array instead of an object
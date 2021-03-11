# API schemas

Create an intermediate representation of an api schema, that can be used to generate code.

**In other words**: Same what OpenAPI has already but with fewer options.

**But why?**: Because it is fun 😎

## Example API schema
```
typedef object MyData
    name: str
    ?an_enum: {SUCCESS, FAILURE} Status # Optional enum 
    an_array[]: object People
        name: str   # comments are also possible
        *: str  # wildcards allow any string as key

server = http://localhost:5000/api/v1

people
    uri: /people/<name>
    GET
        ->
        <-
            200
                data: $MyData
            404
                err_msg: str
            500
                err_msg: str

```
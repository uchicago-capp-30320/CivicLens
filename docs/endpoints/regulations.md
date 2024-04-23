### Endpoint Documentation

Whether you are building an API or an HTML-driven web application you will want to identify key URLs, their purpose, and parameters.

Your team should add a `docs/` directory (you may use another name if convenient)


#### Example

**/photo/{id}**

Parameters: ID (FK to Photo Resource)

Response: HTML page that showcases a single photo.

Template Context Variables: 
- user : auth.User
- image : Image
- current_version : ImageVersion

**/livestream/**

Parameters:
- sort: default, nearby, random - pick from available sort algorithms
- n: number of entries to return (2-10)

Example:
/livestream/?sort=random&n=5 - get 5 random entries

Response: JSON list of up to N entries, in format
```
{
    "meta": {"n": 5, "total": 2230},
    "images": [{"url": "http://...", }]
}
```
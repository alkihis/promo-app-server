# promo-app API

## Objects

### Student objects

```json
{
  "id": 0,
  "name": "",
  "surname": "",
  "promo_in": "",
  "promo_out": "" | null,
  "birthdate": "",
  "email": "",
  "previous_formation": { formation-object } | null,
  "next_formation": { formation-object } | null
}
```

### Company objects

```json
{
  "id": 0,
  "name": "",
  "town": "",
  "size": "small" | "medium" | "large",
  "status": "public" | "private",
  /** Extended company objects may contain contacts */
  "contacts": [ { contact-object } ]
}
```

### Contact objects

```json
{
  "id": 0,
  "name": "",
  "email": "",
  "linked_to": 0 /** company ID */
}
```

### Job object

```json
{
  "id": 0,
  "owner": { student-object },
  "referrer": { contact-object },
  "company": { company-object },
  "domain": "",
  "from": "" /** date or promotion if type == alternance */,
  "to": "" | null /** date or "now" */,
  "type": "" /** CDI, CDD, etc... */,
  "wage": 0
}
```

### Intership object

```json
{
  "id": 0,
  "during": "" /* promotion */,
  "owner": { student-object },
  "company": { company-object },
  "referrer": { contact-object },
}
```

### Formation object

```json
{
  "id": 0,
  "name": ""
}
```

## Authentification

Once auth made with `auth/` endpoints, user should always include his token in the `Authorization` HTTP header in order to be logged, in every request, with the pattern:
```
Authorization: Bearer __token__
```

If not specified, endpoints requires a student level authentification.

## Students endpoints

### GET student/:id

ID must me numeric.

Returns a student object if found.

### GET student/search
**Params**: name, promo_in, promo_out, previous_formation

All parameters are optional.

Auth level: teacher

Return a list of student objects.

### POST student/create
**Params**: name, surname, email, promo_in, birthdate

All parameters are required.

Return the newly created student object.

### POST student/update
**Params**: name, surname, email, promo_in, promo_out, previous_formation, next_formation

All parameters are optional.

Auth level: **student** except for modify name and surname.

Return the updated student object.

### DELETE student/:id

ID must be numeric.

Auth level: teacher

Return the deleted student object.

## Authentification endpoints

### POST auth/login
**Params**: password

Teacher password in order to access website.

```json
{ "token": "" }
```

### POST auth/student
**Params**: token

Return HTTP 200 if success.

### GET auth/redirect
**Params**: token

Webpage. Take a token in get parameters, call `auth/student` and redirect the user to home page with logged token.

### DELETE auth/:token

Invalidate a given token. Logged user must own the token.

Return HTTP 200 if success.

### GET auth/restore
**Params**: name, surname, birthdate

All parameters are required.

Send a email to the student in order to give his token back.

Return a HTTP 200 OK if mail has been sent.

## Company endpoints

### GET company/:id

ID must be numeric.

Return a company object.

### POST company/create
**Params**: name, town, size, status

All parameters are required, status and size must follow the enum pattern as defined in the company object.

Return the newly created company object.

### POST company/update

Same parameters as create, but all are optional.

Return the updated company object.

### GET company/search
**Params**: name, town, alias

All parameters are optional. Alias will search for *similar* company names.

Return a list of company objects.


## Contact endpoints

### GET contact/:id
ID must be numeric.

Return a contact object.

### POST contact/create
**Params**: name, company_id, mail

All parameters are required, company must exists.

Return the newly created contact object.

### POST contact/update
**Params**: mail.

Update only mail. 

Return updated contact object.

### DELETE contact/:id

Auth: teacher

Remove a contact.

Return the deleted contact object.


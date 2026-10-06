# Sign-in: fewer db-service calls

Owner: Surya

## Why

A student opening a quiz session link and signing in makes about 9 calls from portal-backend to db-service. Each one is a separate HTTPS request, and several ask questions db-service can already answer together.

On the Punjab live test (29 Sep), this added up. We had 1.6 lakh sign-ins from 33k students, with peaks of ~1,400 sign-ins a minute around 10:10 IST. db-service (t3.small) sat at 95–98% CPU from 08:15 IST, and portal-backend's p95 latency went from ~55 ms on a normal morning to ~29.6 s, which is basically the Lambda timeout.

## What happens today

For a student signing in through a session link:

| Step | Route | db-service calls | Where |
|---|---|---|---|
| Load the link | `GET /session-occurrence` | 2: session, then active occurrence | `router/session_occurrence.py` |
| Find the auth group | `GET /session-group/{id}` | 1 | `router/group_session.py` |
| Verify ID + DOB | `GET /student/verify` | 4: auth group, student lookup, the auth group's `group` row, `group_user` membership | `services/student_service.py` (`verify_student_comprehensive`, `_matches_verification_params`) |
| Log attendance | `POST /user-session` | 2: session lookup, then write | `router/user_session.py` |

## What db-service already gives us

Before adding anything to db-service, it turns out most of what we need is already there:

- **`GET /student` already scopes by auth group.** Pass `auth_group` or `auth_group_id` and it only returns students with a *current* enrollment record in that group, with the user embedded (`student_controller.maybe_scope_to_auth_group`). We don't pass it in verify. Instead we fetch every student with that `student_id`, then check membership ourselves with two more calls (`group`, then `group_user`). That's the waste.
- **`GET /group-session/session-auth-group`** gives the auth group for a session in one call. We use it already.
- **`GET /session-occurrence`** already filters active occurrences (`is_start_time=active`).
- **`POST /student/verify-student`** exists, but returns only `is_verified: true/false`. We need the record to mint the token, so it doesn't help as is.

So no new db-service endpoint is needed for the main win.

## What we change

1. **Pass the auth group to `GET /student` in verify, and drop our own membership check.** Verify goes from 4 calls to 2 (auth group + scoped student), or 1 once the auth group is cached. This also handles the 372 `student_id`s that exist in more than one auth group, since db-service does the scoping.

   **One catch to decide first.** db-service scopes by the *current enrollment record*, while our check today uses `group_user`. In prod, 7,764 students are in an auth group via `group_user` but have no current enrollment record there (all of them have a non-current one):

   | Auth group | Students |
   |---|---|
   | EnableStudents | 5,232 |
   | HaryanaStudents | 1,399 |
   | PunjabStudents | 722 |
   | others | ~410 |

   These students can log in today and would be locked out after the switch. If they're dropouts or last year's students, that's arguably correct. If not, either backfill their enrollment records first, or expose the `include_inactive` option db-service already has internally (`Users.get_student_by_student_id_and_auth_group(..., include_inactive: true)`) as a query param. Worth checking with the program teams before switching.

2. **Cache the session and auth group lookups** (see `signin-caching.md`). That takes the session call off `/session-occurrence` and the lookup off `/user-session`, without any db-service change.
3. **Timeouts and connection reuse.** Today only 3 of our `requests` calls have a timeout, so a stuck call holds a Lambda for the full 30 s. Use one shared `requests.Session` (or `httpx.Client`) with a 5–10 s timeout for all db-service calls.

## Result

| Step | Today | After |
|---|---|---|
| Load the link | 2 | 1 (session cached) |
| Find the auth group | 1 | 1, or 0 if cached by session |
| Verify | 4 | 1 (auth group cached) |
| Log attendance | 2 | 1 (session cached) |
| **Total** | **9** | **3–4** |

## Beyond sign-in

- **Signup form load** is the heaviest single request: it pulls a whole state's school list from db-service on every load to build the district/school dropdown. Covered in `signin-caching.md`.
- **Signup submit** fans out to several lookups and writes (exam, grade, batch, school validation, group_user). db-service's `POST /student` already creates the auth-group enrollment and `group_user` in one go, so the remaining calls are mostly static lookups, which the caching doc covers. Signup volume is low compared to sign-in (a few thousand on the test morning against 1.6 lakh sign-ins), so moving more of it into db-service isn't worth the bloat right now.
- **Information form**: the submit is 2 calls (lookup + patch), both needed. The load benefits from caching the form schema.

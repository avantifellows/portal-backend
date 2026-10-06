# Sign-in: caching

Owner: Abhinav

## Why

Some of the db-service calls on sign-in fetch things that are the same for every student taking the same test: the auth group, and the session. During a live test thousands of students fetch the same few rows again and again. Caching those saves calls without touching anything student-specific.

The catch is staleness. quiz-backend's cache (PR #142) has no invalidation, so an edited quiz can be served stale for up to an hour, and its PR calls this out. For sign-in, a stale answer can lock students out, so we need to be careful about *what* we cache, not just *how*.

## What the data says

From afdb, last 90 days. Note `inserted_at`/`updated_at` are UTC while occurrence times are IST wall-clock, so we shifted them before comparing.

| | Count |
|---|---|
| Sessions created | 3,258 |
| Created at start time, or within 2 hours before it | 2,200 (68%) |
| Edited while the test was running | 487 (15%) |
| Edited in the 2 hours before start | 0 |
| Occurrence created or changed during the test window | 2,254 |

Auth groups change rarely: the latest edits were OLFStudents (22 Sep), ALC and CMC (11 Sep), DelhiSchools (18 Aug), MaharashtraStudents (17 Aug).

So auth groups are safe to cache. Sessions are mostly safe, with one twist: most of them come into existence right when the test starts. A student who opens the link a minute early gets "session not found", and we must not remember that.

## What to cache

| Lookup | Cache? | TTL |
|---|---|---|
| Auth group, by name or id | Yes | 5 min |
| Session details (name, platform, test id), when found | Yes | 60 s |
| Session not found | **No**, never cache misses | — |
| Is the session open right now (active occurrence) | **No** | — |
| Student lookup / verify result | **No** | — |

That takes 2–3 of the ~9 calls off each sign-in. Together with `signin-fewer-dbservice-calls.md`, a sign-in comes down to about 3 calls.

## How

Start simple: an in-process TTL cache (`cachetools.TTLCache`) inside each worker. The data is tiny (a few hundred auth groups and today's sessions), and a few seconds of disagreement between workers or tasks doesn't matter for these lookups.

Redis, as in quiz-backend #142, buys a shared cache across tasks, but adds a sidecar and failure modes (quiz-backend needed a 250 ms deadline and reconnect cooldown so a slow Redis didn't slow requests). Worth it later if we want to cache more. For these two lookups, in-process is enough.

On Lambda an in-process cache only lives as long as a warm instance, so it helps little at 3,000 concurrent instances. It pays off once portal-backend is on ECS (see `move-to-ecs.md`), so do this after, or together with, the move.

## Checks

- A session created after a student's first attempt becomes reachable immediately (miss not cached).
- Opening or extending a session takes effect immediately (open check not cached).
- Editing an auth group's `input_schema` shows up within 5 minutes.
- A cache error falls through to db-service, never fails the request.

## Beyond sign-in

The same idea applies to a few other paths. From the prod logs of the Punjab test morning and afdb:

**School dropdown on signup. The biggest single win.** When a signup form has district / block / school fields, we build the dropdown by pulling the *whole school list for that state* from db-service on every form load (`form_service._enhance_with_district_school_mapping` and `GET /school/dependant-mapping/{auth_group}`, both via `school_service._get_all_schools`). That's up to ~2,900 rows for Himachal, ~1,100 for Delhi, serialised by db-service each time, and it ran thousands of times that morning. Schools change slowly (1,854 of 11,203 edited in 90 days, mostly bulk imports). Cache the built mapping per auth group for a few hours, or precompute it nightly into a static JSON. A new school shows up a few hours late, which is fine.

**Form schemas.** 39 in total, 7 edited in 90 days. `GET /form-schema/` and the information-form fields lookup fetch the schema fresh every time. Cache for 10–15 min.

**Static lookups during signup.** Signup calls `get_exam_by_name` per exam picked, plus `get_grade_by_number` and `get_batch_by_id`. Exams last changed in January and grades in 2024: cache for an hour. Batches are added daily but rarely edited: cache hits only, like sessions.

**Not worth it:** `/auth/verify`, refresh and launch-token make no db-service calls. The information-form submit (lookup + patch) and the signup writes are necessary as they are.

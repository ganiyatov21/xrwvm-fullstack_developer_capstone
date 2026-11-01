# fullstack_developer_capstone

Best Cars is a dealership review portal built for the IBM Full Stack Application Development Capstone. It uses React for the interactive client, Django for authentication and proxy APIs, Express and MongoDB for dealership and review persistence, and a Flask/NLTK VADER microservice for sentiment analysis.

## Run with Docker Compose

Copy `.env.example` to `.env` and replace `DJANGO_SECRET_KEY` with a random secret. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for your deployment host, then run:

```sh
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Open `http://localhost:8000`. Sign up to write a review. Administration is available at `/admin/`. MongoDB data and the Django user database persist in named volumes. Seed data is loaded only into empty collections and the car inventory command is idempotent.

## Endpoints

| Service | Endpoints |
| --- | --- |
| Django | `/djangoapp/session`, `/djangoapp/login`, `/djangoapp/register`, `/djangoapp/logout` |
| Django proxy | `/djangoapp/get_dealers`, `/djangoapp/get_dealers/Kansas`, `/djangoapp/dealer/1`, `/djangoapp/reviews/dealer/1`, `/djangoapp/get_cars`, `/djangoapp/add_review` |
| Express, port 3030 | `/fetchDealers`, `/fetchDealers/Kansas`, `/fetchDealer/1`, `/fetchReviews/dealer/1`, `/insert_review`, `/health` |
| Sentiment, port 5000 | `/analyze/Excellent%20service` |

Writes require a CSRF token and posting a review requires a Django session. Reviewer identity comes from the authenticated user. Development sample contact details and team biographies are fictional.

## Local development

Use Python 3.12+ and Node.js 22. In `server/frontend`, run `npm ci && npm run build`. Install `server/requirements.txt` in a virtual environment, then from `server` run `python manage.py migrate`, `python manage.py seed_cars`, and `python manage.py runserver`. Start the Mongo-backed Express API and Flask sentiment service as configured in Compose, or set `BACKEND_URL` and `SENTIMENT_URL` to their running addresses.

## Validation and CI/CD

`python server/manage.py test djangoapp` verifies session login/logout, CSRF enforcement, registration validation, idempotent data seeding, state filtering, sentiment enrichment, and review authorization/identity. `node server/database/smoke-test.js` tests a running Mongo-backed API including review persistence.

GitHub Actions runs these checks, builds React, checks migrations, verifies sentiment polarity, then builds and deploys all four services into containers and checks their HTTP endpoints. See `.github/workflows/cicd.yml`.

## Skills Network Kubernetes deployment

Open the course's **Containerize your Application** laboratory. Clone this repository and set `APP_HOST` to the host shown by the lab's Launch Application feature for port 8000. Run `bash scripts/deploy-lab.sh`, then the printed `kubectl port-forward` command. The deployment includes Django, Express, sentiment, and MongoDB containers in one pod so that backend traffic stays on localhost.

The lab manifest uses temporary MongoDB storage and a single replica, suitable for this educational session. For durable hosting, use persistent volumes and a managed database. Do not reset the lab before collecting the required screenshots.

## Screenshot evidence

The Coursera peer submission requires 26 actual screenshots plus the public repository URL and deployment URL. Screenshots must show the application URL in the browser address bar where required. A source-code build or an image of a mock page is not a substitute for running the application.

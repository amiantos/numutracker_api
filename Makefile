up:
	docker-compose up

down:
	docker-compose down

test:
	docker-compose run --user=root --rm api pytest

test-coverage:
	docker-compose run --user=root --rm api pytest --cov=backend

test-coverage-lines:
	docker-compose run --user=root --rm api pytest --cov-report term-missing --cov=backend

test-debug:
	docker-compose run --user=root --rm api pytest --pdb

shell:
	docker-compose run --rm api bash -c "flask shell"
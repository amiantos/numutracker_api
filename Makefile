up:
	docker-compose up

down:
	docker-compose down

test:
	docker-compose run --user=root --rm api pytest

test-debug:
	docker-compose run --user=root --rm api pytest --pdb

shell:
	docker-compose run --rm api bash -c "flask shell"
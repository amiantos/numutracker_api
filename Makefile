up:
	docker-compose -f docker-compose.local.yml build && docker-compose -f docker-compose.local.yml up

down:
	docker-compose -f docker-compose.local.yml down

test:
	docker-compose -f docker-compose.local.yml build && docker-compose -f docker-compose.local.yml run --user=root --rm api pytest

shell:
	docker-compose -f docker-compose.local.yml build && docker-compose -f docker-compose.local.yml run --rm api bash -c "flask shell"
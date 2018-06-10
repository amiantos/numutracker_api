up:
	docker-compose -f docker-compose.local.yml up

test:
	docker-compose build api && docker-compose -f docker-compose.local.yml run --user=root --rm api pytest
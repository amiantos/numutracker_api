up:
	docker-compose build && docker-compose -f docker-compose.local.yml up

test:
	docker-compose build && docker-compose -f docker-compose.local.yml run --user=root --rm api pytest
.PHONY: restore

restore:
	${HOME}/.dokku/contrib/dokku_client.sh postgres:export sleep > sleep.sql
	docker exec -i -u postgres sleep_database_1 psql postgres -c 'DROP DATABASE sleep;'
	docker exec -i -u postgres sleep_database_1 psql postgres -c 'CREATE DATABASE sleep;'
	docker exec -i -u postgres sleep_database_1 pg_restore -d sleep < sleep.sql
	rm sleep.sql

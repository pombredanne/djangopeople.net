proj = djangopeople
django = envdir env django-admin.py
testdjango = envdir tests/env django-admin.py

test:
	$(testdjango) test --failfast --noinput ${TEST}

run:
	foreman start -f Procfile.dev

db:
	$(django) syncdb --noinput && $(django) fix_counts

shell:
	$(django) shell

makemessages:
	cd $(proj) && envdir ../env django-admin.py makemessages -a

compilemessages:
	cd $(proj) && envdir ../env django-admin.py compilemessages

txpush:
	tx push -s

txpull:
	tx pull -a

initialdeploy:
	git push heroku master
	heroku run django-admin.py syncdb --noinput
	heroku run django-admin.py collectstatic
	heroku run django-admin.py fix_counts

deploy:
	git push heroku master
	heroku run django-admin.py collectstatic --noinput

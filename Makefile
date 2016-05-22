proj = djangopeople

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

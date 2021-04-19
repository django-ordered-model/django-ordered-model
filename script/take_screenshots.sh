# requires ubuntu
# sudo apt install cutycapt xvfb

set -x

# https://stackoverflow.com/questions/24390488/django-admin-without-authentication
# https://askubuntu.com/questions/75058/how-can-i-take-a-full-page-screenshot-of-a-webpage-from-the-command-line

# delete test DB if it exists
rm -f testdb
rm -Rf tests/staticfiles
mkdir -p tests/migrations tests/staticfiles
touch tests/migrations/__init__.py
mkdir -p static
killall django-admin

function djangoadmin() {
    django-admin $1 --pythonpath=. --settings=tests.settings --skip-checks $2
}
djangoadmin "makemigrations"
djangoadmin "migrate"
# requires Django > 3.0
DJANGO_SUPERUSER_PASSWORD=password DJANGO_SUPERUSER_EMAIL="x@test.com" DJANGO_SUPERUSER_USERNAME=admin \
    djangoadmin "createsuperuser" "--no-input"
djangoadmin "collectstatic"

# to refresh sample data, use runserver then this export command
# django-admin dumpdata --pythonpath=. --settings=tests.settings tests --output tests/fixtures/screenshot-sample-data.json --indent 4

djangoadmin "loaddata" "screenshot-sample-data"
django-admin runserver --pythonpath=. --settings=tests.settings_autoauth 7000 &
sleep 2

function capture() {
    xvfb-run --server-args="-screen 0, 1024x768x24" cutycapt --url=http://localhost:7000/$1 --out=static/$2
}
capture "admin/tests/item/" "items.png"
capture "admin/tests/pizza/1/change/" "pizza.png"
capture "admin/tests/pizzaproxy/1/change/" "pizza-stacked.png"

sleep 1
killall django-admin
rm -Rf tests/migrations
rm -Rf tests/staticfiles



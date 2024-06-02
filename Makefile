db.sqlite3: schema.sql
	test -r $@ && rm $@
	sqlite3 $@ < $^

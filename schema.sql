-- pname and iname so join queries can omit table name
-- default sqlite3 'rowid' column created for each table

create table ingredient (
 iname text unique not null,
 -- active is Unknown, Active, Inactive, Both. premature optimization with single char
 active varchar(1) CHECK( active IN ('U','A','I', 'B') )  NOT NULL DEFAULT 'U'
);

create table product (
  pname text unique  not null,
  brand text,
  pdesc text);

-- join table. one product to many ingredients.
create table ingredient_product (
    iid int not null, pid int not null,
    pulled timestamp not null default current_timestamp,
    percent number,
    FOREIGN KEY(iid) REFERENCES ingredient(rowid),
    FOREIGN KEY(pid) REFERENCES product(rowid));

-- conflicts
create table conflicts (
    i1 int not null,
    i2 int not null,
    severity int CHECK(severity <= 5 and severity >= 0) not null,
    note text,
    FOREIGN KEY(i1) REFERENCES ingredient(rowid),
    FOREIGN KEY(i2) REFERENCES ingredient(rowid));

create table admin (
  id integer primary key autoincrement,
  user text not null,
  password text not null,
  level text not null
);

create table invkey (
  id integer primary key autoincrement,
  key text not null,
  level integer
);

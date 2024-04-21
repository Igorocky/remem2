create table CACHE
(
    key   text primary key,
    value text not null
) strict;

create table LANGUAGE
(
    id   integer primary key,
    ext_id text not null unique ,
    name text not null unique
) strict;

insert into LANGUAGE(id, ext_id, name) VALUES (1, '629723fb-bf93-45bc-a785-a6184b7a10a3', 'ENG');
insert into LANGUAGE(id, ext_id, name) VALUES (2, '86129ca5-8cf1-4dcf-b152-1ffbbccf193e', 'POL');
insert into LANGUAGE(id, ext_id, name) VALUES (3, '458995d9-0f65-4447-90ff-d03326a4ef67', 'UKR');
insert into LANGUAGE(id, ext_id, name) VALUES (4, '4e54d364-eee7-4a4d-96bd-2684cd3b1060', 'RUS');

create table FOLDER
(
    id   integer primary key,
    parent_id integer references FOLDER on delete restrict on update cascade ,
    name text not null
) strict;

create table QUERY
(
    id integer primary key ,
    name text not null unique ,
    text text not null
) strict ;

create table QUERY_CHG
(
    time integer not null default (unixepoch()),
    id integer not null ,
    name text not null,
    text text not null
) strict ;

create trigger query_insert after insert on QUERY FOR EACH ROW BEGIN
    insert into QUERY_CHG (id, name, text) values (new.id, new.name, new.text);
end;

create trigger query_update after update on QUERY FOR EACH ROW BEGIN
    insert into QUERY_CHG (id, name, text) values (new.id, new.name, new.text);
end;

create table CARD_TYPE
(
    id   integer primary key,
    code text not null unique,
    table_name text not null unique
) strict;

insert into CARD_TYPE(id, code, table_name) VALUES (1, 'translate', 'CARD_TRAN');
insert into CARD_TYPE(id, code, table_name) VALUES (2, 'fill_gaps', 'CARD_FILL');
insert into CARD_TYPE(id, code, table_name) VALUES (3, 'synopsis', 'CARD_SYN');
-- insert into card_typ(id, code, tbl_nm) VALUES (3, 'irregular_verb', 'CARD_IRR');

create table TASK_TYPE
(
    id integer primary key ,
    card_type_id integer not null references CARD_TYPE on delete restrict on update restrict ,
    code text not null unique
) strict ;

insert into TASK_TYPE(card_type_id, code) values (1, 'lang1->lang2');
insert into TASK_TYPE(card_type_id, code) values (1, 'lang2->lang1');
insert into TASK_TYPE(card_type_id, code) values (2, 'fill_gaps');
insert into TASK_TYPE(card_type_id, code) values (3, 'repeat_synopsis');

create table CARD
(
    id   integer primary key,
    ext_id text not null unique ,
    folder_id integer not null references FOLDER on delete restrict on update restrict ,
    card_type_id integer not null references CARD_TYPE on delete restrict on update restrict ,
    crt_time integer not null default (unixepoch())
) strict;

create table CARD_CHG
(
    time integer not null default (unixepoch()),
    id   integer not null ,
    ext_id text not null ,
    folder_id integer not null ,
    card_type_id integer not null ,
    crt_time integer not null
) strict ;

create trigger card_insert AFTER INSERT ON CARD FOR EACH ROW BEGIN
    insert into CARD_CHG(id, ext_id, folder_id, card_type_id, crt_time)
        VALUES (new.id, new.ext_id, new.folder_id, new.card_type_id, new.crt_time);
END;

create trigger card_update AFTER UPDATE ON CARD FOR EACH ROW WHEN old.ext_id <> new.ext_id BEGIN
    insert into CARD_CHG(id, ext_id, folder_id, card_type_id, crt_time)
        VALUES (new.id, new.ext_id, new.folder_id, new.card_type_id, new.crt_time);
END;

create table TASK
(
    id integer primary key ,
    card_id integer not null references CARD on delete cascade on update restrict ,
    task_type_id integer not null references TASK_TYPE on delete restrict on update restrict ,
    unique (card_id, task_type_id)
) strict ;

create trigger card_insert_tasks AFTER INSERT ON CARD FOR EACH ROW BEGIN
    insert into TASK (card_id, task_type_id)
        select new.id, tt.id from TASK_TYPE tt where tt.card_type_id = new.card_type_id;
END;

create table TASK_HIST
(
    time integer not null default (unixepoch()),
    task_id integer not null references TASK on delete cascade on update restrict ,
    mark real not null check ( 0 <= mark and mark <= 1 ),
    note text
) strict ;

create table CARD_TRAN
(
    id integer not null references CARD on delete cascade on update restrict ,
    lang1_id integer not null references LANGUAGE on delete restrict on update restrict ,
    read_only1 integer not null check ( read_only1 in (0,1) ),
    text1 text not null ,
    lang2_id integer not null references LANGUAGE on delete restrict on update restrict ,
    read_only2 integer not null check ( read_only2 in (0,1) ),
    text2 text not null ,
    notes text not null
) strict ;

create table CARD_TRAN_CHG
(
    time integer not null default (unixepoch()),
    id integer not null,
    lang1_id integer not null ,
    read_only1 integer not null check ( read_only1 in (0,1) ),
    text1 text not null ,
    lang2_id integer not null ,
    read_only2 integer not null check ( read_only2 in (0,1) ),
    text2 text not null,
    notes text not null
) strict ;

create trigger insert_CARD_TRAN AFTER INSERT ON CARD_TRAN FOR EACH ROW BEGIN
    insert into CARD_TRAN_CHG(id, lang1_id, read_only1, text1, lang2_id, read_only2, text2, notes)
    VALUES (new.id, new.lang1_id, new.read_only1, new.text1,
            new.lang2_id, new.read_only2, new.text2, new.notes);
end;

create trigger update_CARD_TRAN AFTER UPDATE ON CARD_TRAN FOR EACH ROW BEGIN
    insert into CARD_TRAN_CHG(id, lang1_id, read_only1, text1, lang2_id, read_only2, text2, notes)
    VALUES (new.id, new.lang1_id, new.read_only1, new.text1,
            new.lang2_id, new.read_only2, new.text2, new.notes);
end;

create table CARD_FILL
(
    id integer not null references CARD on delete cascade on update restrict ,
    lang_id integer not null references LANGUAGE on delete restrict on update restrict ,
    descr text not null,
    text text not null,
    notes text not null
) strict ;

create table CARD_FILL_CHG
(
    time integer not null default (unixepoch()),
    id integer not null,
    lang_id integer not null ,
    descr text not null,
    text text not null,
    notes text not null
) strict ;

create trigger insert_CARD_FILL AFTER INSERT ON CARD_FILL FOR EACH ROW BEGIN
    insert into CARD_FILL_CHG(id, lang_id, descr, text, notes)
    VALUES (new.id, new.lang_id, new.descr, new.text, new.notes);
end;

create trigger update_CARD_FILL AFTER UPDATE ON CARD_FILL FOR EACH ROW BEGIN
    insert into CARD_FILL_CHG(id, lang_id, descr, text, notes)
    VALUES (new.id, new.lang_id, new.descr, new.text, new.notes);
end;

create table CARD_SYN
(
    id integer not null references CARD on delete cascade on update cascade,
    cont text not null
) strict ;

create table CARD_SYN_CHG
(
    time integer not null default (unixepoch()),
    id integer not null,
    cont text not null
) strict ;

create trigger insert_CARD_SYN AFTER INSERT ON CARD_SYN FOR EACH ROW BEGIN
    insert into CARD_SYN_CHG(id, cont)
    VALUES (new.id, new.cont);
end;

create trigger update_CARD_SYN AFTER UPDATE ON CARD_SYN FOR EACH ROW BEGIN
    insert into CARD_SYN_CHG(id, cont)
    VALUES (new.id, new.cont);
end;
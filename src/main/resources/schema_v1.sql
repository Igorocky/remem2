create table LANGUAGE
(
    id   integer primary key,
    ext_id text not null unique ,
    name text not null unique,
    read_only integer not null check ( read_only in (0,1) )
) strict;

insert into LANGUAGE(ext_id, name, read_only) VALUES ('629723fb-bf93-45bc-a785-a6184b7a10a3', 'ENG', 0);
insert into LANGUAGE(ext_id, name, read_only) VALUES ('86129ca5-8cf1-4dcf-b152-1ffbbccf193e', 'POL', 0);
insert into LANGUAGE(ext_id, name, read_only) VALUES ('458995d9-0f65-4447-90ff-d03326a4ef67', 'UKR', 1);
insert into LANGUAGE(ext_id, name, read_only) VALUES ('4e54d364-eee7-4a4d-96bd-2684cd3b1060', 'RUS', 1);

create table FOLDER
(
    id   integer primary key,
    parent_id integer references FOLDER on delete restrict on update cascade ,
    name text not null
) strict;

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
    card_type_id integer not null references CARD_TYPE on delete restrict on update cascade ,
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
    folder_id integer not null references FOLDER on delete restrict on update cascade ,
    card_type_id integer not null references CARD_TYPE on delete restrict on update cascade ,
    crt_time integer not null default (unixepoch())
) strict;

create table CARD_EXT_ID_CHG
(
    time integer not null default (unixepoch()),
    card_id integer not null,
    card_ext_id text not null
) strict ;

create trigger card_insert_ext_id AFTER INSERT ON CARD FOR EACH ROW BEGIN
    insert into CARD_EXT_ID_CHG(card_id, card_ext_id) VALUES (new.id, new.ext_id);
END;

create trigger card_update_ext_id AFTER UPDATE ON CARD FOR EACH ROW WHEN old.ext_id <> new.ext_id BEGIN
    insert into CARD_EXT_ID_CHG(card_id, card_ext_id) VALUES (new.id, new.ext_id);
END;

create table TASK
(
    id integer primary key ,
    card_id integer not null references CARD on delete cascade on update cascade ,
    task_type_id integer not null references TASK_TYPE on delete restrict on update cascade,
    unique (card_id, task_type_id)
) strict ;

create trigger card_insert_tasks AFTER INSERT ON CARD FOR EACH ROW BEGIN
    insert into TASK (card_id, task_type_id)
        select new.id, tt.id from TASK_TYPE tt where tt.card_type_id = new.card_type_id;
END;

create table TASK_HIST
(
    time integer not null default (unixepoch()),
    task_id integer not null references TASK on delete cascade on update cascade ,
    mark real not null check ( 0 <= mark and mark <= 1 ),
    note text
) strict ;

create table CARD_TRAN
(
    id integer not null references CARD on delete cascade on update cascade,
    lang1_id integer not null references LANGUAGE on delete restrict on update cascade ,
    text1 text not null ,
    tran1 text not null ,
    lang2_id integer not null references LANGUAGE on delete restrict on update cascade ,
    text2 text not null ,
    tran2 text not null
) strict ;

create table CARD_TRAN_CHG
(
    time integer not null default (unixepoch()),
    id integer not null,
    lang1_id integer not null references LANGUAGE on delete restrict on update cascade ,
    text1 text not null ,
    tran1 text not null ,
    lang2_id integer not null references LANGUAGE on delete restrict on update cascade ,
    text2 text not null,
    tran2 text not null
) strict ;

create trigger insert_CARD_TRAN AFTER INSERT ON CARD_TRAN FOR EACH ROW BEGIN
    insert into CARD_TRAN_CHG(id, lang1_id, text1, tran1, lang2_id, text2, tran2)
    VALUES (new.id, new.lang1_id, new.text1, new.tran1, new.lang2_id, new.text2, new.tran2);
end;

create trigger update_CARD_TRAN AFTER UPDATE ON CARD_TRAN FOR EACH ROW BEGIN
    insert into CARD_TRAN_CHG(id, lang1_id, text1, tran1, lang2_id, text2, tran2)
    VALUES (new.id, new.lang1_id, new.text1, new.tran1, new.lang2_id, new.text2, new.tran2);
end;

create table CARD_FILL
(
    id integer not null references CARD on delete cascade on update cascade,
    text text not null,
    notes text not null
) strict ;

create table CARD_FILL_CHG
(
    id integer not null,
    text text not null,
    notes text not null
) strict ;

create trigger insert_CARD_FILL AFTER INSERT ON CARD_FILL FOR EACH ROW BEGIN
    insert into CARD_FILL_CHG(id, text, notes)
    VALUES (new.id, new.text, new.notes);
end;

create trigger update_CARD_FILL AFTER UPDATE ON CARD_FILL FOR EACH ROW BEGIN
    insert into CARD_FILL_CHG(id, text, notes)
    VALUES (new.id, new.text, new.notes);
end;

create table CARD_SYN
(
    id integer not null references CARD on delete cascade on update cascade,
    cont text not null
) strict ;

create table CARD_SYN_CHG
(
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
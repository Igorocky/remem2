create table LANG
(
    id   integer primary key,
    ext_id text not null unique ,
    name text not null unique,
    read_only integer not null check ( read_only in (0,1) )
) strict;

insert into lang(ext_id, name, read_only) VALUES ('629723fb-bf93-45bc-a785-a6184b7a10a3', 'ENG', 0);
insert into lang(ext_id, name, read_only) VALUES ('86129ca5-8cf1-4dcf-b152-1ffbbccf193e', 'POL', 0);
insert into lang(ext_id, name, read_only) VALUES ('458995d9-0f65-4447-90ff-d03326a4ef67', 'UKR', 1);
insert into lang(ext_id, name, read_only) VALUES ('4e54d364-eee7-4a4d-96bd-2684cd3b1060', 'RUS', 1);

create table FLD
(
    id   integer primary key,
    parent integer references fld(id) on delete restrict on update cascade ,
    name text not null
) strict;

create table CARD_TYP
(
    id   integer primary key,
    code text not null unique,
    tbl_nm text not null unique
) strict;

insert into CARD_TYP(id, code, tbl_nm) VALUES (1, 'translate', 'CARD_TRAN');
insert into CARD_TYP(id, code, tbl_nm) VALUES (2, 'fill_gaps', 'CARD_FILL');
insert into CARD_TYP(id, code, tbl_nm) VALUES (3, 'synopsis', 'CARD_SYN');
-- insert into card_typ(id, code, tbl_nm) VALUES (3, 'irregular_verb', 'CARD_IRR');

create table TASK_TYP
(
    card_typ integer not null references CARD_TYP(id) on delete restrict on update cascade ,
    task_typ integer not null,
    code text not null ,
    unique (card_typ, task_typ),
    unique (card_typ, code)
) strict ;

insert into TASK_TYP(card_typ, task_typ, code) values (1, 1, 'lang1->lang2');
insert into TASK_TYP(card_typ, task_typ, code) values (1, 2, 'lang2->lang1');
insert into TASK_TYP(card_typ, task_typ, code) values (2, 1, 'fill_gaps');
insert into TASK_TYP(card_typ, task_typ, code) values (3, 1, 'repeat_synopsis');

create table CARD
(
    id   integer primary key,
    ext_id text not null unique ,
    fld_id integer not null references FLD(id) on delete restrict on update cascade ,
    typ integer not null references CARD_TYP(id) on delete restrict on update cascade ,
    crt_time integer not null default (unixepoch())
) strict;

create table CARD_EXT_ID_CHG
(
    time integer not null default (unixepoch()),
    card_id integer not null,
    card_ext_id text not null
) strict ;

create trigger card_ext_id_insert AFTER INSERT ON CARD FOR EACH ROW BEGIN
    insert into CARD_EXT_ID_CHG(card_id, card_ext_id) VALUES (new.id, new.ext_id);
END;

create trigger card_ext_id_update AFTER UPDATE ON CARD FOR EACH ROW WHEN old.ext_id <> new.ext_id BEGIN
    insert into CARD_EXT_ID_CHG(card_id, card_ext_id) VALUES (new.id, new.ext_id);
END;

create table TASK
(
    id integer primary key ,
    card integer not null references CARD(id) on delete cascade on update cascade ,
    typ integer not null references TASK_TYP(task_typ) on delete restrict on update cascade,
    unique (card, typ)
) strict ;

create trigger insert_tasks AFTER INSERT ON CARD FOR EACH ROW BEGIN
    insert into TASK (card, typ) select new.id, task_typ from TASK_TYP where card_typ = new.typ;
END;

create table TASK_HIST
(
    time integer not null default (unixepoch()),
    task integer not null references TASK(id) on delete cascade on update cascade ,
    mark real not null check ( 0 <= mark and mark <= 1 ),
    note text
) strict ;

create table CARD_TRAN
(
    id integer not null references CARD(id) on delete cascade on update cascade,
    lang1 integer not null references LANG(id) on delete restrict on update cascade ,
    text1 text not null ,
    lang2 integer not null references LANG(id) on delete restrict on update cascade ,
    text2 text not null
) strict ;

create table CARD_TRAN_CHG
(
    time integer not null default (unixepoch()),
    id integer not null,
    lang1 integer not null references LANG(id) on delete restrict on update cascade ,
    text1 text not null ,
    lang2 integer not null references LANG(id) on delete restrict on update cascade ,
    text2 text not null
) strict ;

create trigger insert_CARD_TRAN_CHG AFTER INSERT ON CARD_TRAN FOR EACH ROW BEGIN
    insert into CARD_TRAN_CHG(id, lang1, text1, lang2, text2)
    VALUES (new.id, new.lang1, new.text1, new.lang2, new.text2);
end;

create trigger update_CARD_TRAN_CHG AFTER UPDATE ON CARD_TRAN FOR EACH ROW BEGIN
    insert into CARD_TRAN_CHG(id, lang1, text1, lang2, text2)
    VALUES (new.id, new.lang1, new.text1, new.lang2, new.text2);
end;

create table CARD_FILL
(
    id integer not null references CARD(id) on delete cascade on update cascade,
    text text not null,
    notes text not null
) strict ;

create table CARD_FILL_CHG
(
    id integer not null,
    text text not null,
    notes text not null
) strict ;

create trigger insert_CARD_FILL_CHG AFTER INSERT ON CARD_FILL FOR EACH ROW BEGIN
    insert into CARD_FILL_CHG(id, text, notes)
    VALUES (new.id, new.text, new.notes);
end;

create trigger update_CARD_FILL_CHG AFTER UPDATE ON CARD_FILL FOR EACH ROW BEGIN
    insert into CARD_FILL_CHG(id, text, notes)
    VALUES (new.id, new.text, new.notes);
end;

create table CARD_SYN
(
    id integer not null references CARD(id) on delete cascade on update cascade,
    cont text not null
) strict ;

create table CARD_SYN_CHG
(
    id integer not null,
    cont text not null
) strict ;

create trigger insert_CARD_SYN_CHG AFTER INSERT ON CARD_SYN FOR EACH ROW BEGIN
    insert into CARD_SYN_CHG(id, cont)
    VALUES (new.id, new.cont);
end;

create trigger update_CARD_SYN_CHG AFTER UPDATE ON CARD_SYN FOR EACH ROW BEGIN
    insert into CARD_SYN_CHG(id, cont)
    VALUES (new.id, new.cont);
end;
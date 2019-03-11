create table rowan.fauxrm_test_band_members (
    first_name  varchar2(100),
    last_name   varchar2(100),
    instrument  varchar2(100),
    band_name   varchar2(100),
    constraint band_pk primary key (band_name, last_name, instrument)
);

comment on table rowan.fauxrm_test_band_members is 'A test table for the FauxRM library''s composite key functionality';
comment on column rowan.fauxrm_test_band_members.first_name is 'A band member''s first name';
comment on column rowan.fauxrm_test_band_members.last_name is 'A band member''s last name';
comment on column rowan.fauxrm_test_band_members.instrument is 'The instrument that the band member plays';
comment on column rowan.fauxrm_test_band_members.band_name is 'The name of the band';

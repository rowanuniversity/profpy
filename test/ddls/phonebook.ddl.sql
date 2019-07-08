CREATE TABLE rowan.fauxrm_test_phonebook (
    ID              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY NOT NULL,
    FIRST_NAME      VARCHAR2(100),
    LAST_NAME       VARCHAR2(100),
    PHONE           VARCHAR2(12)
);

COMMENT ON TABLE rowan.fauxrm_test_phonebook IS 'A Test table for the FauxRM library';
COMMENT ON COLUMN rowan.fauxrm_test_phonebook.ID IS 'Auto generated primary key for phonebook entries';
COMMENT ON COLUMN rowan.fauxrm_test_phonebook.FIRST_NAME IS 'The first name of the person for this entry';
COMMENT ON COLUMN rowan.fauxrm_test_phonebook.LAST_NAME IS 'The last name of the person for this entry';
COMMENT ON COLUMN rowan.fauxrm_test_phonebook.PHONE IS 'The phone number for this entry';

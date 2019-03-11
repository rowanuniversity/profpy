CREATE TABLE rowan.fauxrm_test_medical (
    FIRST_NAME      VARCHAR2(100),
    LAST_NAME       VARCHAR2(100),
    AGE             INTEGER,
    WEIGHT          FLOAT,
    VISIT_DATE      TIMESTAMP,
    CONSTRAINT med_pk PRIMARY KEY (FIRST_NAME, LAST_NAME, VISIT_DATE)
);

COMMENT ON TABLE rowan.fauxrm_test_medical IS 'A Test table for the FauxRM library';
COMMENT ON COLUMN rowan.fauxrm_test_medical.FIRST_NAME IS 'The first name of the person for this entry';
COMMENT ON COLUMN rowan.fauxrm_test_medical.LAST_NAME IS 'The last name of the person for this entry';
COMMENT ON COLUMN rowan.fauxrm_test_medical.AGE IS 'The age of the person';
COMMENT ON COLUMN rowan.fauxrm_test_medical.WEIGHT IS 'The weight of the person';
COMMENT ON COLUMN rowan.fauxrm_test_medical.VISIT_DATE IS 'The date of the office visit';